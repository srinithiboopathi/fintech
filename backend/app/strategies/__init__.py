"""
Strategies Package for QUANTLAB.
Provides pure, deterministic quantitative trading strategy signal engines.
"""
from backend.app.strategies.enums import SignalType, StrategyType
from backend.app.strategies.validation import (
    validate_sma_parameters,
    validate_ema_parameters,
    validate_momentum_parameters,
    validate_mean_reversion_parameters,
    validate_strategy_name,
)
from backend.app.strategies.sma_crossover import calculate_sma_crossover_signals
from backend.app.strategies.ema_trend import calculate_ema_trend_signals
from backend.app.strategies.momentum import calculate_momentum_signals
from backend.app.strategies.mean_reversion import calculate_mean_reversion_signals

__all__ = [
    "SignalType",
    "StrategyType",
    "validate_sma_parameters",
    "validate_ema_parameters",
    "validate_momentum_parameters",
    "validate_mean_reversion_parameters",
    "validate_strategy_name",
    "calculate_sma_crossover_signals",
    "calculate_ema_trend_signals",
    "calculate_momentum_signals",
    "calculate_mean_reversion_signals",
]
