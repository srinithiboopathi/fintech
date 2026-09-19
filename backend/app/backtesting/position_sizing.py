"""
QuantLab - Position Sizing Module

Determines how much capital should be allocated to a position.
"""

from abc import ABC, abstractmethod


class BasePositionSizer(ABC):

    @abstractmethod
    def calculate_allocation(
        self,
        current_equity: float,
        available_cash: float,
        signal: int,
        price: float,
    ) -> float:
        pass


class FullCapitalSizer(BasePositionSizer):

    def __init__(self, fraction: float = 1.0):
        if not (0.0 < fraction <= 1.0):
            raise ValueError(
                f"Allocation fraction must be in (0.0, 1.0], received: {fraction}"
            )

        self.fraction = float(fraction)

    def calculate_allocation(
        self,
        current_equity: float,
        available_cash: float,
        signal: int,
        price: float,
    ) -> float:

        if signal <= 0 or price <= 0:
            return 0.0

        allocation = min(current_equity, available_cash) * self.fraction

        return max(0.0, float(allocation))