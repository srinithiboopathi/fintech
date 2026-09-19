from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.repositories import AssetRepository, MarketPriceRepository
from app.correlation.matrix import CorrelationMatrix
from app.correlation.rolling import RollingCorrelation

router = APIRouter(prefix="/correlation", tags=["Correlation Lab"])

@router.get("/matrix")
def get_matrix(
    method: str = Query("pearson", description="Correlation method: 'pearson' or 'spearman'"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
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
        asset = AssetRepository.get_by_symbol(db, s)
        if not asset:
            raise HTTPException(status_code=500, detail=f"Market data for asset '{s}' could not be loaded.")

        prices = MarketPriceRepository.get_prices_for_asset(db, asset.id)
        if not prices:
            raise HTTPException(status_code=500, detail=f"Market data for asset '{s}' could not be loaded.")

        returns_map = {}
        prev_close = None
        for p in prices:
            ret = (p.close - prev_close) / prev_close if prev_close is not None and prev_close > 0 else 0.0
            prev_close = p.close
            returns_map[p.date] = ret

        asset_bars[s] = returns_map

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
    window: int = Query(30, ge=5, le=252, description="Rolling window size in trading days"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Computes dynamic rolling pairwise correlation between two assets over a sliding window.
    """
    obj_a = AssetRepository.get_by_symbol(db, asset_a)
    obj_b = AssetRepository.get_by_symbol(db, asset_b)

    if not obj_a:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_a}'.")
    if not obj_b:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_b}'.")

    prices_a = MarketPriceRepository.get_prices_for_asset(db, obj_a.id)
    prices_b = MarketPriceRepository.get_prices_for_asset(db, obj_b.id)

    if not prices_a:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_a}'.")
    if not prices_b:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{asset_b}'.")

    bars_a = {}
    prev_close_a = None
    for p in prices_a:
        ret = (p.close - prev_close_a) / prev_close_a if prev_close_a is not None and prev_close_a > 0 else 0.0
        prev_close_a = p.close
        bars_a[p.date] = ret

    bars_b = {}
    prev_close_b = None
    for p in prices_b:
        ret = (p.close - prev_close_b) / prev_close_b if prev_close_b is not None and prev_close_b > 0 else 0.0
        prev_close_b = p.close
        bars_b[p.date] = ret

    common_dates = sorted(list(set(bars_a.keys()) & set(bars_b.keys())))
    if len(common_dates) < window:
        raise HTTPException(status_code=400, detail=f"Insufficient overlapping dates ({len(common_dates)}) for window size {window}.")

    rets_a = [bars_a[d] for d in common_dates]
    rets_b = [bars_b[d] for d in common_dates]

    rolling_series = RollingCorrelation.calculate_rolling(common_dates, rets_a, rets_b, window)

    return {
        "asset_a": obj_a.symbol,
        "asset_b": obj_b.symbol,
        "window": window,
        "total_points": len(rolling_series),
        "series": rolling_series
    }
