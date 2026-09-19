from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.repositories import AssetRepository, MarketPriceRepository
from app.analysis.market_regimes import MarketRegimeClassifier

router = APIRouter(prefix="/regimes", tags=["Market Regimes"])

@router.get("/detect/{symbol}")
def detect_regimes(symbol: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    asset = AssetRepository.get_by_symbol(db, symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{symbol}'.")

    prices = MarketPriceRepository.get_prices_for_asset(db, asset.id)
    if not prices:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{symbol}'.")

    bars = [
        {
            "date": p.date,
            "close": p.close,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "volume": p.volume
        }
        for p in prices
    ]

    series_regimes = MarketRegimeClassifier.classify_series(bars)
    
    # Calculate regime distribution
    counts = {}
    for item in series_regimes:
        reg = item["regime"]
        counts[reg] = counts.get(reg, 0) + 1

    total = len(series_regimes)
    distribution = {k: round(v / total * 100.0, 1) for k, v in counts.items()}

    current_regime = series_regimes[-1] if series_regimes else {}

    return {
        "symbol": asset.symbol,
        "current_regime": current_regime,
        "distribution_pct": distribution,
        "series": series_regimes[-60:] # last 60 days
    }
