"""
Backtesting Enums and Status Definitions for QUANTLAB.
"""
from enum import Enum


class PositionStatus(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"


class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(str, Enum):
    COMPLETED = "COMPLETED"
    OPEN = "OPEN"
