"""
FastAPI Market Regime Endpoints for QUANTLAB (Phase 8).
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path

from backend.app.schemas.regimes import RegimeResponse
from backend.app.schemas.market import ErrorResponse
from backend.app.regimes.enums import ThresholdMode
from backend.app.services.regime_service import regime_service

router = APIRouter(prefix="/regimes", tags=["Market Regime Analysis"])


@router.get(
    "/{asset}",
    response_model=RegimeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameter, lookback window, or date range"},
        404: {"model": ErrorResponse, "description": "Asset not found"},
    },
    summary="Get historical market regime analysis for an asset",
    description="Calculates deterministic trend (BULL/BEAR) and volatility state (HIGH/LOW) regimes, with descriptive statistics and transitions.",
)
def get_market_regimes(
    asset: str = Path(..., description="Asset identifier (e.g., Gold, Bitcoin, NVIDIA)", examples=["Gold"]),
    trend_window: int = Query(50, ge=2, description="Moving average lookback window for trend"),
    volatility_window: int = Query(20, ge=2, description="Rolling lookback window for volatility"),
    threshold_mode: ThresholdMode = Query(
        ThresholdMode.HISTORICAL_DESCRIPTIVE,
        description="Volatility thresholding mode (historical_descriptive or expanding_threshold)",
    ),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)", examples=["2020-01-01"]),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)", examples=["2024-12-31"]),
):
    try:
        if start_date and end_date and start_date > end_date:
            raise ValueError(f"start_date '{start_date}' cannot be after end_date '{end_date}'.")

        return regime_service.get_regime_analysis(
            asset=asset,
            trend_window=trend_window,
            volatility_window=volatility_window,
            threshold_mode=threshold_mode.value,
            start_date=start_date,
            end_date=end_date,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
