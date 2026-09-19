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


class CompareRequest(BaseModel):
    asset: str = "nvidia"
    initial_capital: float = 100000.0
    transaction_cost: float = 0.001


def load_dataset(asset: str) -> pd.DataFrame:
    asset = asset.lower()

    if asset not in DATASETS:
        raise HTTPException(
            status_code=400,
            detail="Asset must be gold, bitcoin, or nvidia.",
        )

    file_path = DATASETS[asset]

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    df = pd.read_csv(file_path)

    if "Date" not in df.columns or "Close" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="Dataset must contain Date and Close columns.",
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df.dropna(subset=["Date", "Close"])
    df = df.sort_values("Date")
    df = df.drop_duplicates(subset=["Date"], keep="last")

    if df.empty:
        raise HTTPException(
            status_code=500,
            detail="Dataset contains no valid market data.",
        )

    return df


def run_strategy(
    df: pd.DataFrame,
    strategy_name: str,
    initial_capital: float,
    transaction_cost: float,
):
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
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
        position_sizer=FullCapitalSizer(),
    )

    metrics = calculate_performance_metrics(
        equity=result.equity_curve,
        initial_capital=initial_capital,
    )

    return result, metrics


@router.post("/run")
def run_backtest_api(request: BacktestRequest):
    asset = request.asset.lower()
    strategy_name = request.strategy.lower()

    df = load_dataset(asset)

    result, metrics = run_strategy(
        df=df,
        strategy_name=strategy_name,
        initial_capital=request.initial_capital,
        transaction_cost=request.transaction_cost,
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
                "transaction_cost": float(
                    trade.transaction_cost
                ),
                "portfolio_value": float(
                    trade.portfolio_value
                ),
            }
        )

    equity_curve = []

    for date, value in result.equity_curve.items():
        equity_curve.append(
            {
                "date": str(date),
                "value": float(value),
            }
        )

    return {
        "asset": asset,
        "strategy": result.strategy_name,
        "initial_capital": request.initial_capital,
        "final_portfolio_value": float(
            result.final_portfolio_value
        ),
        "total_return": float(result.total_return),
        "maximum_drawdown": float(
            result.maximum_drawdown
        ),
        "annualized_volatility": float(
            metrics["annualized_volatility"]
        ),
        "sharpe_ratio": float(
            metrics["sharpe_ratio"]
        ),
        "trade_count": len(trades),
        "trades": trades,
        "equity_curve": equity_curve,
    }


@router.post("/compare")
def compare_strategies(request: CompareRequest):
    asset = request.asset.lower()

    df = load_dataset(asset)

    sma_result, sma_metrics = run_strategy(
        df=df,
        strategy_name="sma",
        initial_capital=request.initial_capital,
        transaction_cost=request.transaction_cost,
    )

    ema_result, ema_metrics = run_strategy(
        df=df,
        strategy_name="ema",
        initial_capital=request.initial_capital,
        transaction_cost=request.transaction_cost,
    )

    return {
        "asset": asset,
        "initial_capital": request.initial_capital,
        "transaction_cost": request.transaction_cost,
        "strategies": [
            {
                "strategy": "sma",
                "final_portfolio_value": float(
                    sma_result.final_portfolio_value
                ),
                "total_return": float(
                    sma_result.total_return
                ),
                "maximum_drawdown": float(
                    sma_result.maximum_drawdown
                ),
                "annualized_volatility": float(
                    sma_metrics["annualized_volatility"]
                ),
                "sharpe_ratio": float(
                    sma_metrics["sharpe_ratio"]
                ),
                "trade_count": len(
                    sma_result.trades
                ),
            },
            {
                "strategy": "ema",
                "final_portfolio_value": float(
                    ema_result.final_portfolio_value
                ),
                "total_return": float(
                    ema_result.total_return
                ),
                "maximum_drawdown": float(
                    ema_result.maximum_drawdown
                ),
                "annualized_volatility": float(
                    ema_metrics["annualized_volatility"]
                ),
                "sharpe_ratio": float(
                    ema_metrics["sharpe_ratio"]
                ),
                "trade_count": len(
                    ema_result.trades
                ),
            },
        ],
    }