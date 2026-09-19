from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from app.data.providers.csv_provider import CSVMarketProvider
from app.analysis.market_regimes import MarketRegimeClassifier

router = APIRouter(prefix="/regimes", tags=["Market Regimes"])
provider = CSVMarketProvider()

@router.get("/detect/{symbol}")
def detect_regimes(symbol: str) -> Dict[str, Any]:
    bars = provider.get_historical_bars(symbol)
    if not bars:
        raise HTTPException(status_code=404, detail=f"No data for symbol '{symbol}'.")

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
        "symbol": symbol.upper(),
        "current_regime": current_regime,
        "distribution_pct": distribution,
        "series": series_regimes[-60:] # last 60 days
    }
