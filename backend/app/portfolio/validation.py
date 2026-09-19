"""
Validation Module for Portfolio Analytics.
"""
from typing import Dict, List, Tuple
from fastapi import HTTPException, status
from backend.app.services.market_service import market_service


def validate_portfolio_weights(
    weights: Dict[str, float],
    tolerance: float = 1e-4,
) -> Dict[str, float]:
    """
    Validates and normalizes asset weights.
    
    Rules:
    - Each asset must be a known asset (Gold, Bitcoin, NVIDIA).
    - Each weight must be between 0.0 and 1.0 (non-negative).
    - The sum of weights must equal 1.0 within tolerance.
    - At least one asset must have a strictly positive weight.
    """
    if not weights:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Portfolio must contain at least one asset with non-zero weight.",
        )

    normalized_weights: Dict[str, float] = {}
    for raw_asset, weight in weights.items():
        canonical = market_service.normalize_asset_name(raw_asset)
        if not canonical:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown asset identifier: '{raw_asset}'. Supported assets: Gold, Bitcoin, NVIDIA.",
            )

        if weight is None or weight < 0.0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Weight for asset '{canonical}' cannot be negative ({weight}).",
            )
        if weight > 1.0 + tolerance:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Weight for asset '{canonical}' cannot exceed 100% ({weight * 100:.2f}%).",
            )

        # Merge weights if duplicate alias provided
        normalized_weights[canonical] = normalized_weights.get(canonical, 0.0) + float(weight)

    # Filter out 0 weight assets
    active_weights = {k: v for k, v in normalized_weights.items() if v > 1e-6}
    if not active_weights:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Portfolio must have at least one asset with positive allocation.",
        )

    total_weight = sum(active_weights.values())
    if abs(total_weight - 1.0) > tolerance:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Portfolio weights must sum to 100%. Current sum: {total_weight * 100:.2f}%.",
        )

    return active_weights


def validate_portfolio_parameters(
    initial_capital: float,
    risk_free_rate: float,
    start_date: str = None,
    end_date: str = None,
) -> None:
    """
    Validates general portfolio simulation parameters.
    """
    if initial_capital <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Initial capital must be strictly positive. Received: {initial_capital}",
        )
    if risk_free_rate < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Risk-free rate cannot be negative. Received: {risk_free_rate}",
        )
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Start date ({start_date}) cannot be after end date ({end_date}).",
        )
