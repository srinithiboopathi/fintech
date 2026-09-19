"""
Market Regime and Volatility State Enums for QUANTLAB.
"""
from enum import Enum


class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"


class VolatilityState(str, Enum):
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


class ThresholdMode(str, Enum):
    HISTORICAL_DESCRIPTIVE = "historical_descriptive"
    EXPANDING_THRESHOLD = "expanding_threshold"
