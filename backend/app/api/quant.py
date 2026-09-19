"""
FastAPI Quantitative Analysis Endpoints for QUANTLAB.
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path

from backend.app.schemas.quant import (
    IndicatorResponse,
    ReturnsResponse,
    VolatilityResponse,
    RiskMetricsResponse,
    RollingPerformanceResponse,
    AssetQuantSummaryResponse,
)
from backend.app.schemas.market import ErrorResponse
from backend.app.services.quant_service import quant_service

router = APIRouter(prefix="/quant", tags=["Quantitative Analysis"])


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
    "/{asset}/indicators",
    response_model=IndicatorResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date or parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get SMA and EMA technical indicators for an asset",
    description="Calculates configurable Simple Moving Average (SMA) and Exponential Moving Average (EMA) time-series."
)
def get_indicators(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    sma_period: int = Query(20, ge=1, le=1000, description="Simple Moving Average period in trading days"),
    ema_period: int = Query(20, ge=1, le=1000, description="Exponential Moving Average period in trading days"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_indicators(
            asset=asset,
            sma_period=sma_period,
            ema_period=ema_period,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/returns",
    response_model=ReturnsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date range"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get daily and cumulative returns for an asset",
    description="Calculates arithmetic daily percentage returns and compounded growth index series."
)
def get_returns(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_returns(
            asset=asset,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/volatility",
    response_model=VolatilityResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get rolling and annualized volatility for an asset",
    description="Calculates rolling historical sample standard deviation and scaled annualized volatility series."
)
def get_volatility(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    window: int = Query(20, ge=2, le=500, description="Rolling lookback window in days"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_volatility(
            asset=asset,
            window=window,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/risk-metrics",
    response_model=RiskMetricsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid date range"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get risk and return metrics (Volatility, Sharpe, Drawdown)",
    description="Calculates annualized volatility, Sharpe ratio (with configurable risk-free rate), and Maximum Drawdown."
)
def get_risk_metrics(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate (e.g. 0.02 for 2%)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_risk_metrics(
            asset=asset,
            start_date=start_date,
            end_date=end_date,
            risk_free_rate=risk_free_rate,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/rolling-performance",
    response_model=RollingPerformanceResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get rolling performance time-series",
    description="Computes multi-dimensional rolling returns, rolling volatility, rolling Sharpe, and drawdown curves."
)
def get_rolling_performance(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    window: int = Query(20, ge=2, le=500, description="Rolling lookback window in days"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_rolling_performance(
            asset=asset,
            window=window,
            start_date=start_date,
            end_date=end_date,
            risk_free_rate=risk_free_rate,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{asset}/summary",
    response_model=AssetQuantSummaryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get consolidated quantitative profile for an asset",
    description="Returns full quantitative summary including cumulative return, annualized volatility, Sharpe ratio, Max Drawdown, and return distribution statistics."
)
def get_asset_summary(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    risk_free_rate: float = Query(0.0, description="Annualized risk-free rate"),
):
    _validate_date_range(start_date, end_date)
    try:
        return quant_service.get_asset_summary(
            asset=asset,
            start_date=start_date,
            end_date=end_date,
            risk_free_rate=risk_free_rate,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e).strip("'"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
