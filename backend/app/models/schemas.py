from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator

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


# ==============================================================================
# Step 8: Strategy-Agnostic Backtesting Models
# ==============================================================================

class SignalPoint(BaseModel):
    """Trading signal observation."""
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp corresponding to historical observation")
    signal: str = Field(..., description="Signal directive: 'BUY', 'SELL', or 'HOLD'")


class BacktestRequest(BaseModel):
    """Configuration payload for backtest execution."""
    initial_capital: Optional[float] = Field(100000.0, description="Initial investment capital in base currency (must be > 0, default 100,000.0)")
    transaction_cost_rate: Optional[float] = Field(0.001, description="Per-trade transaction cost percentage fraction (must be >= 0, default 0.001 = 0.1%)")
    allocation_fraction: Optional[float] = Field(1.0, description="Fraction of available cash to invest on BUY (must be in (0, 1], default 1.0 = 100%)")
    signals: Optional[List[SignalPoint]] = Field(None, description="Optional sequence of trading signals aligned with historical data")


class TradeRecord(BaseModel):
    """Individual executed transaction record."""
    trade_id: int = Field(..., description="Chronological trade index (1-based)")
    timestamp: str = Field(..., description="ISO-8601 timestamp of execution (time t+1)")
    side: str = Field(..., description="Trade side: 'BUY' or 'SELL'")
    price: float = Field(..., description="Execution close price at time of execution")
    quantity: float = Field(..., description="Asset units / shares transacted")
    trade_value: float = Field(..., description="Gross value of trade (price * quantity)")
    transaction_cost: float = Field(..., description="Fee deducted for trade execution")
    resulting_cash: float = Field(..., description="Cash balance immediately following trade")
    resulting_position: float = Field(..., description="Total position units held following trade")
    pnl: Optional[float] = Field(None, description="Realized dollar PnL for closed trade (populated on SELL)")
    pnl_percent: Optional[float] = Field(None, description="Realized percentage PnL for closed trade (populated on SELL)")


class PortfolioObservation(BaseModel):
    """Daily portfolio accounting and valuation snapshot."""
    timestamp: str = Field(..., description="ISO-8601 timestamp of observation")
    close_price: float = Field(..., description="Market close price at observation")
    signal: str = Field(..., description="Signal directive generated at this observation ('BUY', 'SELL', 'HOLD')")
    executed_action: str = Field(..., description="Action executed at this observation ('BUY', 'SELL', 'HOLD', 'NONE')")
    cash: float = Field(..., description="Cash balance in portfolio")
    position_quantity: float = Field(..., description="Asset position units held")
    position_market_value: float = Field(..., description="Current market value of asset position")
    transaction_cost: float = Field(..., description="Transaction fees incurred on this observation")
    portfolio_value: float = Field(..., description="Total portfolio equity value (cash + position_market_value)")
    portfolio_return_pct: Optional[float] = Field(None, description="Daily percentage change in portfolio value")


class BenchmarkPoint(BaseModel):
    """Benchmark equity observation."""
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    portfolio_value: float = Field(..., description="Benchmark equity value")
    total_return_pct: float = Field(..., description="Cumulative percentage return of benchmark from inception")


class BenchmarkResults(BaseModel):
    """Benchmark comparison performance metrics (Buy-and-Hold)."""
    benchmark_name: str = Field(default="Buy & Hold", description="Name of benchmark strategy")
    initial_value: float = Field(..., description="Initial capital allocated to benchmark")
    final_value: float = Field(..., description="Final equity value of benchmark")
    total_return_pct: float = Field(..., description="Total percentage return of benchmark")
    initial_capital: Optional[float] = Field(None, description="Alias for initial_value")
    final_portfolio_value: Optional[float] = Field(None, description="Alias for final_value")
    total_return: Optional[float] = Field(None, description="Alias for total_return_pct")
    equity_curve: List[BenchmarkPoint] = Field(default_factory=list, description="Benchmark historical equity curve")

    @model_validator(mode="after")
    def populate_benchmark_aliases(self) -> "BenchmarkResults":
        if self.initial_capital is None:
            self.initial_capital = self.initial_value
        if self.final_portfolio_value is None:
            self.final_portfolio_value = self.final_value
        if self.total_return is None:
            self.total_return = self.total_return_pct
        return self


class BacktestPerformance(BaseModel):
    """Executive portfolio performance metrics."""
    initial_capital: float = Field(..., description="Starting investment capital")
    final_portfolio_value: float = Field(..., description="Final portfolio liquidation / market value")
    total_return_pct: float = Field(..., description="Total cumulative strategy return percentage")
    total_trades: int = Field(..., description="Total number of executed trades (BUY + SELL)")
    winning_trades: int = Field(..., description="Number of round-trip trades with positive realized PnL")
    losing_trades: int = Field(..., description="Number of round-trip trades with negative realized PnL")
    win_rate_pct: Optional[float] = Field(None, description="Percentage of profitable completed trades")
    total_fees_paid: float = Field(..., description="Total transaction fees incurred across backtest")
    maximum_drawdown_pct: Optional[float] = Field(None, description="Maximum peak-to-trough equity decline percentage")
    maximum_drawdown_timestamp: Optional[str] = Field(None, description="Timestamp where maximum drawdown occurred")
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio of strategy daily returns")


class BacktestResponse(BaseModel):
    """Comprehensive backtest simulation response payload."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Market ticker symbol")
    source: str = Field(default="Twelve Data", description="Market data provider source")
    data_status: str = Field(default="calculated", description="Data processing status")
    execution_model: str = Field(
        default="Next-Observation (Signal at t executes at t+1)",
        description="Causal order execution assumption"
    )
    performance: BacktestPerformance = Field(..., description="Executive performance and risk statistics")
    benchmark: BenchmarkResults = Field(..., description="Buy-and-Hold benchmark comparison")
    trade_history: List[TradeRecord] = Field(default_factory=list, description="Chronological log of executed trades")
    equity_curve: List[PortfolioObservation] = Field(default_factory=list, description="Daily portfolio equity and accounting series")


# ==============================================================================
# Step 9: Quantitative Trading Strategies Models
# ==============================================================================

class StrategySignalPoint(BaseModel):
    """Timestamped strategy signal with underlying market and indicator references."""
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp of historical observation")
    signal: str = Field(..., description="Directive generated at time t: 'BUY', 'SELL', or 'HOLD'")
    close: float = Field(..., description="Close price at observation time t")
    indicators: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Reference indicator values at time t (e.g. short_sma, long_sma, ema, momentum, z_score)"
    )


class StrategySignalsRequest(BaseModel):
    """Request payload for strategy signal generation."""
    strategy: str = Field(
        ...,
        description="Strategy identifier: 'sma_crossover', 'ema_trend', 'momentum', 'mean_reversion'"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Strategy-specific parameter overrides"
    )


class StrategySignalsResponse(BaseModel):
    """Response payload for strategy signal generation."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Market ticker symbol")
    strategy: str = Field(..., description="Executed strategy name")
    parameters: Dict[str, Any] = Field(..., description="Active strategy parameters used")
    source: str = Field(default="Twelve Data", description="Underlying market data provider")
    data_status: str = Field(default="calculated", description="Processing status")
    observation_count: int = Field(..., description="Total historical observations analyzed")
    start_date: Optional[str] = Field(None, description="Earliest observation date")
    end_date: Optional[str] = Field(None, description="Latest observation date")
    signals: List[StrategySignalPoint] = Field(..., description="Chronological strategy signals")


class StrategyBacktestRequest(BaseModel):
    """Request payload to simulate a strategy through the Step 8 backtesting engine."""
    strategy: str = Field(
        ...,
        description="Strategy identifier: 'sma_crossover', 'ema_trend', 'momentum', 'mean_reversion'"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Strategy-specific parameter overrides"
    )
    initial_capital: Optional[float] = Field(
        100000.0,
        description="Initial investment capital in base currency (must be > 0, default 100,000.0)"
    )
    transaction_cost_rate: Optional[float] = Field(
        0.001,
        description="Per-trade transaction cost percentage fraction (must be >= 0, default 0.001 = 0.1%)"
    )
    allocation: Optional[float] = Field(
        1.0,
        description="Fraction of available cash to invest on BUY (must be in (0, 1], default 1.0 = 100%)"
    )
    allocation_fraction: Optional[float] = Field(
        None,
        description="Fraction of available cash to invest on BUY (alias for allocation)"
    )


class StrategyBacktestResponse(BaseModel):
    """Comprehensive backtest simulation response for a strategy."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Market ticker symbol")
    strategy: str = Field(..., description="Executed strategy identifier")
    parameters: Dict[str, Any] = Field(..., description="Strategy configuration parameters")
    source: str = Field(default="Twelve Data", description="Market data provider source")
    data_status: str = Field(default="calculated", description="Data processing status")
    execution_model: str = Field(
        default="Next-Observation (Signal at t executes at t+1 at P_{t+1})",
        description="Causal order execution assumption"
    )
    initial_capital: float = Field(..., description="Initial investment capital")
    final_portfolio_value: float = Field(..., description="Terminal portfolio value")
    total_return: float = Field(..., description="Cumulative total return percentage fraction")
    total_trades: int = Field(..., description="Total executed trade count")
    number_of_trades: int = Field(..., description="Total executed trade count (alias)")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage fraction")
    maximum_drawdown: float = Field(..., description="Maximum drawdown percentage fraction (alias)")
    equity_curve: List[PortfolioObservation] = Field(default_factory=list, description="Daily portfolio equity and accounting series")
    trade_history: List[TradeRecord] = Field(default_factory=list, description="Chronological log of executed trades")
    benchmark: BenchmarkResults = Field(..., description="Buy-and-Hold benchmark comparison")
    benchmark_buy_and_hold: BenchmarkResults = Field(..., description="Buy & Hold benchmark comparison")
    performance: BacktestPerformance = Field(..., description="Executive performance and risk statistics")


# ==============================================================================
# Step 10: Strategy Comparison & Robustness Analysis Models
# ==============================================================================

class StrategyComparisonItem(BaseModel):
    """Factual performance metrics for a single strategy in the comparison matrix."""
    strategy: str = Field(..., description="Strategy identifier: sma_crossover, ema_trend, momentum, mean_reversion")
    parameters: Dict[str, Any] = Field(..., description="Configuration parameters used")
    initial_capital: float = Field(..., description="Starting portfolio capital")
    final_portfolio_value: float = Field(..., description="Terminal portfolio value")
    total_return: float = Field(..., description="Cumulative percentage return")
    total_trades: int = Field(..., description="Total executed trade count")
    number_of_trades: int = Field(..., description="Total executed trade count (alias)")
    winning_trades: int = Field(..., description="Count of profitable round-trip trades")
    losing_trades: int = Field(..., description="Count of unprofitable round-trip trades")
    win_rate_pct: Optional[float] = Field(None, description="Win rate percentage")
    maximum_drawdown: float = Field(..., description="Maximum peak-to-trough decline percentage")
    max_drawdown: float = Field(..., description="Maximum peak-to-trough decline percentage (alias)")
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio")
    total_fees_paid: float = Field(..., description="Total transaction fees incurred")
    benchmark_return: float = Field(..., description="Baseline Buy-and-Hold total return percentage")
    excess_return_vs_benchmark: float = Field(..., description="Strategy total return minus benchmark total return percentage")


class StrategyComparisonRequest(BaseModel):
    """Request payload to compare all or selected strategies under identical market assumptions."""
    strategies: Optional[List[str]] = Field(
        None,
        description="Optional subset of strategies to compare. Defaults to all 4 supported strategies."
    )
    strategy_configs: Optional[Dict[str, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Optional custom parameter dictionary for each strategy identifier"
    )
    initial_capital: Optional[float] = Field(
        100000.0,
        description="Identical starting capital across all strategies (must be > 0)"
    )
    transaction_cost_rate: Optional[float] = Field(
        0.001,
        description="Identical transaction cost fraction across all strategies (must be >= 0)"
    )
    allocation: Optional[float] = Field(
        1.0,
        description="Identical cash allocation fraction across all strategies in (0, 1]"
    )
    allocation_fraction: Optional[float] = Field(
        None,
        description="Alias for allocation"
    )


class StrategyComparisonResponse(BaseModel):
    """Comparative factual performance evaluation across strategies under identical market conditions."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Asset market ticker symbol")
    source: str = Field(default="Twelve Data", description="Market data source provider")
    data_status: str = Field(default="calculated", description="Data processing status")
    execution_model: str = Field(
        default="Next-Observation (Signal at t executes at t+1 at P_{t+1})",
        description="Causal execution assumption applied identically to all strategies"
    )
    observation_count: int = Field(..., description="Number of aligned historical observations")
    start_date: Optional[str] = Field(None, description="Earliest observation timestamp")
    end_date: Optional[str] = Field(None, description="Latest observation timestamp")
    benchmark: BenchmarkResults = Field(..., description="Identical Buy-and-Hold benchmark results")
    benchmark_buy_and_hold: BenchmarkResults = Field(..., description="Buy-and-Hold benchmark (alias)")
    strategies: List[StrategyComparisonItem] = Field(..., description="Factual metrics for each strategy")


class RobustnessCombinationResult(BaseModel):
    """Performance metrics for one specific parameter combination in robustness testing."""
    strategy: str = Field(..., description="Strategy identifier")
    parameters: Dict[str, Any] = Field(..., description="Tested parameter set")
    initial_capital: float = Field(..., description="Starting capital")
    final_portfolio_value: float = Field(..., description="Terminal portfolio value")
    total_return: float = Field(..., description="Cumulative percentage return")
    total_trades: int = Field(..., description="Executed trade count")
    number_of_trades: int = Field(..., description="Executed trade count (alias)")
    maximum_drawdown: float = Field(..., description="Maximum drawdown percentage")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage (alias)")
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio")
    total_fees_paid: float = Field(..., description="Total fees paid")
    benchmark_return: float = Field(..., description="Benchmark percentage return")
    excess_return_vs_benchmark: float = Field(..., description="Strategy total return minus benchmark return")


class RobustnessAnalysisRequest(BaseModel):
    """Request payload to perform parameter sensitivity and robustness testing."""
    strategy: str = Field(
        ...,
        description="Target strategy identifier: 'sma_crossover', 'ema_trend', 'momentum', 'mean_reversion'"
    )
    parameter_grid: Dict[str, List[Any]] = Field(
        ...,
        description="Dictionary mapping parameter names to lists of discrete test values"
    )
    initial_capital: Optional[float] = Field(
        100000.0,
        description="Starting capital (must be > 0)"
    )
    transaction_cost_rate: Optional[float] = Field(
        0.001,
        description="Transaction fee fraction (must be >= 0)"
    )
    allocation: Optional[float] = Field(
        1.0,
        description="Cash allocation fraction in (0, 1]"
    )
    allocation_fraction: Optional[float] = Field(
        None,
        description="Alias for allocation"
    )


class RobustnessAnalysisResponse(BaseModel):
    """Comprehensive parameter sensitivity analysis response."""
    asset: str = Field(..., description="Asset display name")
    symbol: str = Field(..., description="Asset ticker symbol")
    strategy: str = Field(..., description="Tested strategy identifier")
    source: str = Field(default="Twelve Data", description="Market data source provider")
    data_status: str = Field(default="calculated", description="Data processing status")
    execution_model: str = Field(
        default="Next-Observation (Signal at t executes at t+1 at P_{t+1})",
        description="Causal execution assumption"
    )
    observation_count: int = Field(..., description="Total historical observations analyzed")
    start_date: Optional[str] = Field(None, description="Earliest observation timestamp")
    end_date: Optional[str] = Field(None, description="Latest observation timestamp")
    benchmark: BenchmarkResults = Field(..., description="Buy-and-Hold baseline benchmark")
    benchmark_buy_and_hold: BenchmarkResults = Field(..., description="Buy-and-Hold benchmark (alias)")
    total_combinations_tested: int = Field(..., description="Total valid parameter configurations tested")
    results: List[RobustnessCombinationResult] = Field(..., description="Factual metrics for each parameter combination")





