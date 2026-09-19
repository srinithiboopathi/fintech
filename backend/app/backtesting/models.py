"""
Internal Data Models and State Classes for Portfolio Simulation.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from backend.app.backtesting.enums import PositionStatus


@dataclass
class Position:
    """Represents the current open asset position in the portfolio."""
    status: PositionStatus = PositionStatus.FLAT
    quantity: float = 0.0
    entry_price: float = 0.0
    entry_date: str = ""
    entry_cost: float = 0.0
    entry_notional: float = 0.0

    def is_long(self) -> bool:
        return self.status == PositionStatus.LONG and self.quantity > 0.0

    def is_flat(self) -> bool:
        return self.status == PositionStatus.FLAT or self.quantity <= 0.0


@dataclass
class TradeRecordInternal:
    """Represents a completed round-trip trade."""
    trade_id: int
    asset: str
    strategy: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_notional: float
    exit_notional: float
    entry_cost: float
    exit_cost: float
    gross_pnl: float
    net_pnl: float
    return_pct: float
    holding_period_days: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "asset": self.asset,
            "strategy": self.strategy,
            "entry_date": self.entry_date,
            "exit_date": self.exit_date,
            "entry_price": round(self.entry_price, 4),
            "exit_price": round(self.exit_price, 4),
            "quantity": round(self.quantity, 6),
            "entry_notional": round(self.entry_notional, 2),
            "exit_notional": round(self.exit_notional, 2),
            "entry_cost": round(self.entry_cost, 2),
            "exit_cost": round(self.exit_cost, 2),
            "gross_pnl": round(self.gross_pnl, 2),
            "net_pnl": round(self.net_pnl, 2),
            "return_pct": round(self.return_pct, 6),
            "holding_period_days": self.holding_period_days,
        }


@dataclass
class DailyPortfolioState:
    """Daily snapshot of portfolio equity, cash, and asset allocation."""
    date: str
    cash: float
    position_quantity: float
    position_value: float
    portfolio_value: float
    daily_return: Optional[float] = None
    cumulative_return: Optional[float] = None
    drawdown: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "cash": round(self.cash, 2),
            "position_quantity": round(self.position_quantity, 6),
            "position_value": round(self.position_value, 2),
            "portfolio_value": round(self.portfolio_value, 2),
            "daily_return": round(self.daily_return, 6) if self.daily_return is not None else None,
            "cumulative_return": round(self.cumulative_return, 6) if self.cumulative_return is not None else None,
            "drawdown": round(self.drawdown, 6) if self.drawdown is not None else None,
        }
