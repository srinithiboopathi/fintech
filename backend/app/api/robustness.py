"""
FastAPI Robustness Lab Endpoints for QUANTLAB (Phase 8).
"""
from fastapi import APIRouter, HTTPException

from backend.app.schemas.robustness import RobustnessRequest, RobustnessResponse
from backend.app.schemas.backtesting import StrategyInfoListResponse
from backend.app.schemas.market import ErrorResponse
from backend.app.services.robustness_service import robustness_service
from backend.app.services.backtesting_service import backtest_service

router = APIRouter(prefix="/robustness", tags=["Strategy Robustness Lab"])


@router.post(
    "/run",
    response_model=RobustnessResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameter grid, limit exceeded, or bad parameters"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Run multi-parameter strategy robustness sensitivity sweep",
    description="Executes backtests across parameter grids, transaction costs, and backtest windows. Reports objective sensitivity metrics without ranking.",
)
def run_robustness(request: RobustnessRequest):
    try:
        # Convert periods to dict format if present
        period_dicts = None
        if request.periods:
            period_dicts = [{"start_date": p.start_date, "end_date": p.end_date} for p in request.periods]

        return robustness_service.run_robustness(
            asset=request.asset,
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date,
            periods=period_dicts,
            initial_capital=request.initial_capital,
            position_size=request.position_size,
            transaction_costs=request.transaction_costs,
            risk_free_rate=request.risk_free_rate,
            strategy_parameter_grid=request.strategy_parameter_grid,
            max_configurations=request.max_configurations or 100,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/strategies",
    response_model=StrategyInfoListResponse,
    summary="Get strategies available for robustness exploration",
    description="Returns metadata catalog of all strategies and their configurable hyperparameter ranges.",
)
def get_robustness_strategies():
    strategies_data = backtest_service.get_supported_strategies()
    return {"strategies": strategies_data}
