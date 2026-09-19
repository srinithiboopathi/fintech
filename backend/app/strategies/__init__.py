"""
QuantLab Strategy Module
"""

from .base import BaseStrategy
from .sma_crossover import SMACrossoverStrategy
from .ema_trend import EMATrendStrategy

__all__ = [
    "BaseStrategy",
    "SMACrossoverStrategy",
    "EMATrendStrategy",
]
