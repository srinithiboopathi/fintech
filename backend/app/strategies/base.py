"""
QuantLab - Base Trading Strategy Interface

Defines the abstract interface for all quantitative strategy models.
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstract base strategy interface.

    Strategies process historical market data and emit an actionable position signal:
    1 = Long (invested in asset)
    0 = Out of market (100% cash)

    Guarantees look-ahead protection by ensuring signals generated at bar t
    only influence trading decisions in period t + 1.
    """

    def __init__(self, name: str = "BaseStrategy"):
        self.name = name

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate execution-ready position signals for the given market dataset.

        Parameters
        ----------
        df : pd.DataFrame
            Market OHLCV DataFrame (must contain Close prices).

        Returns
        -------
        pd.Series
            Binary position series (1 = long, 0 = flat), shifted to avoid look-ahead bias.
        """
        pass
