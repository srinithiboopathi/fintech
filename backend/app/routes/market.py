from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, Path

from app.config import settings
from app.models.schemas import (
    HealthResponse,
    AssetsListResponse,
    HistoricalDataResponse,
    LatestMarketDataResponse
)
from app.services.market_data import market_data_service
from app.services.cache_manager import cache_manager

router = APIRouter()

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
