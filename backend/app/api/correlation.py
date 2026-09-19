"""
FastAPI Correlation & Cross-Asset Endpoints for QUANTLAB.
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.correlation import (
    CorrelationMatrixResponse,
    PairCorrelationResponse,
    RollingCorrelationResponse,
    AssetComparisonResponse,
)
from backend.app.schemas.market import ErrorResponse
from backend.app.services.correlation_service import correlation_service

router = APIRouter(prefix="/correlation", tags=["Asset Comparison & Correlation"])


def _validate_date_string(date_str: Optional[str], param_name: str) -> None:
    """Validates that a date string follows YYYY-MM-DD."""
    if date_str is not None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {param_name} format '{date_str}'. Expected valid calendar date in YYYY-MM-DD format."
            )


def _validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates start_date <= end_date."""
    _validate_date_string(start_date, "start_date")
    _validate_date_string(end_date, "end_date")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date range: start_date '{start_date}' cannot be greater than end_date '{end_date}'."
        )


@router.get(
    "/matrix",
    response_model=CorrelationMatrixResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid dates or parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get cross-asset Pearson correlation matrix",
    description="Computes symmetric correlation matrix and pairwise observation counts across selected assets."
)
def get_correlation_matrix(
    assets: Optional[str] = Query(None, description="Comma-separated asset list (e.g. Gold,Bitcoin,NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    
    asset_list: Optional[List[str]] = None
    if assets:
        asset_list = [a.strip() for a in assets.split(",") if a.strip()]
        
    try:
        return correlation_service.get_correlation_matrix(
            assets=asset_list,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/pair",
    response_model=PairCorrelationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date range"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get pairwise Pearson correlation between two assets",
    description="Calculates correlation coefficient, overlapping observation count, and active date bounds for two assets."
)
def get_pair_correlation(
    asset_a: str = Query(..., description="First asset identifier (e.g. Gold)"),
    asset_b: str = Query(..., description="Second asset identifier (e.g. Bitcoin)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return correlation_service.get_pairwise_correlation(
            asset_a=asset_a,
            asset_b=asset_b,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/rolling",
    response_model=RollingCorrelationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get rolling correlation time-series between two assets",
    description="Calculates rolling Pearson correlation over a configurable lookback window on aligned calendar dates."
)
def get_rolling_correlation(
    asset_a: str = Query(..., description="First asset identifier (e.g. Gold)"),
    asset_b: str = Query(..., description="Second asset identifier (e.g. NVIDIA)"),
    window: int = Query(30, ge=2, le=500, description="Rolling window size in days"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return correlation_service.get_rolling_correlation(
            asset_a=asset_a,
            asset_b=asset_b,
            window=window,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/comparison",
    response_model=AssetComparisonResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get comparative risk/return performance statistics across assets",
    description="Compares cumulative returns, CAGR, volatility, Sharpe ratio, and Max Drawdown across selected assets."
)
def get_asset_comparison(
    assets: Optional[str] = Query(None, description="Comma-separated asset list (e.g. Gold,Bitcoin,NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    
    asset_list: Optional[List[str]] = None
    if assets:
        asset_list = [a.strip() for a in assets.split(",") if a.strip()]
        
    try:
        return correlation_service.get_asset_comparison(
            assets=asset_list,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
