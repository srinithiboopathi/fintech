from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.repositories import AssetRepository, MarketPriceRepository
from app.quant.returns import ReturnMetrics
from app.quant.volatility import VolatilityMetrics
from app.quant.sharpe import RiskAdjustedMetrics
from app.quant.drawdown import DrawdownAnalysis
from app.correlation.matrix import CorrelationMatrix
from app.analysis.market_regimes import MarketRegimeClassifier
from app.strategies.sma_crossover import SMACrossoverStrategy
from app.backtesting.engine import BacktestEngine

router = APIRouter(prefix="/reports", tags=["Research Reports"])

def _get_asset_bars(db: Session, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    asset = AssetRepository.get_by_symbol(db, symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"No market data found for '{symbol}'.")

    prices = MarketPriceRepository.get_prices_for_asset(db, asset.id, start_date, end_date)
    if not prices:
        raise HTTPException(status_code=404, detail=f"No market data found for '{symbol}'.")

    bars = []
    prev_close = None
    for p in prices:
        daily_return = (p.close - prev_close) / prev_close if prev_close is not None and prev_close > 0 else 0.0
        prev_close = p.close
        bars.append({
            "date": p.date,
            "symbol": asset.symbol,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume,
            "daily_return": round(daily_return, 6)
        })
    return asset.symbol, bars

@router.get("/generate/{symbol}")
def generate_tear_sheet(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generates a full quantitative research tear sheet and factor risk report
    for the selected asset over the requested historical window.
    """
    norm_sym, bars = _get_asset_bars(db, symbol, start_date, end_date)

    prices = [b["close"] for b in bars]
    dates = [b["date"] for b in bars]
    rets = [b["daily_return"] for b in bars]

    # Return & Risk Calculations
    total_cum_ret = ReturnMetrics.cumulative_return(prices) * 100.0
    cagr_val = ReturnMetrics.cagr(prices[0], prices[-1], len(prices)) * 100.0
    ann_vol = VolatilityMetrics.annualized_volatility(rets) * 100.0
    downside_vol = VolatilityMetrics.downside_volatility(rets) * 100.0
    sharpe = RiskAdjustedMetrics.sharpe_ratio(rets)
    sortino = RiskAdjustedMetrics.sortino_ratio(rets)
    
    underwater, max_dd, max_dd_len = DrawdownAnalysis.calculate_drawdowns(prices)
    calmar = RiskAdjustedMetrics.calmar_ratio(cagr_val / 100.0, max_dd)

    var_95 = VolatilityMetrics.value_at_risk_historical(rets, 0.95) * 100.0
    cvar_95 = VolatilityMetrics.conditional_var_historical(rets, 0.95) * 100.0

    # Correlation with peer assets from SQLite
    all_syms = ["GC=F", "BTC-USD", "NVDA"]
    asset_rets = {}
    for s in all_syms:
        try:
            _, s_bars = _get_asset_bars(db, s)
            asset_rets[s] = {b["date"]: b["daily_return"] for b in s_bars}
        except Exception:
            asset_rets[s] = {}

    common_dates = sorted(list(set.intersection(*[set(asset_rets[s].keys()) for s in all_syms if asset_rets[s]])))
    peer_correlations = {}
    if common_dates:
        aligned_data = {s: [asset_rets[s][d] for d in common_dates] for s in all_syms}
        corr_matrix = CorrelationMatrix.calculate_matrix(aligned_data, all_syms, method="pearson")
        sym_idx = all_syms.index(norm_sym) if norm_sym in all_syms else 0
        for i, s in enumerate(all_syms):
            if s != norm_sym:
                peer_correlations[s] = corr_matrix[sym_idx][i]

    # Baseline Strategy Backtest (Dual SMA Golden Cross)
    baseline_strat = SMACrossoverStrategy({"fast_period": 20, "slow_period": 50})
    engine = BacktestEngine(
        strategy=baseline_strat,
        bars=bars,
        initial_capital=100000.0,
        commission_bps=5.0,
        slippage_pct=0.0005
    )
    bt_res = engine.run()

    bench_comp = bt_res.get("benchmark_comparison", {})
    bench_return = bt_res.get("benchmark_return_pct", bench_comp.get("buy_and_hold", {}).get("total_return_pct", 0.0))
    alpha_excess = bench_comp.get("alpha_excess_return_pct", round(bt_res["total_return_pct"] - bench_return, 2))

    # Market Regime Summary
    regime_series = MarketRegimeClassifier.classify_series(bars)
    curr_regime = regime_series[-1]["regime"] if regime_series else "Unknown"

    return {
        "report_id": f"REP-{norm_sym}-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
        "symbol": norm_sym,
        "date_range": {
            "start_date": dates[0],
            "end_date": dates[-1],
            "total_bars": len(bars)
        },
        "price_summary": {
            "latest_close": prices[-1],
            "period_high": max(prices),
            "period_low": min(prices),
            "total_volume": sum(b.get("volume", 0) for b in bars)
        },
        "performance_metrics": {
            "total_cumulative_return_pct": round(total_cum_ret, 2),
            "cagr_pct": round(cagr_val, 2),
            "annualized_volatility_pct": round(ann_vol, 2),
            "downside_volatility_pct": round(downside_vol, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "max_drawdown_pct": round(max_dd * 100.0, 2),
            "max_drawdown_duration_days": max_dd_len,
            "var_95_pct": round(var_95, 2),
            "cvar_95_pct": round(cvar_95, 2)
        },
        "correlation_profile": peer_correlations,
        "current_market_regime": curr_regime,
        "baseline_backtest": {
            "strategy": "Dual SMA Golden Cross (20/50)",
            "total_return_pct": bt_res["total_return_pct"],
            "sharpe_ratio": bt_res["sharpe_ratio"],
            "max_drawdown_pct": bt_res["max_drawdown_pct"],
            "total_trades": bt_res["total_trades"],
            "benchmark_return_pct": bench_return,
            "alpha_excess_return_pct": alpha_excess
        },
        "generated_at": datetime.utcnow().isoformat()
    }
