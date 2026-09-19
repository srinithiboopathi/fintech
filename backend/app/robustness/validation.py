"""
Validation Module for Robustness Grid Sweeps and Limits.
"""
from typing import List, Optional, Dict, Any, Union
from backend.app.backtesting.validation import (
    validate_backtest_parameters,
    validate_backtest_dates,
)
from backend.app.strategies.validation import validate_strategy_name

MAX_CONFIGURATIONS = 100


def validate_robustness_inputs(
    asset: str,
    strategy: str,
    initial_capital: float,
    position_size: float,
    transaction_costs: Optional[List[float]],
    risk_free_rate: float = 0.0,
) -> List[float]:
    """Validates top-level portfolio simulation parameters for grid sweeps."""
    validate_strategy_name(strategy)
    validate_backtest_parameters(
        initial_capital=initial_capital,
        position_size=position_size,
        transaction_cost=0.0,
        risk_free_rate=risk_free_rate,
    )

    costs = transaction_costs if transaction_costs is not None and len(transaction_costs) > 0 else [0.001]
    for cost in costs:
        if not isinstance(cost, (int, float)) or cost < 0:
            raise ValueError(f"Transaction cost must be non-negative, got {cost}.")

    return costs


def validate_grid_size(count: int, max_limit: int = MAX_CONFIGURATIONS) -> None:
    """Enforces safety limits to prevent runaway parameter grid combinatorial explosion."""
    if count == 0:
        raise ValueError("Parameter grid produced 0 valid configurations. Check your parameter boundaries.")
    if count > max_limit:
        raise ValueError(
            f"Requested parameter grid generated {count} configurations, exceeding the maximum safety limit of {max_limit}. "
            f"Please reduce the number of parameter steps, transaction costs, or test periods."
        )
