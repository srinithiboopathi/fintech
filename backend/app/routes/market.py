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
)
from app.services.market_data import market_data_service
from app.services.cache_manager import cache_manager
from app.utils.exceptions import (
    InvalidIndicatorPeriodError,
    InvalidVolatilityPeriodError,
    InvalidRiskAnalysisParameterError,
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


