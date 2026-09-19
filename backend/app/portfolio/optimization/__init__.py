"""
Portfolio Optimization Package for QUANTLAB.
"""
from backend.app.portfolio.optimization.constraints import validate_optimization_parameters
from backend.app.portfolio.optimization.optimizer import (
    calculate_portfolio_stats,
    optimize_equal_weight,
    optimize_min_volatility,
    optimize_max_sharpe,
    optimize_for_target_return,
)
from backend.app.portfolio.optimization.frontier import (
    generate_efficient_frontier,
    generate_random_portfolios,
    get_max_feasible_expected_return,
)
from backend.app.portfolio.optimization.service import (
    portfolio_optimization_service,
    PortfolioOptimizationService,
)

__all__ = [
    "validate_optimization_parameters",
    "calculate_portfolio_stats",
    "optimize_equal_weight",
    "optimize_min_volatility",
    "optimize_max_sharpe",
    "optimize_for_target_return",
    "generate_efficient_frontier",
    "generate_random_portfolios",
    "get_max_feasible_expected_return",
    "portfolio_optimization_service",
    "PortfolioOptimizationService",
]
