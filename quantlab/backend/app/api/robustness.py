from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.data.providers.csv_provider import CSVMarketProvider
from app.analysis.robustness import RobustnessEngine
from app.strategies.sma_crossover import SMACrossoverStrategy
from app.strategies.ema_trend import EMATrendStrategy
from app.strategies.momentum import MomentumBreakoutStrategy
from app.strategies.mean_reversion import MeanReversionStrategy

router = APIRouter(prefix="/robustness", tags=["Robustness Lab"])
provider = CSVMarketProvider()

STRATEGY_MAP = {
    "sma_crossover": SMACrossoverStrategy,
    "ema_trend": EMATrendStrategy,
    "momentum": MomentumBreakoutStrategy,
    "mean_reversion": MeanReversionStrategy
}

@router.get("/monte-carlo/{symbol}")
def run_monte_carlo(
    symbol: str,
    simulations: int = Query(300, ge=50, le=1000, description="Number of Monte Carlo paths"),
    horizon: int = Query(252, ge=20, le=504, description="Horizon days"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Simulates forward probability distributions and tail-risk confidence intervals
    via non-parametric historical return bootstrap resampling.
    """
    bars = provider.get_historical_bars(symbol, start_date, end_date)
    if not bars:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{symbol}'.")

    rets = [b["daily_return"] for b in bars]
    result = RobustnessEngine.monte_carlo_simulation(
        daily_returns=rets,
        initial_capital=100000.0,
        num_simulations=simulations,
        horizon_days=horizon
    )
    result["symbol"] = provider.normalize_symbol(symbol)
    return result

@router.get("/sensitivity/{symbol}")
def run_parameter_sensitivity(
    symbol: str,
    strategy_id: str = Query("sma_crossover", description="Strategy identifier"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Evaluates strategy performance across parameter grids and transaction cost friction levels
    to test for parameter stability and curve-fitting fragility.
    """
    bars = provider.get_historical_bars(symbol, start_date, end_date)
    if not bars:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{symbol}'.")

    strat_cls = STRATEGY_MAP.get(strategy_id.lower(), SMACrossoverStrategy)
    
    # Generate test grid based on strategy
    if strategy_id.lower() == "sma_crossover":
        param_grid = [
            {"fast_period": 10, "slow_period": 30},
            {"fast_period": 15, "slow_period": 45},
            {"fast_period": 20, "slow_period": 50},
            {"fast_period": 25, "slow_period": 75},
            {"fast_period": 50, "slow_period": 200}
        ]
    elif strategy_id.lower() == "ema_trend":
        param_grid = [
            {"fast_ema": 8, "mid_ema": 21, "slow_ema": 50},
            {"fast_ema": 9, "mid_ema": 21, "slow_ema": 55},
            {"fast_ema": 12, "mid_ema": 26, "slow_ema": 100}
        ]
    elif strategy_id.lower() == "momentum":
        param_grid = [
            {"lookback": 15, "rsi_filter": 50.0},
            {"lookback": 20, "rsi_filter": 50.0},
            {"lookback": 30, "rsi_filter": 55.0}
        ]
    else: # mean reversion
        param_grid = [
            {"bb_period": 15, "bb_std": 2.0, "rsi_period": 14},
            {"bb_period": 20, "bb_std": 2.0, "rsi_period": 14},
            {"bb_period": 20, "bb_std": 2.5, "rsi_period": 14}
        ]

    friction_levels = [0.0, 5.0, 15.0] # basis points
    sensitivity_results = RobustnessEngine.parameter_sensitivity(
        strategy_class=strat_cls,
        bars=bars,
        param_grid=param_grid,
        friction_levels=friction_levels
    )

    return {
        "symbol": provider.normalize_symbol(symbol),
        "strategy_id": strategy_id,
        "total_permutations": len(sensitivity_results),
        "results": sensitivity_results
    }
