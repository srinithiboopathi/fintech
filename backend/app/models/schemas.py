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

# ----------------------------------------------------------------------
# Step 4: Quantitative Moving Average Indicators Schemas
# ----------------------------------------------------------------------

class IndicatorPoint(BaseModel):
    """Quantitative indicator data point with SMA and EMA values."""
    timestamp: str = Field(..., description="UTC ISO-8601 formatted timestamp")
    close: float = Field(..., description="Closing price")
    sma: Optional[float] = Field(None, description="Simple Moving Average (null if insufficient history)")
    ema: Optional[float] = Field(None, description="Exponential Moving Average (null if insufficient history)")

class IndicatorsSummary(BaseModel):
    """Statistical summary of calculated moving average indicators."""
    requested_sma_period: int = Field(..., description="Configured SMA period")
    requested_ema_period: int = Field(..., description="Configured EMA period")
    total_records: int = Field(..., description="Total chronological records analyzed")
    valid_sma_count: int = Field(..., description="Count of non-null SMA observations")
    valid_ema_count: int = Field(..., description="Count of non-null EMA observations")
    latest_close: Optional[float] = Field(None, description="Most recent closing price in series")
    latest_sma: Optional[float] = Field(None, description="Most recent calculated SMA value")
    latest_ema: Optional[float] = Field(None, description="Most recent calculated EMA value")

class IndicatorsResponse(BaseModel):
    """Complete quantitative indicator response payload."""
    asset: str
    symbol: str
    source: str
    data_status: str = Field(default="calculated", description="Status of indicator computation")
    summary: IndicatorsSummary
    data: List[IndicatorPoint]

# ----------------------------------------------------------------------
# Step 5: Returns and Volatility Analysis Schemas
# ----------------------------------------------------------------------

class RiskMetricPoint(BaseModel):
    """Normalized data point containing closing price, daily percentage return, and rolling volatility."""
    timestamp: str = Field(..., description="UTC ISO-8601 formatted timestamp")
    close: float = Field(..., description="Closing price")
    return_pct: Optional[float] = Field(None, description="Percentage daily return: ((Close_t / Close_(t-1)) - 1) * 100")
    volatility: Optional[float] = Field(None, description="Sample standard deviation (ddof=1) of returns in percentage points (not annualized)")

class RiskMetricsSummary(BaseModel):
    """Statistical summary of return and volatility metrics."""
    volatility_period: int = Field(..., description="Configured rolling volatility window (observations)")
    total_records: int = Field(..., description="Total chronological records analyzed")
    valid_return_count: int = Field(..., description="Count of valid percentage return observations")
    valid_volatility_count: int = Field(..., description="Count of valid rolling volatility observations")
    latest_close: Optional[float] = Field(None, description="Most recent closing price in series")
    latest_return: Optional[float] = Field(None, description="Most recent percentage daily return")
    latest_volatility: Optional[float] = Field(None, description="Most recent rolling daily volatility (percentage points, not annualized)")

class RiskMetricsResponse(BaseModel):
    """Complete quantitative returns and volatility response payload."""
    asset: str
    symbol: str
    source: str
    data_status: str = Field(default="calculated", description="Status of risk metrics computation")
    summary: RiskMetricsSummary
    data: List[RiskMetricPoint]


# ==============================================================================
# Step 6: Sharpe Ratio and Maximum Drawdown Models
# ==============================================================================

class DrawdownPoint(BaseModel):
    """Historical drawdown observation with running peak."""
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp")
    close: float = Field(..., description="Closing price for the observation")
    running_peak: float = Field(..., description="Running peak closing price observed up to this point")
    drawdown_pct: float = Field(..., description="Percentage drawdown from running peak ((close / peak) - 1) * 100")


class RiskAnalysisSummary(BaseModel):
    """Executive summary of annualized Sharpe Ratio and Maximum Drawdown analysis."""
    risk_free_rate: float = Field(..., description="Annual risk-free rate percentage used")
    annualization_factor: int = Field(..., description="Trading periods per year used for annualization (default 252)")
    valid_return_count: int = Field(..., description="Number of valid daily return observations")
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio (null if fewer than 2 returns or zero std dev)")
    maximum_drawdown_pct: Optional[float] = Field(None, description="Maximum historical peak-to-trough percentage drawdown")
    maximum_drawdown_timestamp: Optional[str] = Field(None, description="ISO-8601 timestamp where maximum drawdown occurred")
    latest_close: Optional[float] = Field(None, description="Latest clean closing price in the series")


class RiskAnalysisResponse(BaseModel):
    """Complete annualized Sharpe Ratio and Maximum Drawdown response payload."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Market asset symbol")
    source: str = Field(..., description="Underlying market data provider source")
    data_status: str = Field("calculated", description="Data processing status")
    summary: RiskAnalysisSummary = Field(..., description="Executive risk and performance analysis summary")
    drawdown_series: List[DrawdownPoint] = Field(default_factory=list, description="Historical drawdown and running peak time series")


# ==============================================================================
# Step 7: Correlation & Rolling Correlation Models
# ==============================================================================

class CorrelationMatrixResponse(BaseModel):
    """Pairwise Pearson correlation matrix across multi-asset universe computed on aligned daily returns."""
    assets: List[str] = Field(..., description="List of included assets")
    symbols: List[str] = Field(..., description="List of asset ticker symbols")
    matrix: Dict[str, Dict[str, Optional[float]]] = Field(..., description="Symmetric correlation matrix by symbol with 1.0 diagonal")
    observation_count: int = Field(..., description="Number of strictly overlapping, aligned daily return observations")
    start_date: Optional[str] = Field(None, description="Start date of overlapping return observations")
    end_date: Optional[str] = Field(None, description="End date of overlapping return observations")
    source: str = Field(default="Twelve Data", description="Market data provider source")
    data_status: str = Field(default="calculated", description="Data processing status")
    methodology: str = Field(
        default="Pearson correlation on aligned daily percentage returns ((close_t / close_{t-1}) - 1)",
        description="Mathematical methodology description"
    )

class RollingCorrelationPoint(BaseModel):
    """Observation point for rolling correlation series."""
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp or date")
    correlation: Optional[float] = Field(None, description="Rolling Pearson correlation coefficient (null for first window-1 warmup points)")

class RollingPairSeries(BaseModel):
    """Rolling correlation series for a specific asset pair."""
    pair: str = Field(..., description="Asset pair descriptor, e.g. 'NVDA vs BTC/USD'")
    asset1: str = Field(..., description="First asset identifier or symbol")
    asset2: str = Field(..., description="Second asset identifier or symbol")
    window: int = Field(..., description="Configured rolling lookback window in observations")
    observation_count: int = Field(..., description="Total overlapping return observations for this pair")
    valid_correlation_count: int = Field(..., description="Count of valid (non-null) rolling correlation values")
    latest_correlation: Optional[float] = Field(None, description="Most recent valid rolling correlation value")
    series: List[RollingCorrelationPoint] = Field(default_factory=list, description="Chronological rolling correlation time series")

class RollingCorrelationResponse(BaseModel):
    """Complete rolling correlation response payload across asset pairs."""
    window: int = Field(..., description="Rolling lookback window in observations")
    assets: List[str] = Field(..., description="List of included assets")
    source: str = Field(default="Twelve Data", description="Market data provider source")
    data_status: str = Field(default="calculated", description="Data processing status")
    pairs: List[RollingPairSeries] = Field(default_factory=list, description="Rolling correlation time series for each pairwise combination")




