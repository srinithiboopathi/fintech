"""
QuantLab - Position Sizing Module

Determines capital allocation and target order quantities per signal.
Designed to be extensible for fixed-fraction, volatility-parity, and Kelly sizing.
"""

from abc import ABC, abstractmethod
from typing import Tuple


class BasePositionSizer(ABC):
    """
    Abstract base class for capital allocation and position sizing.
    """

    @abstractmethod
    def calculate_allocation(
        self,
        current_equity: float,
        available_cash: float,
        signal: int,
        price: float
    ) -> float:
        """
        Calculate target dollar allocation for the asset.

        Parameters
        ----------
        current_equity : float
            Total current portfolio value (cash + mark-to-market holdings).
        available_cash : float
            Liquid unallocated cash.
        signal : int
            Position signal (1 = Long, 0 = Flat).
        price : float
            Current asset price.

        Returns
        -------
        float
            Target capital in monetary units to allocate to the asset.
        """
        pass


class FullCapitalSizer(BasePositionSizer):
    """
    Allocates 100% of available capital when long, 0% when flat.

    Parameters
    ----------
    fraction : float, default 1.0
        Fraction of available capital to deploy (1.0 = 100%).
    """

    def __init__(self, fraction: float = 1.0):
        if not (0.0 < fraction <= 1.0):
            raise ValueError(f"Allocation fraction must be in (0.0, 1.0], received: {fraction}")
        self.fraction = float(fraction)

    def calculate_allocation(
        self,
        current_equity: float,
        available_cash: float,
        signal: int,
        price: float
    ) -> float:
        if signal <= 0 or price <= 0:
            return 0.0
        # When entering or holding long, allocate fraction of total equity
        return max(0.0, current_equity * self.fraction)
