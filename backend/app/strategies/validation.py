"""
Strategy Parameter Validation Module.
Ensures mathematical integrity and valid bounds for trading strategy parameters.
"""
from typing import Union
from backend.app.quant.validation import validate_positive_integer
from backend.app.strategies.enums import StrategyType


def validate_sma_parameters(fast_period: int, slow_period: int) -> None:
    """Validates fast and slow SMA lookback periods."""
    validate_positive_integer(fast_period, name="fast_period", min_value=2)
    validate_positive_integer(slow_period, name="slow_period", min_value=2)
    if fast_period >= slow_period:
        raise ValueError(
            f"fast_period ({fast_period}) must be strictly less than slow_period ({slow_period})."
        )


def validate_ema_parameters(short_period: int, long_period: int) -> None:
    """Validates short and long EMA lookback periods."""
    validate_positive_integer(short_period, name="short_period", min_value=2)
    validate_positive_integer(long_period, name="long_period", min_value=2)
    if short_period >= long_period:
        raise ValueError(
            f"short_period ({short_period}) must be strictly less than long_period ({long_period})."
        )


def validate_momentum_parameters(lookback: int) -> None:
    """Validates momentum lookback window."""
    validate_positive_integer(lookback, name="lookback", min_value=1)


def validate_mean_reversion_parameters(window: int, threshold: Union[int, float]) -> None:
    """Validates mean reversion moving average window and deviation threshold."""
    validate_positive_integer(window, name="window", min_value=2)
    if not isinstance(threshold, (int, float)) or threshold <= 0:
        raise ValueError(f"threshold must be a positive number greater than 0, got {threshold}.")


def validate_strategy_name(strategy_name: str) -> StrategyType:
    """
    Validates and normalizes strategy identifier string.
    Accepts underscores or hyphens, case-insensitively.
    """
    if not strategy_name or not isinstance(strategy_name, str):
        raise ValueError("Strategy name must be a non-empty string.")
    
    normalized = strategy_name.strip().lower().replace("-", "_")
    for strat in StrategyType:
        if normalized == strat.value:
            return strat
            
    valid_names = [s.value for s in StrategyType]
    raise ValueError(
        f"Unknown strategy '{strategy_name}'. Supported strategies: {', '.join(valid_names)}."
    )
