from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HistoricalPoint(BaseModel):
    """Normalized OHLCV data point."""
    timestamp: str = Field(..., description="UTC ISO-8601 formatted timestamp or date")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price in period")
    low: float = Field(..., description="Lowest price in period")
    close: float = Field(..., description="Closing price")
    volume: Optional[float] = Field(None, description="Trading volume where available")
    asset: str = Field(..., description="Normalized asset name (e.g. NVIDIA, Bitcoin, Gold)")
    symbol: str = Field(..., description="Normalized asset ticker/symbol (e.g. NVDA, BTC/USD, XAU/USD)")
    source: str = Field(default="Twelve Data", description="Data source provider")

class HistoricalDataResponse(BaseModel):
    """Normalized historical time series payload."""
    asset: str
    symbol: str
    source: str = "Twelve Data"
    data_status: str = Field(
        default="latest_available",
        description="Indicates data status: 'latest_available' or 'delayed' (never 'real-time')"
    )
    count: int
    data: List[HistoricalPoint]

class LatestMarketDataResponse(BaseModel):
    """Normalized latest available market price payload."""
    asset: str
    symbol: str
    price: float
    timestamp: str = Field(..., description="UTC ISO-8601 formatted timestamp")
    source: str = "Twelve Data"
    data_status: str = Field(
        default="latest_available",
        description="Clearly indicates 'latest_available' or 'delayed' (never 'real-time')"
    )
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[str] = None

class AssetMetadata(BaseModel):
    """Metadata for a supported asset."""
    asset_id: str
    name: str
    symbol: str
    asset_class: str
    description: str
    supported_endpoints: List[str]

class AssetsListResponse(BaseModel):
    """Response containing all supported assets."""
    assets: List[AssetMetadata]
    count: int

class HealthResponse(BaseModel):
    """System and API configuration health status."""
    status: str
    primary_provider: str = "twelve_data"
    fallback_provider: str = "alpha_vantage"
    twelve_data_configured: bool = False
    twelve_data_masked_key: str = ""
    alpha_vantage_configured: bool = False
    alpha_vantage_masked_key: str = ""
    api_key_configured: bool
    masked_key: str
    environment: str
    timestamp: str
    cache_stats: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Standardized error payload."""
    error: str
    message: str
    error_type: str
    status_code: int
    details: Dict[str, Any] = {}
    timestamp: str
