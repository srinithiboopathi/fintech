from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from app.data.providers.csv_provider import CSVMarketProvider
from app.correlation.matrix import CorrelationMatrix
from app.correlation.rolling import RollingCorrelation

router = APIRouter(prefix="/correlation", tags=["Correlation Lab"])
provider = CSVMarketProvider()

@router.get("/matrix")
def get_matrix(method: str = Query("pearson", description="Correlation method: 'pearson' or 'spearman'")) -> Dict[str, Any]:
    """
    Computes aligned pairwise correlation matrix across Gold, Bitcoin, and NVIDIA
    based on historical percentage returns.
    """
    symbols = ["GC=F", "BTC-USD", "NVDA"]
    label_map = {
        "GC=F": "Gold (GC=F)",
        "BTC-USD": "Bitcoin (BTC)",
        "NVDA": "NVIDIA (NVDA)"
    }
    
    asset_bars = {}
    for s in symbols:
        bars = provider.get_historical_bars(s)
        if not bars:
            raise HTTPException(status_code=500, detail=f"Market data for asset '{s}' could not be loaded.")
        asset_bars[s] = {b["date"]: b["daily_return"] for b in bars}

    # Find common overlapping trading dates
    date_sets = [set(asset_bars[s].keys()) for s in symbols]
    common_dates = sorted(list(set.intersection(*date_sets)))
    if not common_dates:
        raise HTTPException(status_code=400, detail="No overlapping trading dates found across assets.")

    data_dict = {s: [asset_bars[s][d] for d in common_dates] for s in symbols}
    matrix = CorrelationMatrix.calculate_matrix(data_dict, symbols, method=method)

    return {
        "symbols": [label_map[s] for s in symbols],
        "raw_symbols": symbols,
        "total_aligned_days": len(common_dates),
        "start_date": common_dates[0],
        "end_date": common_dates[-1],
        "matrix": matrix,
        "method": method
    }

@router.get("/rolling")
def get_rolling_correlation(
    asset_a: str = Query("BTC-USD", description="First asset symbol (e.g., BTC, GOLD, NVDA)"),
    asset_b: str = Query("GC=F", description="Second asset symbol (e.g., GC=F, NVDA, BTC)"),
    window: int = Query(30, ge=5, le=252, description="Rolling window size in trading days")
) -> Dict[str, Any]:
    """
    Computes dynamic rolling pairwise correlation between two assets over a sliding window.
    """
    norm_a = provider.normalize_symbol(asset_a)
    norm_b = provider.normalize_symbol(asset_b)

    bars_raw_a = provider.get_historical_bars(norm_a)
    bars_raw_b = provider.get_historical_bars(norm_b)

    if not bars_raw_a:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_a}'.")
    if not bars_raw_b:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_b}'.")

    bars_a = {b["date"]: b["daily_return"] for b in bars_raw_a}
    bars_b = {b["date"]: b["daily_return"] for b in bars_raw_b}

    common_dates = sorted(list(set(bars_a.keys()) & set(bars_b.keys())))
    if len(common_dates) < window:
        raise HTTPException(status_code=400, detail=f"Insufficient overlapping dates ({len(common_dates)}) for window size {window}.")

    rets_a = [bars_a[d] for d in common_dates]
    rets_b = [bars_b[d] for d in common_dates]

    rolling_series = RollingCorrelation.calculate_rolling(common_dates, rets_a, rets_b, window)

    return {
        "asset_a": norm_a,
        "asset_b": norm_b,
        "window": window,
        "total_points": len(rolling_series),
        "series": rolling_series
    }
