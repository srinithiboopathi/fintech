"""
Portfolio Analytics Service Module for QUANTLAB.
"""
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
import numpy as np
import pandas as pd

from backend.app.services.market_service import market_service
from backend.app.correlation.alignment import align_asset_returns
from backend.app.portfolio.validation import (
    validate_portfolio_weights,
    validate_portfolio_parameters,
)
from backend.app.portfolio.metrics import (
    calculate_portfolio_daily_returns,
    calculate_portfolio_cumulative_returns,
    calculate_portfolio_value_series,
    calculate_portfolio_performance_summary,
    calculate_performance_contributions,
)
from backend.app.portfolio.risk import calculate_portfolio_risk_contributions
from backend.app.schemas.portfolio import (
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
    PortfolioSummaryMetrics,
    PortfolioDataPoint,
    PortfolioComparisonPoint,
    AssetPerformanceContribution,
    AssetRiskContribution,
)


class PortfolioService:
    """
    Orchestrates multi-asset portfolio construction, date alignment,
    performance evaluation, risk decomposition, and comparative analysis.
    """

    def analyze_portfolio(self, request: PortfolioAnalysisRequest) -> PortfolioAnalysisResponse:
        # 1. Validate weights and simulation parameters
        active_weights = validate_portfolio_weights(request.weights)
        validate_portfolio_parameters(
            initial_capital=request.initial_capital,
            risk_free_rate=request.risk_free_rate,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        # 2. Fetch price datasets for all active assets
        asset_dfs: Dict[str, pd.DataFrame] = {}
        for asset in active_weights.keys():
            try:
                df = market_service._get_dataset(asset)
                asset_dfs[asset] = df
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not load market data for asset '{asset}': {str(e)}",
                )

        # 3. Synchronize daily returns across active assets on common dates
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

        # 4. Calculate portfolio daily returns, cumulative returns & value series
        port_daily_ret = calculate_portfolio_daily_returns(aligned_returns_df, active_weights)
        port_cum_ret = calculate_portfolio_cumulative_returns(port_daily_ret)
        port_value_series = calculate_portfolio_value_series(port_cum_ret, request.initial_capital)

        # 5. Compute summary performance metrics
        summary_dict = calculate_portfolio_performance_summary(
            portfolio_daily_returns=port_daily_ret,
            cumulative_returns=port_cum_ret,
            initial_capital=request.initial_capital,
            risk_free_rate=request.risk_free_rate,
        )
        drawdown_series = summary_dict.pop("drawdown_series")

        summary_metrics = PortfolioSummaryMetrics(
            initial_capital=summary_dict["initial_capital"],
            final_value=summary_dict["final_value"],
            total_return=summary_dict["total_return"],
            annualized_return=summary_dict["annualized_return"],
            annualized_volatility=summary_dict["annualized_volatility"],
            sharpe_ratio=summary_dict["sharpe_ratio"],
            maximum_drawdown=summary_dict["maximum_drawdown"],
            observations=summary_dict["observations"],
            start_date=start_date,
            end_date=end_date,
        )

        # 6. Compute performance contributions
        perf_contribs_raw = calculate_performance_contributions(aligned_returns_df, active_weights)
        performance_contributions = [
            AssetPerformanceContribution(**c) for c in perf_contribs_raw
        ]

        # 7. Compute Euler risk contributions
        risk_decomp = calculate_portfolio_risk_contributions(
            aligned_returns_df=aligned_returns_df,
            weights=active_weights,
            annualization_factor=252,
        )
        risk_contributions = [
            AssetRiskContribution(**r) for r in risk_decomp["contributions"]
        ]
        covariance_matrix = risk_decomp["covariance_matrix"]

        # 8. Build daily time-series data points
        data_points: List[PortfolioDataPoint] = []
        for i, d in enumerate(dates):
            data_points.append(
                PortfolioDataPoint(
                    date=d,
                    portfolio_return=float(port_daily_ret.iloc[i]),
                    cumulative_return=float(port_cum_ret.iloc[i]),
                    portfolio_value=round(float(port_value_series.iloc[i]), 2),
                    drawdown=float(drawdown_series.iloc[i]),
                )
            )

        # 9. Build Normalized Comparison Series (Base = 100.0)
        # Compute asset cumulative return series for normalized comparison
        asset_cum_series: Dict[str, pd.Series] = {}
        for asset in active_weights.keys():
            if asset in aligned_returns_df.columns:
                asset_cum_series[asset] = (1.0 + aligned_returns_df[asset]).cumprod() - 1.0

        comparison_points: List[PortfolioComparisonPoint] = []
        for i, d in enumerate(dates):
            port_base100 = float(100.0 * (1.0 + port_cum_ret.iloc[i]))
            assets_base100: Dict[str, float] = {}
            for asset, cum_s in asset_cum_series.items():
                assets_base100[asset] = float(100.0 * (1.0 + cum_s.iloc[i]))

            comparison_points.append(
                PortfolioComparisonPoint(
                    date=d,
                    portfolio=round(port_base100, 3),
                    assets={k: round(v, 3) for k, v in assets_base100.items()},
                )
            )

        return PortfolioAnalysisResponse(
            weights=active_weights,
            summary=summary_metrics,
            performance_contributions=performance_contributions,
            risk_contributions=risk_contributions,
            covariance_matrix=covariance_matrix,
            data=data_points,
            comparison=comparison_points,
        )


portfolio_service = PortfolioService()
