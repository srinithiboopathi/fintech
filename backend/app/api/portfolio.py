"""
Portfolio Analytics API Router for QUANTLAB.
"""
from fastapi import APIRouter, status
from backend.app.schemas.portfolio import (
    PortfolioAnalysisRequest,
    PortfolioAnalysisResponse,
)
from backend.app.portfolio.service import portfolio_service

router = APIRouter(prefix="/portfolio", tags=["Portfolio Analytics"])


@router.post(
    "/analyze",
    response_model=PortfolioAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Multi-Asset Portfolio Performance & Risk",
    description="Calculates aligned daily returns, cumulative growth, Sharpe ratio, drawdown, asset return contributions, and Euler covariance risk decomposition for a custom weighted portfolio.",
)
def analyze_portfolio(
    request: PortfolioAnalysisRequest,
) -> PortfolioAnalysisResponse:
    return portfolio_service.analyze_portfolio(request)
