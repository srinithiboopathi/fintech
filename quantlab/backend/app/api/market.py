from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.repositories import AssetRepository, MarketPriceRepository
from app.data.providers.csv_provider import CSVMarketProvider
from app.schemas.market import AssetOverview, MarketDataResponse

router = APIRouter(prefix="/market", tags=["Market Data"])
provider = CSVMarketProvider()

@router.get("/assets", response_model=List[AssetOverview])
def get_assets():
    """Retrieve all supported assets and current live quantitative telemetry."""
    return provider.get_supported_assets()

@router.get("/history/{symbol}", response_model=MarketDataResponse)
def get_historical_bars(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Retrieve historical daily OHLCV bars for a specified symbol."""
    asset = AssetRepository.get_by_symbol(db, symbol)
    if not asset:
        raise HTTPException(status_code=404, detail=f"No market data found for symbol '{symbol}'.")

    prices = MarketPriceRepository.get_prices_for_asset(db, asset.id, start_date, end_date)
    if not prices:
        raise HTTPException(status_code=404, detail=f"No market data found for symbol '{symbol}'.")

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
            "adj_close": p.close,
            "volume": p.volume,
            "daily_return": round(daily_return, 6)
        })

    return {
        "symbol": asset.symbol,
        "total_bars": len(bars),
        "bars": bars
    }

@router.get("/{symbol}/history", response_model=MarketDataResponse)
def get_historical_bars_alt(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Alternate route: /api/market/{symbol}/history."""
    return get_historical_bars(symbol, start_date, end_date, db)
