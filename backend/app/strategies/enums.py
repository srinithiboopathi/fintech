"""
Strategy Enums and Signal Definitions for QUANTLAB.
"""
from enum import Enum


class SignalType(str, Enum):
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"
    EMA_TREND = "ema_trend"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
