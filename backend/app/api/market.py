"""
FastAPI Market Data Endpoints for QUANTLAB.
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime

from backend.app.schemas.market import (
    AssetListResponse,
    AssetMetadataResponse,
    MultiAssetDateRangeResponse,
    HistoricalDataResponse,
    MultiAssetHistoricalDataResponse,
    ErrorResponse,
)
from backend.app.services.market_service import market_service

router = APIRouter(prefix="/market", tags=["Market Data"])


def _validate_date_string(date_str: Optional[str], param_name: str) -> None:
    """Validates that a date string follows YYYY-MM-DD and is a real calendar date."""
    if date_str is not None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {param_name} format '{date_str}'. Expected valid calendar date in YYYY-MM-DD format."
            )


def _validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates that start_date <= end_date."""
    _validate_date_string(start_date, "start_date")
    _validate_date_string(end_date, "end_date")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date range: start_date '{start_date}' cannot be greater than end_date '{end_date}'."
        )


@router.get(
    "/assets",
    response_model=AssetListResponse,
    summary="List available assets",
    description="Returns all market assets supported by QUANTLAB with category metadata."
)
def list_assets():
    assets = market_service.get_available_assets()
    return AssetListResponse(assets=assets)


@router.get(
    "/date-range",
    response_model=MultiAssetDateRangeResponse,
    summary="Get date ranges for all assets",
    description="Returns the earliest and latest available historical dates and record counts for all assets."
)
def get_date_ranges():
    try:
        ranges = market_service.get_all_date_ranges()
        return MultiAssetDateRangeResponse(assets=ranges)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/assets/{asset}",
    response_model=AssetMetadataResponse,
    responses={404: {"model": ErrorResponse, "description": "Asset not found"}},
    summary="Get metadata for a specific asset",
    description="Returns date range, record count, and time-series frequency for the requested asset."
)
def get_asset_metadata(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)")
):
    try:
        meta = market_service.get_asset_metadata(asset)
        return AssetMetadataResponse(**meta)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{asset}' not found. Supported assets are: Gold, Bitcoin, NVIDIA."
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    response_model=MultiAssetHistoricalDataResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid date range"}},
    summary="Get multi-asset historical OHLCV data",
    description="Returns filtered time-series data across multiple assets from the unified market dataset."
)
def get_multi_asset_history(
    assets: Optional[str] = Query(None, description="Comma-separated asset list (e.g. Gold,Bitcoin,NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    limit: int = Query(2000, ge=1, le=20000, description="Maximum number of records to return (max 20000)")
):
    _validate_date_range(start_date, end_date)
    
    asset_list: Optional[List[str]] = None
    if assets:
        asset_list = [a.strip() for a in assets.split(",") if a.strip()]

    try:
        data, count = market_service.get_multi_asset_history(
            assets=asset_list,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        return MultiAssetHistoricalDataResponse(
            frequency="daily",
            count=len(data),
            data=data
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/history",
    response_model=HistoricalDataResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date range"},
        404: {"model": ErrorResponse, "description": "Asset not found"}
    },
    summary="Get historical OHLCV data for an asset",
    description="Returns daily historical open, high, low, close, and volume records for the specified asset."
)
def get_asset_history(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records to return (max 10000)")
):
    _validate_date_range(start_date, end_date)

    try:
        data, count = market_service.get_asset_history(
            asset=asset,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        canonical = market_service.normalize_asset_name(asset) or asset
        return HistoricalDataResponse(
            asset=canonical,
            frequency="daily",
            count=len(data),
            data=data
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Asset '{asset}' not found. Supported assets are: Gold, Bitcoin, NVIDIA."
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
