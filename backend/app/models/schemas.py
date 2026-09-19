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

# ----------------------------------------------------------------------
# Step 3: Clean Historical Data & Quality Schemas
# ----------------------------------------------------------------------

class CleanHistoricalPoint(BaseModel):
    """Validated, normalized, and cleaned OHLCV data point."""
    timestamp: str = Field(..., description="UTC ISO-8601 formatted timestamp")
    open: float = Field(..., description="Opening price (strictly positive float)")
    high: float = Field(..., description="Highest price in period (>= low and >= max(open, close))")
    low: float = Field(..., description="Lowest price in period (<= high and <= min(open, close))")
    close: float = Field(..., description="Closing price (strictly positive float)")
    volume: Optional[float] = Field(None, description="Trading volume; strictly null when not provided by provider")
    asset: str = Field(..., description="Normalized asset name (e.g. NVIDIA, Bitcoin, Gold)")
    symbol: str = Field(..., description="Normalized ticker/symbol (e.g. NVDA, BTC/USD, XAU/USD)")
    source: str = Field(..., description="Provider source (e.g. Twelve Data, Alpha Vantage)")
    is_valid: bool = Field(default=True, description="Indicates record passed all validation checks")

class DataQualityReport(BaseModel):
    """Detailed quality assessment for a cleaned dataset."""
    total_records: int = Field(..., description="Total clean records in dataset")
    raw_records: int = Field(..., description="Number of raw records processed")
    duplicates_removed: int = Field(default=0, description="Count of duplicate timestamps dropped")
    invalid_records_dropped: int = Field(default=0, description="Count of non-numeric, negative, or invalid records dropped")
    missing_close_count: int = Field(default=0, description="Count of records missing close price")
    missing_volume_count: int = Field(default=0, description="Count of records with null volume (expected for spot crypto/gold)")
    ohlc_anomalies_detected: int = Field(default=0, description="Count of records where OHLC bounds required reconciliation")
    earliest_timestamp: Optional[str] = Field(None, description="Earliest UTC timestamp in series")
    latest_timestamp: Optional[str] = Field(None, description="Latest UTC timestamp in series")
    quality_status: str = Field(..., description="Quality assessment: 'pristine', 'good', or 'acceptable'")
    issues: List[str] = Field(default_factory=list, description="Descriptive list of issues detected or handled")

class CleanMarketDataResponse(BaseModel):
    """Clean historical market dataset ready for quantitative analysis and backtesting."""
    asset: str
    symbol: str
    source: str
    data_status: str = Field(default="clean_verified", description="Indicates data has undergone cleaning and validation")
    count: int
    quality_report: DataQualityReport
    data: List[CleanHistoricalPoint]

class DataSummaryResponse(BaseModel):
    """Concise executive summary of clean market data quality and boundaries."""
    asset: str
    symbol: str
    source: str
    total_records: int
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None
    missing_value_count: Dict[str, int] = Field(..., description="Breakdown of missing values by column")
    duplicate_count: int
    latest_close: Optional[float] = None
    data_quality: str = Field(..., description="Overall dataset health ('pristine', 'good', 'acceptable')")
    data_status: str = "clean_verified"
