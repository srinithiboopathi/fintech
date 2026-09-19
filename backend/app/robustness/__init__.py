"""
Robustness Lab Package for QUANTLAB.
Provides hyperparameter sweeps, cost sensitivity analysis, and objective range summaries.
"""
from backend.app.robustness.models import BacktestConfig, RobustnessResult
from backend.app.robustness.validation import (
    MAX_CONFIGURATIONS,
    validate_robustness_inputs,
    validate_grid_size,
)
from backend.app.robustness.parameter_grid import (
    generate_strategy_parameter_combinations,
    build_backtest_configurations,
)
from backend.app.robustness.comparison import summarize_robustness_results
from backend.app.robustness.runner import RobustnessRunner, robustness_runner

__all__ = [
    "BacktestConfig",
    "RobustnessResult",
    "MAX_CONFIGURATIONS",
    "validate_robustness_inputs",
    "validate_grid_size",
    "generate_strategy_parameter_combinations",
    "build_backtest_configurations",
    "summarize_robustness_results",
    "RobustnessRunner",
    "robustness_runner",
]
