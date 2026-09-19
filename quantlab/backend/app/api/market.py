from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
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
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """Retrieve historical daily OHLCV bars for a specified symbol."""
    bars = provider.get_historical_bars(symbol, start_date, end_date)
    if not bars:
        raise HTTPException(status_code=404, detail=f"No market data found for symbol '{symbol}'.")
    return {
        "symbol": provider.normalize_symbol(symbol),
        "total_bars": len(bars),
        "bars": bars
    }

@router.get("/{symbol}/history", response_model=MarketDataResponse)
def get_historical_bars_alt(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD")
):
    """Alternate route: /api/market/{symbol}/history."""
    return get_historical_bars(symbol, start_date, end_date)
