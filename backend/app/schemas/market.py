"""
Pydantic Schemas for Market Data API endpoints.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class MarketDataPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 date (YYYY-MM-DD)", examples=["2025-12-31"])
    asset: str = Field(..., description="Standard asset identifier name", examples=["Gold"])
    open: float = Field(..., description="Opening price in USD", examples=[4353.00])
    high: float = Field(..., description="Session high price in USD", examples=[4353.00])
    low: float = Field(..., description="Session low price in USD", examples=[4284.30])
    close: float = Field(..., description="Session closing / settlement price in USD", examples=[4337.10])
    volume: float = Field(..., description="Session traded volume", examples=[135785.0])


class AssetItem(BaseModel):
    symbol: str = Field(..., description="Asset symbol identifier", examples=["Gold"])
    name: str = Field(..., description="Full asset name", examples=["Gold"])
    category: Optional[str] = Field(None, description="Asset classification category", examples=["Commodity"])


class AssetListResponse(BaseModel):
    assets: List[AssetItem] = Field(..., description="List of supported market assets")


class AssetMetadataResponse(BaseModel):
    asset: str = Field(..., description="Standard asset identifier", examples=["NVIDIA"])
    start_date: str = Field(..., description="First available observation date", examples=["1999-01-22"])
    end_date: str = Field(..., description="Last available observation date", examples=["2025-12-31"])
    records: int = Field(..., description="Total count of historical records", examples=[6778])
    frequency: str = Field(default="daily", description="Time-series frequency", examples=["daily"])


class DateRangeInfo(BaseModel):
    start_date: str = Field(..., description="Earliest available date (YYYY-MM-DD)", examples=["2000-08-30"])
    end_date: str = Field(..., description="Latest available date (YYYY-MM-DD)", examples=["2025-12-31"])
    records: int = Field(..., description="Total count of records", examples=[6358])


class MultiAssetDateRangeResponse(BaseModel):
    assets: Dict[str, DateRangeInfo] = Field(..., description="Date range metadata per asset")


class HistoricalDataResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["Gold"])
    frequency: str = Field(default="daily", description="Time-series frequency", examples=["daily"])
    count: int = Field(..., description="Number of returned data records", examples=[100])
    data: List[MarketDataPoint] = Field(..., description="List of daily OHLCV bars")


class MultiAssetHistoricalDataResponse(BaseModel):
    frequency: str = Field(default="daily", description="Time-series frequency", examples=["daily"])
    count: int = Field(..., description="Number of returned data records", examples=[300])
    data: List[MarketDataPoint] = Field(..., description="List of multi-asset daily OHLCV bars")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message description", examples=["Asset not found"])
