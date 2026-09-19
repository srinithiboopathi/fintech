import pandas as pd
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analysis.metrics import calculate_performance_metrics
from app.backtesting.engine import run_backtest
from app.backtesting.position_sizing import FullCapitalSizer
from app.strategies.ema_trend import EMATrendStrategy
from app.strategies.sma_crossover import SMACrossoverStrategy


router = APIRouter(prefix="/backtest", tags=["Backtest"])


DATA_ROOT = Path(__file__).resolve().parents[3] / "datasets" / "raw"

DATASETS = {
    "gold": DATA_ROOT / "gold" / "gold_raw.csv",
    "bitcoin": DATA_ROOT / "bitcoin" / "bitcoin_raw.csv",
    "nvidia": DATA_ROOT / "nvidia" / "nvidia_raw.csv",
}


class BacktestRequest(BaseModel):
    asset: str = "nvidia"
    strategy: str = "sma"
    initial_capital: float = 100000.0
    transaction_cost: float = 0.001


@router.post("/run")
def run_backtest_api(request: BacktestRequest):
    asset = request.asset.lower()
    strategy_name = request.strategy.lower()

    if asset not in DATASETS:
        raise HTTPException(
            status_code=400,
            detail="Asset must be gold, bitcoin, or nvidia.",
        )

    if not DATASETS[asset].exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    df = pd.read_csv(DATASETS[asset])

    if "Date" not in df.columns or "Close" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="Dataset must contain Date and Close columns.",
        )

    if strategy_name == "sma":
        strategy = SMACrossoverStrategy()

    elif strategy_name == "ema":
        strategy = EMATrendStrategy()

    else:
        raise HTTPException(
            status_code=400,
            detail="Strategy must be sma or ema.",
        )

    result = run_backtest(
        df=df,
        strategy=strategy,
        initial_capital=request.initial_capital,
        transaction_cost=request.transaction_cost,
        position_sizer=FullCapitalSizer(),
    )

    metrics = calculate_performance_metrics(
        equity=result.equity_curve,
        initial_capital=request.initial_capital,
    )

    trades = []

    for trade in result.trades:
        trades.append(
            {
                "date": str(trade.date),
                "action": trade.action,
                "price": float(trade.price),
                "position": int(trade.position),
                "quantity": float(trade.quantity),
                "transaction_cost": float(trade.transaction_cost),
                "portfolio_value": float(trade.portfolio_value),
            }
        )

    return {
        "asset": asset,
        "strategy": result.strategy_name,
        "initial_capital": request.initial_capital,
        "final_portfolio_value": float(result.final_portfolio_value),
        "total_return": float(result.total_return),
        "maximum_drawdown": float(result.maximum_drawdown),
        "annualized_volatility": float(metrics["annualized_volatility"]),
        "sharpe_ratio": float(metrics["sharpe_ratio"]),
        "trade_count": len(trades),
        "trades": trades,
    }