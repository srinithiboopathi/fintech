from typing import List, Optional
from pydantic import BaseModel

class AssetSchema(BaseModel):
    id: str
    symbol: str
    name: str
    asset_type: str

    class Config:
        from_attributes = True

class MarketPriceSchema(BaseModel):
    id: Optional[int] = None
    asset_id: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        from_attributes = True

class OHLCVBar(BaseModel):
    date: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: float
    daily_return: Optional[float] = 0.0

class AssetOverview(BaseModel):
    symbol: str
    name: str
    category: str
    current_price: float
    change_24h: float
    volatility_30d: float
    sharpe_1y: float
    regime: str
    volume_24h: float
    high_52w: float
    low_52w: float
    sparkline: List[float] = []

class MarketDataResponse(BaseModel):
    symbol: str
    total_bars: int
    bars: List[OHLCVBar]
