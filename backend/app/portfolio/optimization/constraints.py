"""
Portfolio Optimization Constraints and Validation Module.
"""
from typing import List, Dict, Optional
from fastapi import HTTPException, status

from backend.app.services.market_service import market_service


def validate_optimization_parameters(
    assets: List[str],
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    random_portfolios: int = 5000,
    frontier_points: int = 50,
    risk_free_rate: float = 0.02,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_weights: Optional[Dict[str, float]] = None,
) -> List[str]:
    """
    Validates input parameters and constraints for multi-asset portfolio optimization.
    
    Returns:
        List of canonical asset names.
    """
    if not assets or len(assets) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Portfolio optimization requires at least 2 distinct assets.",
        )

    # Normalize asset names
    canonical_assets: List[str] = []
    for raw_asset in assets:
        canonical = market_service.normalize_asset_name(raw_asset)
        if not canonical:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown asset identifier: '{raw_asset}'. Supported assets: Gold, Bitcoin, NVIDIA.",
            )
        if canonical not in canonical_assets:
            canonical_assets.append(canonical)

    if len(canonical_assets) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least 2 unique assets must be selected for optimization.",
        )

    n_assets = len(canonical_assets)

    # Validate weight bounds
    if min_weight < 0.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Minimum weight cannot be negative ({min_weight}). Long-only optimization required.",
        )
    if max_weight > 1.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum weight cannot exceed 1.0 ({max_weight}).",
        )
    if min_weight > max_weight:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Minimum weight ({min_weight}) cannot exceed maximum weight ({max_weight}).",
        )

    # Check constraint feasibility on simplex
    # If n * min_weight > 1.0, no valid allocation exists
    if (n_assets * min_weight) > 1.0 + 1e-4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Infeasible allocation constraints: With {n_assets} assets, sum of minimum weights "
                f"({n_assets} * {min_weight * 100:.1f}% = {n_assets * min_weight * 100:.1f}%) exceeds 100%."
            ),
        )

    # If n * max_weight < 1.0, weights cannot sum to 100%
    if (n_assets * max_weight) < 1.0 - 1e-4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Infeasible allocation constraints: With {n_assets} assets, sum of maximum weights "
                f"({n_assets} * {max_weight * 100:.1f}% = {n_assets * max_weight * 100:.1f}%) cannot reach 100%."
            ),
        )

    # Validate random portfolios count
    if random_portfolios < 100 or random_portfolios > 10000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Random portfolio count must be between 100 and 10,000. Received: {random_portfolios}",
        )

    # Validate frontier points
    if frontier_points < 10 or frontier_points > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Frontier points count must be between 10 and 100. Received: {frontier_points}",
        )

    # Validate risk-free rate
    if risk_free_rate < 0.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Risk-free rate cannot be negative. Received: {risk_free_rate}",
        )

    # Validate date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Start date ({start_date}) cannot be after end date ({end_date}).",
        )

    # Validate user weights if provided
    if user_weights:
        total_uw = 0.0
        for asset, w in user_weights.items():
            canon = market_service.normalize_asset_name(asset)
            if not canon or canon not in canonical_assets:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"User weight asset '{asset}' is not in the optimization universe.",
                )
            if w < 0.0 or w > 1.0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"User weight for '{canon}' must be between 0.0 and 1.0 ({w}).",
                )
            total_uw += float(w)

        if abs(total_uw - 1.0) > 1e-4:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User portfolio weights must sum to 100%. Current sum: {total_uw * 100:.2f}%.",
            )

    return canonical_assets
