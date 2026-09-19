"""
Portfolio Tracker and State Machine for QUANTLAB Backtesting.
"""
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from backend.app.backtesting.enums import PositionStatus, OrderType
from backend.app.backtesting.models import Position, TradeRecordInternal, DailyPortfolioState
from backend.app.backtesting.execution import execute_buy, execute_sell


class PortfolioTracker:
    """Manages the lifecycle of cash, open positions, daily equity valuation, and trade history."""

    def __init__(
        self,
        initial_capital: float,
        position_size: float,
        transaction_cost: float,
        asset: str,
        strategy: str,
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_size = position_size
        self.transaction_cost = transaction_cost
        self.asset = asset
        self.strategy = strategy

        self.position = Position(status=PositionStatus.FLAT)
        self.trades: List[TradeRecordInternal] = []
        self.equity_curve: List[DailyPortfolioState] = []
        self.trade_counter = 1
        self.running_peak = -np.inf
        self.pending_order: Optional[OrderType] = None

    def process_morning_execution(self, date: str, open_price: float) -> None:
        """Executes any pending orders at the market session OPEN."""
        if self.pending_order == OrderType.BUY:
            if self.position.is_flat():
                self.position, cash_spent = execute_buy(
                    available_cash=self.cash,
                    open_price=open_price,
                    position_size=self.position_size,
                    transaction_cost_pct=self.transaction_cost,
                    entry_date=date,
                )
                self.cash -= cash_spent
            self.pending_order = None

        elif self.pending_order == OrderType.SELL:
            if self.position.is_long():
                trade, cash_received, self.position = execute_sell(
                    position=self.position,
                    open_price=open_price,
                    transaction_cost_pct=self.transaction_cost,
                    exit_date=date,
                    asset=self.asset,
                    strategy=self.strategy,
                    trade_id=self.trade_counter,
                )
                self.cash += cash_received
                self.trades.append(trade)
                self.trade_counter += 1
            self.pending_order = None

    def process_evening_mark_to_market(self, date: str, close_price: float) -> None:
        """Calculates end-of-day equity value, daily return, cumulative return, and drawdown."""
        pos_val = (self.position.quantity * close_price) if self.position.is_long() else 0.0
        port_val = self.cash + pos_val

        self.running_peak = max(self.running_peak, port_val)
        dd = (port_val / self.running_peak) - 1.0 if self.running_peak > 0 else 0.0
        if dd > 0.0:
            dd = 0.0

        if self.equity_curve:
            prev_port_val = self.equity_curve[-1].portfolio_value
            daily_ret = (port_val / prev_port_val) - 1.0 if prev_port_val > 0 else 0.0
        else:
            daily_ret = 0.0

        cum_ret = (port_val / self.initial_capital) - 1.0

        self.equity_curve.append(
            DailyPortfolioState(
                date=date,
                cash=self.cash,
                position_quantity=self.position.quantity,
                position_value=pos_val,
                portfolio_value=port_val,
                daily_return=daily_ret,
                cumulative_return=cum_ret,
                drawdown=dd,
            )
        )

    def evaluate_signal_for_next_session(self, signal: str) -> None:
        """Schedules trade actions for the next available trading session OPEN."""
        if signal == "BUY" and self.position.is_flat():
            self.pending_order = OrderType.BUY
        elif signal == "SELL" and self.position.is_long():
            self.pending_order = OrderType.SELL
        else:
            self.pending_order = None

    def get_open_position_summary(self, final_close: float) -> Optional[Dict[str, Any]]:
        """Returns details of any position that remains open at backtest termination."""
        if not self.position.is_long():
            return None

        current_notional = self.position.quantity * final_close
        unrealized_pnl = current_notional - self.position.entry_notional
        total_invested = self.position.entry_notional + self.position.entry_cost
        unrealized_ret = (unrealized_pnl / total_invested) if total_invested > 0 else 0.0

        return {
            "asset": self.asset,
            "quantity": round(self.position.quantity, 6),
            "entry_date": self.position.entry_date,
            "entry_price": round(self.position.entry_price, 4),
            "current_price": round(final_close, 4),
            "entry_notional": round(self.position.entry_notional, 2),
            "current_notional": round(current_notional, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_return_pct": round(unrealized_ret, 6),
        }
