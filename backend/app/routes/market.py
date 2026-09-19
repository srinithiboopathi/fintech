import math
import re
from datetime import datetime, timezone
from typing import Optional, Any
from fastapi import APIRouter, Query, Path

from app.config import settings
from app.models.schemas import (
    HealthResponse,
    AssetsListResponse,
    HistoricalDataResponse,
    LatestMarketDataResponse,
    CleanMarketDataResponse,
    DataSummaryResponse,
    IndicatorsResponse,
    RiskMetricsResponse,
    RiskAnalysisResponse,
    CorrelationMatrixResponse,
    RollingCorrelationResponse,
    BacktestRequest,
    BacktestResponse,
    StrategySignalsRequest,
    StrategySignalsResponse,
    StrategyBacktestRequest,
    StrategyBacktestResponse,
    StrategyComparisonRequest,
    StrategyComparisonResponse,
    RobustnessAnalysisRequest,
    RobustnessAnalysisResponse,
    MarketRegimesResponse,
    MarketRegimesSummaryResponse,
    StrategyRegimePerformanceResponse,
)
from app.services.market_data import market_data_service
from app.services.cache_manager import cache_manager
from app.utils.exceptions import (
    InvalidIndicatorPeriodError,
    InvalidVolatilityPeriodError,
    InvalidRiskAnalysisParameterError,
    InvalidCorrelationWindowError,
    InvalidBacktestParameterError,
    UnsupportedStrategyError,
    InvalidStrategyParameterError,
    InvalidRegimeParameterError,
)

router = APIRouter()


def validate_indicator_period(val: Any) -> int:
    """
    Validates that a period parameter is a positive integer >= 1.
    Rejects: 0, negative numbers, decimals, non-digit strings, empty values.
    Raises InvalidIndicatorPeriodError (HTTP 400).
    """
    if val is None:
        raise InvalidIndicatorPeriodError()

    val_str = str(val).strip()
    if not val_str:
        raise InvalidIndicatorPeriodError()

    # Reject floats, negative numbers, non-digit characters
    if not re.fullmatch(r"\d+", val_str):
        raise InvalidIndicatorPeriodError()

    period = int(val_str)
    if period < 1:
        raise InvalidIndicatorPeriodError()

    return period

def validate_volatility_period(val: Any) -> int:
    """
    Validates that volatility_period is a positive integer >= 1.
    Rejects: 0, negative numbers, decimals, non-digit strings, empty values.
    Raises InvalidVolatilityPeriodError (HTTP 400).
    """
    if val is None:
        raise InvalidVolatilityPeriodError()

    val_str = str(val).strip()
    if not val_str:
        raise InvalidVolatilityPeriodError()

    # Reject floats, negative numbers, non-digit characters
    if not re.fullmatch(r"\d+", val_str):
        raise InvalidVolatilityPeriodError()

    period = int(val_str)
    if period < 1:
        raise InvalidVolatilityPeriodError()

    return period

def validate_risk_analysis_params(rf_val: Any, af_val: Any) -> tuple[float, int]:
    """
    Validates risk analysis query parameters:
    - risk_free_rate: non-negative float >= 0.0
    - annualization_factor: positive integer >= 1
    Raises InvalidRiskAnalysisParameterError (HTTP 400).
    """
    if rf_val is None:
        rf = 0.0
    else:
        rf_str = str(rf_val).strip()
        try:
            rf = float(rf_str)
            if rf < 0.0 or not math.isfinite(rf):
                raise InvalidRiskAnalysisParameterError()
        except (ValueError, TypeError):
            raise InvalidRiskAnalysisParameterError()

    if af_val is None:
        af = 252
    else:
        af_str = str(af_val).strip()
        if not re.fullmatch(r"\d+", af_str):
            raise InvalidRiskAnalysisParameterError()
        af = int(af_str)
        if af < 1:
            raise InvalidRiskAnalysisParameterError()

    return rf, af

def validate_rolling_window(val: Any) -> int:
    """
    Validates that a rolling correlation window is a positive integer >= 2.
    Rejects: 0, 1, negative numbers, decimals, non-digit strings, empty values.
    Raises InvalidCorrelationWindowError (HTTP 400).
    """
    if val is None:
        raise InvalidCorrelationWindowError()

    val_str = str(val).strip()
    if not val_str:
        raise InvalidCorrelationWindowError()

    # Reject floats, negative numbers, non-digit characters
    if not re.fullmatch(r"\d+", val_str):
        raise InvalidCorrelationWindowError()

    window = int(val_str)
    if window < 2:
        raise InvalidCorrelationWindowError()

    return window


def validate_regime_params(
    trend_val: Any,
    vol_val: Any,
    vol_thresh_val: Any,
    trend_thresh_val: Any,
) -> tuple[int, int, Optional[float], float]:
    """
    Validates market regime query parameters:
    - trend_period: positive integer in [1, 500] (default: 50)
    - volatility_window: positive integer in [2, 500] (default: 20)
    - volatility_threshold: optional positive float in (0.0, 100.0]
    - trend_threshold: float in [0.0, 1.0] (default: 0.0)
    Raises InvalidRegimeParameterError (HTTP 400).
    """
    if trend_val is None:
        tp = 50
    else:
        tp_str = str(trend_val).strip()
        if not re.fullmatch(r"\d+", tp_str):
            raise InvalidRegimeParameterError("trend_period must be a positive integer.")
        tp = int(tp_str)
        if tp < 1 or tp > 500:
            raise InvalidRegimeParameterError("trend_period must be between 1 and 500.")

    if vol_val is None:
        vw = 20
    else:
        vw_str = str(vol_val).strip()
        if not re.fullmatch(r"\d+", vw_str):
            raise InvalidRegimeParameterError("volatility_window must be an integer >= 2.")
        vw = int(vw_str)
        if vw < 2 or vw > 500:
            raise InvalidRegimeParameterError("volatility_window must be between 2 and 500.")

    if vol_thresh_val is None:
        vt = None
    else:
        vt_str = str(vol_thresh_val).strip()
        try:
            vt = float(vt_str)
            if vt <= 0.0 or vt > 100.0 or not math.isfinite(vt):
                raise InvalidRegimeParameterError("volatility_threshold must be a positive float between 0 and 100.")
        except (ValueError, TypeError):
            raise InvalidRegimeParameterError("volatility_threshold must be a numeric value.")

    if trend_thresh_val is None:
        tt = 0.0
    else:
        tt_str = str(trend_thresh_val).strip()
        try:
            tt = float(tt_str)
            if tt < 0.0 or tt > 1.0 or not math.isfinite(tt):
                raise InvalidRegimeParameterError("trend_threshold must be a float between 0.0 and 1.0.")
        except (ValueError, TypeError):
            raise InvalidRegimeParameterError("trend_threshold must be a numeric value.")

    return tp, vw, vt, tt



@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System & Data Layer Health Check",
    tags=["Health"]
)
async def health_check():
    """
    Returns API health status, active market data providers (Twelve Data primary,
    Alpha Vantage fallback), cache statistics, and environment settings.
    """
    return HealthResponse(
        status="healthy",
        primary_provider=settings.PRIMARY_PROVIDER,
        fallback_provider=settings.FALLBACK_PROVIDER,
        twelve_data_configured=settings.is_twelve_data_configured,
        twelve_data_masked_key=settings.masked_twelve_data_key,
        alpha_vantage_configured=settings.is_alpha_vantage_configured,
        alpha_vantage_masked_key=settings.masked_alpha_vantage_key,
        api_key_configured=settings.is_api_key_configured,
        masked_key=settings.masked_api_key,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        cache_stats=cache_manager.get_cache_stats()
    )

@router.get(
    "/assets",
    response_model=AssetsListResponse,
    summary="List Supported Assets",
    tags=["Assets"]
)
async def list_assets():
    """
    Lists the supported multi-asset universe (NVIDIA, Bitcoin, Gold)
    with their tickers, asset classes, and supported routes.
    """
    assets = market_data_service.list_supported_assets()
    return AssetsListResponse(assets=assets, count=len(assets))

@router.get(
    "/market/{asset}/historical",
    response_model=HistoricalDataResponse,
    summary="Get Normalized Historical Market Data",
    tags=["Market Data"]
)
async def get_historical_market_data(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    outputsize: Optional[str] = Query(
        "compact",
        pattern="^(compact|full)$",
        description="Historical depth: 'compact' (recent time series) or 'full' (extended history)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh fetch from market data provider"
    )
):
    """
    Retrieves normalized historical daily price data for the specified asset.
    Uses Twelve Data as primary provider, protected by local cache.
    Timestamps are converted to UTC ISO-8601.
    """
    return await market_data_service.get_historical_data(
        asset_identifier=asset,
        outputsize=outputsize,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/latest",
    response_model=LatestMarketDataResponse,
    summary="Get Latest Available Market Price",
    tags=["Market Data"]
)
async def get_latest_market_data(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh fetch from market data provider"
    )
):
    """
    Retrieves the latest available price quote for the specified asset.
    Clearly marked as 'latest_available' or 'delayed', never 'real-time'.
    """
    return await market_data_service.get_latest_data(
        asset_identifier=asset,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/data",
    response_model=CleanMarketDataResponse,
    summary="Get Clean, Validated Historical Market Data",
    tags=["Clean Market Data"]
)
async def get_clean_market_data(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local clean cache and re-process from provider"
    )
):
    """
    Retrieves clean, validated, and chronologically sorted historical market data.
    - Duplicate timestamps removed
    - Non-numeric or negative prices rejected
    - OHLC relationship bounds verified
    - Volume strictly preserved as null for spot crypto and gold bullion
    - Reuses local cache; does NOT call external provider if valid cached data exists.
    """
    return await market_data_service.get_clean_data(
        asset_identifier=asset,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/data/summary",
    response_model=DataSummaryResponse,
    summary="Get Executive Clean Market Data Summary",
    tags=["Clean Market Data"]
)
async def get_clean_market_data_summary(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh evaluation"
    )
):
    """
    Returns executive summary of clean market data quality:
    - Asset & symbol
    - Provider source
    - Total records
    - Earliest and latest timestamps
    - Missing-value breakdown (close, volume, invalid dropped)
    - Duplicate count
    - Latest close price
    - Overall data quality rating
    """
    return await market_data_service.get_clean_summary(
        asset_identifier=asset,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/indicators",
    response_model=IndicatorsResponse,
    summary="Get Technical Indicators (SMA & EMA)",
    tags=["Quantitative Indicators"]
)
async def get_market_indicators(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    sma_period: Optional[str] = Query(
        "20",
        description="Simple Moving Average period (positive integer >= 1, default 20)"
    ),
    ema_period: Optional[str] = Query(
        "20",
        description="Exponential Moving Average period (positive integer >= 1, default 20)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA)
    for NVIDIA, Bitcoin, or Gold strictly from Step 3 cleaned historical data.

    Query Parameters:
    - sma_period: Positive integer >= 1 (default: 20)
    - ema_period: Positive integer >= 1 (default: 20)
    - refresh: Optional boolean to force fresh fetch and calculation
    """
    valid_sma = validate_indicator_period(sma_period)
    valid_ema = validate_indicator_period(ema_period)

    return await market_data_service.get_indicators(
        asset_identifier=asset,
        sma_period=valid_sma,
        ema_period=valid_ema,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/risk-metrics",
    response_model=RiskMetricsResponse,
    summary="Get Quantitative Risk Metrics (Returns & Volatility)",
    tags=["Risk & Quantitative Metrics"]
)
async def get_market_risk_metrics(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    volatility_period: Optional[str] = Query(
        "20",
        description="Rolling volatility window in observations (positive integer >= 1, default 20)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Calculates percentage daily returns and rolling sample volatility (ddof=1)
    for NVIDIA, Bitcoin, or Gold strictly from Step 3 cleaned historical data.

    Query Parameters:
    - volatility_period: Positive integer >= 1 (default: 20)
    - refresh: Optional boolean to force fresh fetch and calculation
    """
    valid_vol_period = validate_volatility_period(volatility_period)

    return await market_data_service.get_risk_metrics(
        asset_identifier=asset,
        volatility_period=valid_vol_period,
        refresh=refresh or False
    )

@router.get(
    "/market/{asset}/risk-analysis",
    response_model=RiskAnalysisResponse,
    summary="Get Quantitative Risk Analysis (Sharpe Ratio & Maximum Drawdown)",
    tags=["Risk & Quantitative Metrics"]
)
async def get_market_risk_analysis(
    asset: str = Path(..., description="Asset name or symbol (e.g. 'nvidia', 'bitcoin', 'gold')"),
    risk_free_rate: Optional[str] = Query(
        "0.0",
        description="Annualized risk-free rate percentage (non-negative number, default 0.0)"
    ),
    annualization_factor: Optional[str] = Query(
        "252",
        description="Annualization trading periods per year (positive integer >= 1, default 252)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Calculates annualized Sharpe Ratio and Maximum Drawdown analysis
    for NVIDIA, Bitcoin, or Gold strictly from Step 3 cleaned historical data.

    Query Parameters:
    - risk_free_rate: Non-negative float (default: 0.0)
    - annualization_factor: Positive integer >= 1 (default: 252)
    - refresh: Optional boolean to force fresh fetch and calculation
    """
    valid_rf, valid_af = validate_risk_analysis_params(risk_free_rate, annualization_factor)

    return await market_data_service.get_risk_analysis(
        asset_identifier=asset,
        risk_free_rate=valid_rf,
        annualization_factor=valid_af,
        refresh=refresh or False
    )


# ==============================================================================
# Step 7: Correlation & Rolling Correlation Endpoints
# ==============================================================================

@router.get(
    "/market/correlation",
    response_model=CorrelationMatrixResponse,
    summary="Get Multi-Asset Pearson Correlation Matrix",
    tags=["Correlation & Portfolio Risk"]
)
async def get_market_correlation(
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Calculates pairwise symmetric Pearson correlation matrix across multi-asset returns
    (NVIDIA, Bitcoin, Gold) strictly from Step 3 cleaned historical data.
    Aligns observations on matching dates without forward-filling.
    """
    return await market_data_service.get_correlation_matrix(refresh=refresh or False)


@router.get(
    "/market/correlation/rolling",
    response_model=RollingCorrelationResponse,
    summary="Get Rolling Pearson Correlation Time Series",
    tags=["Correlation & Portfolio Risk"]
)
async def get_market_rolling_correlation(
    window: Optional[str] = Query(
        "20",
        description="Rolling correlation lookback window in observations (positive integer >= 2, default 20)"
    ),
    asset1: Optional[str] = Query(
        None,
        description="Optional first asset identifier (e.g. 'nvidia', 'bitcoin', 'gold')"
    ),
    asset2: Optional[str] = Query(
        None,
        description="Optional second asset identifier (e.g. 'nvidia', 'bitcoin', 'gold')"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Calculates pairwise rolling Pearson correlation time series across asset combinations
    strictly from Step 3 cleaned historical data.

    Query Parameters:
    - window: Positive integer >= 2 (default: 20)
    - asset1: Optional asset filter
    - asset2: Optional asset filter
    - refresh: Optional boolean to force fresh fetch and calculation
    """
    valid_window = validate_rolling_window(window)

    return await market_data_service.get_rolling_correlation(
        window=valid_window,
        asset1=asset1,
        asset2=asset2,
        refresh=refresh or False
    )


# ------------------------------------------------------------------------------
# Step 8: Strategy-Agnostic Backtesting Engine Endpoint
# ------------------------------------------------------------------------------
@router.post(
    "/market/{asset}/backtest",
    response_model=BacktestResponse,
    summary="Run Strategy-Agnostic Portfolio Backtest",
    tags=["Backtesting Engine"]
)
async def run_market_backtest(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    request: BacktestRequest = ...,
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Executes a strategy-agnostic backtesting simulation on cleaned historical market data
    for NVIDIA, Bitcoin, or Gold.

    Next-Observation Execution Assumption:
    Signals generated using information available at observation t execute at observation t+1
    at Close price P_{t+1}, strictly preventing look-ahead bias.
    """
    return await market_data_service.run_backtest(
        asset_identifier=asset,
        request=request,
        refresh=refresh or False
    )


# ------------------------------------------------------------------------------
# Step 9: Quantitative Trading Strategies Endpoints
# ------------------------------------------------------------------------------
@router.post(
    "/market/{asset}/strategy/signals",
    response_model=StrategySignalsResponse,
    summary="Generate Trading Strategy Signals",
    tags=["Trading Strategies"]
)
async def get_market_strategy_signals(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    request: StrategySignalsRequest = ...,
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Generates timestamped trading signals (BUY, SELL, HOLD) for a requested strategy
    (sma_crossover, ema_trend, momentum, mean_reversion) on cleaned historical market data.
    """
    return await market_data_service.get_strategy_signals(
        asset_identifier=asset,
        strategy=request.strategy,
        parameters=request.parameters,
        refresh=refresh or False
    )


@router.post(
    "/market/{asset}/strategy/backtest",
    response_model=StrategyBacktestResponse,
    summary="Backtest a Trading Strategy",
    tags=["Trading Strategies"]
)
async def run_market_strategy_backtest(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    request: StrategyBacktestRequest = ...,
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Generates strategy signals and executes them causally through the Step 8
    strategy-agnostic backtesting engine with Next-Observation Execution.
    """
    return await market_data_service.run_strategy_backtest(
        asset_identifier=asset,
        request=request,
        refresh=refresh or False
    )


@router.post(
    "/market/{asset}/strategy/compare",
    response_model=StrategyComparisonResponse,
    summary="Compare Trading Strategies",
    tags=["Strategy Comparison"]
)
async def compare_market_strategies(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    request: StrategyComparisonRequest = ...,
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Executes a side-by-side factual comparison across quantitative strategies under identical
    market data, capital, fee, and causal execution conditions.
    """
    return await market_data_service.compare_strategies(
        asset_identifier=asset,
        request=request,
        refresh=refresh or False
    )


@router.post(
    "/market/{asset}/strategy/robustness",
    response_model=RobustnessAnalysisResponse,
    summary="Parameter Sensitivity & Robustness Analysis",
    tags=["Strategy Robustness"]
)
async def analyze_strategy_robustness(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    request: RobustnessAnalysisRequest = ...,
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Performs controlled parameter sensitivity testing over a bounded discrete grid
    for a designated strategy, reporting factual performance across every tested configuration.
    """
    return await market_data_service.analyze_robustness(
        asset_identifier=asset,
        request=request,
        refresh=refresh or False
    )


# ==============================================================================
# Step 11: Market Regime Analysis Endpoints
# ==============================================================================

@router.get(
    "/market/{asset}/regimes",
    response_model=MarketRegimesResponse,
    summary="Market Regime Analysis",
    tags=["Market Regimes"]
)
async def get_market_regimes(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    trend_period: Optional[Any] = Query(
        50,
        description="SMA lookback window for trend state classification (>= 1, default: 50)"
    ),
    volatility_window: Optional[Any] = Query(
        20,
        description="Rolling window for volatility state classification (>= 2, default: 20)"
    ),
    volatility_threshold: Optional[Any] = Query(
        None,
        description="Optional fixed volatility threshold percentage. If omitted, causal expanding median is used."
    ),
    trend_threshold: Optional[Any] = Query(
        0.0,
        description="Optional neutral band fraction for sideways trend (>= 0.0, default: 0.0)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Classifies historical market data into deterministic trend, volatility,
    and combined market regimes with strict causal zero look-ahead protection.
    """
    tp, vw, vt, tt = validate_regime_params(
        trend_val=trend_period,
        vol_val=volatility_window,
        vol_thresh_val=volatility_threshold,
        trend_thresh_val=trend_threshold,
    )

    return await market_data_service.get_market_regimes(
        asset_identifier=asset,
        trend_period=tp,
        volatility_window=vw,
        volatility_threshold=vt,
        trend_threshold=tt,
        refresh=refresh or False
    )


@router.get(
    "/market/{asset}/regimes/summary",
    response_model=MarketRegimesSummaryResponse,
    summary="Market Regimes Distribution Summary",
    tags=["Market Regimes"]
)
async def get_market_regimes_summary(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    trend_period: Optional[Any] = Query(
        50,
        description="SMA lookback window for trend state classification (>= 1, default: 50)"
    ),
    volatility_window: Optional[Any] = Query(
        20,
        description="Rolling window for volatility state classification (>= 2, default: 20)"
    ),
    volatility_threshold: Optional[Any] = Query(
        None,
        description="Optional fixed volatility threshold percentage. If omitted, causal expanding median is used."
    ),
    trend_threshold: Optional[Any] = Query(
        0.0,
        description="Optional neutral band fraction for sideways trend (>= 0.0, default: 0.0)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Returns an executive distribution summary of detected market regimes including
    observation counts, percentage distribution, and historical start/end dates.
    """
    tp, vw, vt, tt = validate_regime_params(
        trend_val=trend_period,
        vol_val=volatility_window,
        vol_thresh_val=volatility_threshold,
        trend_thresh_val=trend_threshold,
    )

    return await market_data_service.get_market_regimes_summary(
        asset_identifier=asset,
        trend_period=tp,
        volatility_window=vw,
        volatility_threshold=vt,
        trend_threshold=tt,
        refresh=refresh or False
    )


@router.get(
    "/market/{asset}/regimes/performance",
    response_model=StrategyRegimePerformanceResponse,
    summary="Strategy Performance by Market Regime",
    tags=["Market Regimes"]
)
async def get_strategy_regime_performance(
    asset: str = Path(..., description="Target asset identifier: 'nvidia', 'bitcoin', or 'gold'"),
    trend_period: Optional[Any] = Query(
        50,
        description="SMA lookback window for trend state classification (>= 1, default: 50)"
    ),
    volatility_window: Optional[Any] = Query(
        20,
        description="Rolling window for volatility state classification (>= 2, default: 20)"
    ),
    volatility_threshold: Optional[Any] = Query(
        None,
        description="Optional fixed volatility threshold percentage. If omitted, causal expanding median is used."
    ),
    trend_threshold: Optional[Any] = Query(
        0.0,
        description="Optional neutral band fraction for sideways trend (>= 0.0, default: 0.0)"
    ),
    refresh: Optional[bool] = Query(
        False,
        description="Bypass local cache and force fresh data calculation"
    )
):
    """
    Factual attribution of strategy performance and maximum drawdown across detected market regimes.
    Reuses Step 8 BacktestingEngine and Step 9 strategy dispatcher with zero ranking/scoring.
    """
    tp, vw, vt, tt = validate_regime_params(
        trend_val=trend_period,
        vol_val=volatility_window,
        vol_thresh_val=volatility_threshold,
        trend_thresh_val=trend_threshold,
    )

    return await market_data_service.get_strategy_performance_by_regime(
        asset_identifier=asset,
        trend_period=tp,
        volatility_window=vw,
        volatility_threshold=vt,
        trend_threshold=tt,
        refresh=refresh or False
    )



