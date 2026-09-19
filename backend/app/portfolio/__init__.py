"""
Portfolio Analytics Package for QUANTLAB.
"""
from backend.app.portfolio.service import portfolio_service, PortfolioService
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
from backend.app.portfolio.optimization import (
    portfolio_optimization_service,
    PortfolioOptimizationService,
    validate_optimization_parameters,
)

__all__ = [
    "portfolio_service",
    "PortfolioService",
    "portfolio_optimization_service",
    "PortfolioOptimizationService",
    "validate_optimization_parameters",
    "validate_portfolio_weights",
    "validate_portfolio_parameters",
    "calculate_portfolio_daily_returns",
    "calculate_portfolio_cumulative_returns",
    "calculate_portfolio_value_series",
    "calculate_portfolio_performance_summary",
    "calculate_performance_contributions",
    "calculate_portfolio_risk_contributions",
]
