"""
Validation Module for Backtest Configurations and Hyperparameters.
"""
from typing import Optional, Dict, Any, Union
from datetime import datetime

from backend.app.strategies.enums import StrategyType
from backend.app.strategies.validation import (
    validate_strategy_name,
    validate_sma_parameters,
    validate_ema_parameters,
    validate_momentum_parameters,
    validate_mean_reversion_parameters,
)


def validate_backtest_parameters(
    initial_capital: Union[int, float],
    position_size: Union[int, float],
    transaction_cost: Union[int, float],
    risk_free_rate: Union[int, float] = 0.0,
) -> None:
    """Validates financial portfolio constraints and simulation parameters."""
    if not isinstance(initial_capital, (int, float)) or initial_capital <= 0:
        raise ValueError(
            f"initial_capital must be a positive number greater than 0, got {initial_capital}."
        )

    if not isinstance(position_size, (int, float)) or position_size <= 0 or position_size > 1.0:
        raise ValueError(
            f"position_size must be a number strictly greater than 0 and less than or equal to 1.0 (e.g. 1.0 for 100%), got {position_size}."
        )

    if not isinstance(transaction_cost, (int, float)) or transaction_cost < 0:
        raise ValueError(
            f"transaction_cost must be a non-negative number (>= 0), got {transaction_cost}."
        )

    if not isinstance(risk_free_rate, (int, float)) or risk_free_rate < 0:
        raise ValueError(
            f"risk_free_rate must be a non-negative number (>= 0), got {risk_free_rate}."
        )


def validate_backtest_dates(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates ISO date format and chronological start <= end ordering."""
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid start_date format '{start_date}'. Expected YYYY-MM-DD.")
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid end_date format '{end_date}'. Expected YYYY-MM-DD.")

    if start_date and end_date and start_date > end_date:
        raise ValueError(f"start_date '{start_date}' cannot be greater than end_date '{end_date}'.")


def validate_strategy_config(strategy_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validates strategy identifier and extracts/validates strategy-specific parameters."""
    strat_type = validate_strategy_name(strategy_name)
    params = params or {}

    validated_params: Dict[str, Any] = {}

    if strat_type == StrategyType.SMA_CROSSOVER:
        fast_period = params.get("fast_period", 20)
        slow_period = params.get("slow_period", 50)
        validate_sma_parameters(fast_period, slow_period)
        validated_params["fast_period"] = fast_period
        validated_params["slow_period"] = slow_period

    elif strat_type == StrategyType.EMA_TREND:
        short_period = params.get("short_period", 20)
        long_period = params.get("long_period", 50)
        validate_ema_parameters(short_period, long_period)
        validated_params["short_period"] = short_period
        validated_params["long_period"] = long_period

    elif strat_type == StrategyType.MOMENTUM:
        lookback = params.get("lookback", 20)
        validate_momentum_parameters(lookback)
        validated_params["lookback"] = lookback

    elif strat_type == StrategyType.MEAN_REVERSION:
        window = params.get("window", 20)
        threshold = params.get("threshold", 0.02)
        validate_mean_reversion_parameters(window, threshold)
        validated_params["window"] = window
        validated_params["threshold"] = threshold

    return validated_params
