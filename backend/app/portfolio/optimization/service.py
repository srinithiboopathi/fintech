"""
Portfolio Optimization Service Module.
"""
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from backend.app.services.market_service import market_service
from backend.app.correlation.alignment import align_asset_returns
from backend.app.portfolio.optimization.constraints import validate_optimization_parameters
from backend.app.portfolio.optimization.optimizer import (
    calculate_portfolio_stats,
    optimize_equal_weight,
    optimize_min_volatility,
    optimize_max_sharpe,
)
from backend.app.portfolio.optimization.frontier import (
    generate_efficient_frontier,
    generate_random_portfolios,
)
from backend.app.schemas.portfolio_optimization import (
    PortfolioOptimizationRequest,
    PortfolioOptimizationResponse,
    OptimalPortfolioPoint,
    OptimalPortfoliosContainer,
    EfficientFrontierPoint,
    RandomPortfolioPoint,
    PortfolioComparisonItem,
)


class PortfolioOptimizationService:
    """
    Orchestrates Markowitz portfolio optimization, Efficient Frontier construction,
    and random portfolio sampling across multi-asset market universes.
    """

    def optimize_portfolio(
        self, request: PortfolioOptimizationRequest
    ) -> PortfolioOptimizationResponse:
        # 1. Parameter and constraint validation
        canonical_assets = validate_optimization_parameters(
            assets=request.assets,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            random_portfolios=request.random_portfolios,
            frontier_points=request.frontier_points,
            risk_free_rate=request.risk_free_rate,
            start_date=request.start_date,
            end_date=request.end_date,
            user_weights=request.user_weights,
        )

        # 2. Fetch market datasets for active assets
        asset_dfs: Dict[str, pd.DataFrame] = {}
        for asset in canonical_assets:
            try:
                df = market_service._get_dataset(asset)
                asset_dfs[asset] = df
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not load market data for asset '{asset}': {str(e)}",
                )

        # 3. Synchronize daily returns via inner join on common trading dates
        aligned_returns_df = align_asset_returns(
            asset_dataframes=asset_dfs,
            start_date=request.start_date,
            end_date=request.end_date,
            how="inner",
        )

        if aligned_returns_df.empty or len(aligned_returns_df) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient overlapping trading days ({len(aligned_returns_df)}) for the selected assets "
                    f"and date range ({request.start_date or 'inception'} to {request.end_date or 'latest'}). "
                    f"Note: Bitcoin data is available for calendar year 2017."
                ),
            )

        dates = aligned_returns_df["date"].tolist()
        start_date = dates[0]
        end_date = dates[-1]
        n_obs = len(aligned_returns_df)

        # 4. Extract return matrix and compute annualized expected returns & covariance matrix
        ret_matrix = aligned_returns_df[canonical_assets]
        
        # Annualized expected return: mu = 252 * mean(daily_return)
        daily_mean = ret_matrix.mean().values
        annualized_returns = daily_mean * 252.0
        
        # Annualized covariance matrix: Sigma = 252 * Cov(daily_returns)
        daily_cov = ret_matrix.cov().values
        annualized_cov = daily_cov * 252.0

        # Build dictionary representations for response
        asset_exp_rets_dict = {
            canonical_assets[i]: float(annualized_returns[i])
            for i in range(len(canonical_assets))
        }

        cov_dict: Dict[str, Dict[str, float]] = {}
        for i, a1 in enumerate(canonical_assets):
            cov_dict[a1] = {}
            for j, a2 in enumerate(canonical_assets):
                cov_dict[a1][a2] = float(annualized_cov[i, j])

        # 5. Compute Equal Weight benchmark portfolio
        eq_res = optimize_equal_weight(
            asset_names=canonical_assets,
            expected_returns=annualized_returns,
            cov_matrix=annualized_cov,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            risk_free_rate=request.risk_free_rate,
        )
        equal_weight_point = OptimalPortfolioPoint(**eq_res)

        # 6. Compute Global Minimum Variance (GMV) portfolio
        min_vol_res = optimize_min_volatility(
            asset_names=canonical_assets,
            expected_returns=annualized_returns,
            cov_matrix=annualized_cov,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            risk_free_rate=request.risk_free_rate,
        )
        min_vol_point = OptimalPortfolioPoint(**min_vol_res)

        # 7. Compute Maximum Sharpe Ratio portfolio
        max_sharpe_res = optimize_max_sharpe(
            asset_names=canonical_assets,
            expected_returns=annualized_returns,
            cov_matrix=annualized_cov,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            risk_free_rate=request.risk_free_rate,
        )
        max_sharpe_point = OptimalPortfolioPoint(**max_sharpe_res)

        # 8. Compute User Portfolio if provided
        user_point: Optional[OptimalPortfolioPoint] = None
        if request.user_weights:
            user_w_vec = np.array(
                [
                    request.user_weights.get(asset, 0.0)
                    or request.user_weights.get(market_service.normalize_asset_name(asset), 0.0)
                    for asset in canonical_assets
                ],
                dtype=float,
            )
            # Normalize if tiny float discrepancy
            if np.sum(user_w_vec) > 0:
                user_w_vec = user_w_vec / np.sum(user_w_vec)
                u_ret, u_var, u_vol, u_sharpe = calculate_portfolio_stats(
                    user_w_vec, annualized_returns, annualized_cov, request.risk_free_rate
                )
                user_w_dict = {canonical_assets[i]: float(user_w_vec[i]) for i in range(len(canonical_assets))}
                user_point = OptimalPortfolioPoint(
                    portfolio_type="User Portfolio",
                    weights=user_w_dict,
                    expected_return=float(u_ret),
                    variance=float(u_var),
                    volatility=float(u_vol),
                    sharpe_ratio=float(u_sharpe),
                )

        optimal_portfolios = OptimalPortfoliosContainer(
            max_sharpe=max_sharpe_point,
            min_volatility=min_vol_point,
            equal_weight=equal_weight_point,
            user_portfolio=user_point,
        )

        # 9. Generate Efficient Frontier curve
        frontier_raw = generate_efficient_frontier(
            asset_names=canonical_assets,
            expected_returns=annualized_returns,
            cov_matrix=annualized_cov,
            gmv_return=min_vol_res["expected_return"],
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            frontier_points=request.frontier_points,
            risk_free_rate=request.risk_free_rate,
        )
        efficient_frontier = [EfficientFrontierPoint(**pt) for pt in frontier_raw]

        # 10. Generate Random Feasible Portfolios
        random_raw = generate_random_portfolios(
            asset_names=canonical_assets,
            expected_returns=annualized_returns,
            cov_matrix=annualized_cov,
            num_portfolios=request.random_portfolios,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            risk_free_rate=request.risk_free_rate,
            random_seed=request.random_seed,
        )
        random_portfolios = [RandomPortfolioPoint(**pt) for pt in random_raw]

        # 11. Compile unranked descriptive comparison list
        comparison: List[PortfolioComparisonItem] = [
            PortfolioComparisonItem(
                name="Maximum Sharpe",
                weights=max_sharpe_point.weights,
                expected_return=max_sharpe_point.expected_return,
                volatility=max_sharpe_point.volatility,
                sharpe_ratio=max_sharpe_point.sharpe_ratio,
            ),
            PortfolioComparisonItem(
                name="Minimum Volatility",
                weights=min_vol_point.weights,
                expected_return=min_vol_point.expected_return,
                volatility=min_vol_point.volatility,
                sharpe_ratio=min_vol_point.sharpe_ratio,
            ),
            PortfolioComparisonItem(
                name="Equal Weight",
                weights=equal_weight_point.weights,
                expected_return=equal_weight_point.expected_return,
                volatility=equal_weight_point.volatility,
                sharpe_ratio=equal_weight_point.sharpe_ratio,
            ),
        ]

        if user_point:
            comparison.append(
                PortfolioComparisonItem(
                    name="User Portfolio",
                    weights=user_point.weights,
                    expected_return=user_point.expected_return,
                    volatility=user_point.volatility,
                    sharpe_ratio=user_point.sharpe_ratio,
                )
            )

        return PortfolioOptimizationResponse(
            assets=canonical_assets,
            start_date=start_date,
            end_date=end_date,
            observations=n_obs,
            risk_free_rate=request.risk_free_rate,
            min_weight=request.min_weight,
            max_weight=request.max_weight,
            asset_expected_returns=asset_exp_rets_dict,
            covariance_matrix=cov_dict,
            optimal_portfolios=optimal_portfolios,
            efficient_frontier=efficient_frontier,
            random_portfolios=random_portfolios,
            comparison=comparison,
        )


portfolio_optimization_service = PortfolioOptimizationService()
