"""
FastAPI Strategy Signal Endpoints for QUANTLAB (Phase 6).
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Path

from backend.app.schemas.strategy import StrategyResponse
from backend.app.schemas.market import ErrorResponse
from backend.app.services.strategy_service import strategy_service

router = APIRouter(prefix="/strategies", tags=["Strategy Engine"])


def _validate_date_string(date_str: Optional[str], param_name: str) -> None:
    """Validates that a date string follows YYYY-MM-DD format."""
    if date_str is not None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {param_name} format '{date_str}'. Expected valid calendar date in YYYY-MM-DD format.",
            )


def _validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates that start_date <= end_date."""
    _validate_date_string(start_date, "start_date")
    _validate_date_string(end_date, "end_date")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date range: start_date '{start_date}' cannot be greater than end_date '{end_date}'.",
        )


@router.get(
    "/{asset}/sma-crossover",
    response_model=StrategyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid dates or parameters (e.g. fast_period >= slow_period)"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get SMA Crossover trading signals",
    description="Generates deterministic crossing-event signals for Fast SMA crossing above/below Slow SMA.",
)
def get_sma_crossover(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    fast_period: int = Query(20, ge=2, le=1000, description="Fast SMA lookback window (days)"),
    slow_period: int = Query(50, ge=2, le=1000, description="Slow SMA lookback window (days)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return strategy_service.get_sma_crossover_signals(
            asset=asset,
            fast_period=fast_period,
            slow_period=slow_period,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{asset}/ema-trend",
    response_model=StrategyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid dates or parameters (e.g. short_period >= long_period)"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get EMA Trend trading signals",
    description="Generates deterministic crossing-event signals for Short EMA crossing above/below Long EMA.",
)
def get_ema_trend(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    short_period: int = Query(20, ge=2, le=1000, description="Short EMA lookback window (days)"),
    long_period: int = Query(50, ge=2, le=1000, description="Long EMA lookback window (days)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return strategy_service.get_ema_trend_signals(
            asset=asset,
            short_period=short_period,
            long_period=long_period,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{asset}/momentum",
    response_model=StrategyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid dates or parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get Momentum trading signals",
    description="Calculates rate-of-change momentum and generates zero-line crossing signals.",
)
def get_momentum(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    lookback: int = Query(20, ge=1, le=1000, description="Momentum lookback period (days)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return strategy_service.get_momentum_signals(
            asset=asset,
            lookback=lookback,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{asset}/mean-reversion",
    response_model=StrategyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid dates or parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get Mean Reversion trading signals",
    description="Calculates percentage deviation from rolling central moving average and generates threshold signals.",
)
def get_mean_reversion(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    window: int = Query(20, ge=2, le=1000, description="Moving average lookback window (days)"),
    threshold: float = Query(0.02, gt=0.0, le=1.0, description="Deviation threshold percentage (e.g. 0.02 for 2%)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return strategy_service.get_mean_reversion_signals(
            asset=asset,
            window=window,
            threshold=threshold,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{asset}/signals",
    response_model=StrategyResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid strategy, dates, or parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Unified strategy signal generation endpoint",
    description="Calculates signals for any supported strategy (sma_crossover, ema_trend, momentum, mean_reversion).",
)
def get_signals(
    asset: str = Path(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)"),
    strategy: str = Query(..., description="Strategy name: sma_crossover, ema_trend, momentum, mean_reversion"),
    fast_period: int = Query(20, ge=2, le=1000, description="Fast SMA lookback (for sma_crossover)"),
    slow_period: int = Query(50, ge=2, le=1000, description="Slow SMA lookback (for sma_crossover)"),
    short_period: int = Query(20, ge=2, le=1000, description="Short EMA lookback (for ema_trend)"),
    long_period: int = Query(50, ge=2, le=1000, description="Long EMA lookback (for ema_trend)"),
    lookback: int = Query(20, ge=1, le=1000, description="Momentum lookback (for momentum)"),
    window: int = Query(20, ge=2, le=1000, description="Moving average window (for mean_reversion)"),
    threshold: float = Query(0.02, gt=0.0, le=1.0, description="Deviation threshold (for mean_reversion)"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    _validate_date_range(start_date, end_date)
    try:
        return strategy_service.get_signals(
            asset=asset,
            strategy=strategy,
            fast_period=fast_period,
            slow_period=slow_period,
            short_period=short_period,
            long_period=long_period,
            lookback=lookback,
            window=window,
            threshold=threshold,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
