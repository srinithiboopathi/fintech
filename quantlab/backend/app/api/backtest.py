from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.repositories import BacktestRepository, AssetRepository, MarketPriceRepository
from app.schemas.backtest import BacktestRequest, BacktestResult
from app.backtesting.engine import BacktestEngine
from app.strategies.sma_crossover import SMACrossoverStrategy
from app.strategies.ema_trend import EMATrendStrategy
from app.strategies.momentum import MomentumBreakoutStrategy
from app.strategies.mean_reversion import MeanReversionStrategy

router = APIRouter(prefix="/backtest", tags=["Backtesting"])

STRATEGY_MAP = {
    "sma_crossover": SMACrossoverStrategy,
    "ema_trend": EMATrendStrategy,
    "momentum": MomentumBreakoutStrategy,
    "mean_reversion": MeanReversionStrategy
}

@router.post("/run", response_model=BacktestResult)
def run_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    """
    Executes an event-driven quantitative backtest simulation with explicit transaction friction
    and compares it against a passive Buy-and-Hold benchmark.
    Persists the run record and trade log into the database.
    """
    asset = AssetRepository.get_by_symbol(db, req.symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"No price data available for '{req.symbol}' in the selected date range.")

    prices = MarketPriceRepository.get_prices_for_asset(
        db,
        asset.id,
        req.start_date,
        req.end_date
    )
    if not prices:
        raise HTTPException(status_code=404, detail=f"No price data available for '{req.symbol}' in the selected date range.")

    bars = [
        {
            "date": p.date,
            "symbol": asset.symbol,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume
        }
        for p in prices
    ]

    strat_cls = STRATEGY_MAP.get(req.strategy_id.lower(), SMACrossoverStrategy)
    strategy_instance = strat_cls(req.parameters)

    engine = BacktestEngine(
        strategy=strategy_instance,
        bars=bars,
        initial_capital=req.initial_capital,
        position_sizing=req.position_sizing,
        position_size_value=req.position_size_value,
        commission_bps=req.commission_bps,
        slippage_pct=req.slippage_pct
    )

    result = engine.run()

    # Attempt to persist in DB for historical tracking
    try:
        asset_id = asset.id
        
        db_payload = {
            "run_id": result["run_id"],
            "asset_id": asset_id,
            "strategy_id": req.strategy_id,
            "strategy": result["strategy_name"],
            "start_date": result["start_date"],
            "end_date": result["end_date"],
            "initial_capital": result["initial_capital"],
            "final_value": result["final_equity"],
            "total_return": result["total_return_pct"],
            "sharpe_ratio": result["sharpe_ratio"],
            "max_drawdown": result["max_drawdown_pct"],
            "number_of_trades": result["total_trades"],
            "transaction_cost": result["total_transaction_costs"],
            "parameters": req.parameters,
            "equity_curve": result["equity_curve"]
        }
        
        # Prepare trades for persistence
        trade_items = []
        for t in result.get("trades", []):
            trade_items.append({
                "trade_id": t.get("trade_id"),
                "date": t.get("exit_date") or t.get("entry_date", ""),
                "action": "SELL" if t.get("side") == "BUY" else "BUY",
                "price": t.get("exit_price", t.get("entry_price", 0.0)),
                "quantity": t.get("quantity", 0.0),
                "portfolio_value": result["final_equity"]
            })

        BacktestRepository.save_run(db, db_payload, trade_items)
    except Exception as e:
        # If DB write fails, log and continue returning backtest result without disrupting client
        pass

    return result

@router.get("/history", response_model=List[Dict[str, Any]])
def get_backtest_history(limit: int = 20, db: Session = Depends(get_db)):
    """
    Retrieves recent backtest run summaries from the database.
    """
    runs = BacktestRepository.list_recent(db, limit=limit)
    return [
        {
            "id": r.id,
            "strategy": r.strategy,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "initial_capital": r.initial_capital,
            "final_value": r.final_value,
            "total_return": r.total_return,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown": r.max_drawdown,
            "number_of_trades": r.number_of_trades,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in runs
    ]

@router.get("/{run_id}")
def get_backtest_by_id(run_id: str, db: Session = Depends(get_db)):
    """
    Retrieves complete metrics, equity curve, and parameters for a specific historical backtest run.
    """
    run = BacktestRepository.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Backtest run '{run_id}' not found.")
    
    trades = [
        {
            "id": t.id,
            "date": t.date,
            "action": t.action,
            "price": t.price,
            "quantity": t.quantity,
            "portfolio_value": t.portfolio_value
        }
        for t in run.trades
    ]

    return {
        "id": run.id,
        "strategy": run.strategy,
        "start_date": run.start_date,
        "end_date": run.end_date,
        "initial_capital": run.initial_capital,
        "final_value": run.final_value,
        "total_return": run.total_return,
        "sharpe_ratio": run.sharpe_ratio,
        "max_drawdown": run.max_drawdown,
        "number_of_trades": run.number_of_trades,
        "transaction_cost": run.transaction_cost,
        "parameters": run.parameters,
        "equity_curve": run.equity_curve,
        "trades": trades,
        "created_at": run.created_at.isoformat() if run.created_at else None
    }
