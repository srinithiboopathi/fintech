"""
FastAPI Backtesting and Portfolio Simulation Endpoints for QUANTLAB (Phase 7).
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException

from backend.app.schemas.backtesting import (
    BacktestRequest,
    BacktestResponse,
    StrategyInfoListResponse,
)
from backend.app.schemas.market import ErrorResponse
from backend.app.services.backtesting_service import backtest_service

router = APIRouter(prefix="/backtesting", tags=["Backtesting Engine"])


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


@router.post(
    "/run",
    response_model=BacktestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid simulation parameters or date ranges"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Run full portfolio backtest simulation",
    description="Simulates realistic trade execution, transaction fees, cash accounting, daily mark-to-market, and Buy-and-Hold benchmark comparison.",
)
def run_backtest(request: BacktestRequest):
    _validate_date_range(request.start_date, request.end_date)
    try:
        return backtest_service.run_backtest(
            asset=request.asset,
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            position_size=request.position_size,
            transaction_cost=request.transaction_cost,
            risk_free_rate=request.risk_free_rate,
            strategy_parameters=request.strategy_parameters,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/strategies",
    response_model=StrategyInfoListResponse,
    summary="Get available strategies and default parameters",
    description="Returns metadata catalog of all strategies available for backtest execution.",
)
def get_strategies():
    strategies_data = backtest_service.get_supported_strategies()
    return {"strategies": strategies_data}
