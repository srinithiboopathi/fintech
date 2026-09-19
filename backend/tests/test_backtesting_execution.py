"""
Unit Tests for Trade Execution Mechanics and Portfolio State Transitions (Phase 7).
Validates next-day open fills, transaction fee accounting, position sizing, and trade lifecycles.
"""
import pytest
import pandas as pd
import numpy as np

from backend.app.backtesting.enums import PositionStatus, OrderType
from backend.app.backtesting.models import Position
from backend.app.backtesting.execution import execute_buy, execute_sell
from backend.app.backtesting.portfolio import PortfolioTracker


class TestTradeExecutionMechanics:
    """Test execution functions and timing rules."""

    def test_buy_execution_math_and_fees(self):
        # Initial cash $100,000, Open price $100, Position Size 1.0 (100%), Fee 0.001 (0.1%)
        cash = 100000.0
        open_price = 100.0
        pos_size = 1.0
        fee_pct = 0.001

        # Effective unit cost = 100 * 1.001 = 100.1
        # Quantity = 100,000 / 100.1 = 999.000999
        # Notional = 999.000999 * 100 = 99900.0999
        # Fee = 99900.0999 * 0.001 = 99.9001
        # Total spent = 100,000.0
        pos, cash_spent = execute_buy(
            available_cash=cash,
            open_price=open_price,
            position_size=pos_size,
            transaction_cost_pct=fee_pct,
            entry_date="2024-01-02",
        )

        assert pos.is_long()
        assert pytest.approx(pos.quantity, rel=1e-5) == 999.000999
        assert pytest.approx(pos.entry_price, rel=1e-5) == 100.0
        assert pos.entry_date == "2024-01-02"
        assert pytest.approx(cash_spent, rel=1e-5) == 100000.0
        assert pytest.approx(pos.entry_cost, rel=1e-5) == 99.9001
        assert pytest.approx(pos.entry_notional, rel=1e-5) == 99900.0999

    def test_position_sizing_half_allocation(self):
        # 50% position sizing on $100,000 -> deploys $50,000
        cash = 100000.0
        open_price = 200.0
        pos_size = 0.5
        fee_pct = 0.002  # 0.2%

        pos, cash_spent = execute_buy(
            available_cash=cash,
            open_price=open_price,
            position_size=pos_size,
            transaction_cost_pct=fee_pct,
            entry_date="2024-01-02",
        )

        assert pytest.approx(cash_spent, rel=1e-5) == 50000.0
        remaining_cash = cash - cash_spent
        assert pytest.approx(remaining_cash, rel=1e-5) == 50000.0

    def test_sell_execution_math_and_pnl(self):
        # Enter at $100, Exit at $150
        pos = Position(
            status=PositionStatus.LONG,
            quantity=100.0,
            entry_price=100.0,
            entry_date="2024-01-02",
            entry_cost=10.0,      # 100 * 100 * 0.001
            entry_notional=10000.0,
        )

        exit_open = 150.0
        fee_pct = 0.001  # 0.1%

        # Exit notional = 100 * 150 = 15,000
        # Exit fee = 15,000 * 0.001 = 15
        # Net cash received = 15,000 - 15 = 14,985
        # Gross PnL = 15,000 - 10,000 = 5,000
        # Net PnL = 5,000 - (10 + 15) = 4,975
        # Return Pct = 4,975 / (10,000 + 10) = 4,975 / 10,010 = 0.497002997
        trade, cash_rec, flat_pos = execute_sell(
            position=pos,
            open_price=exit_open,
            transaction_cost_pct=fee_pct,
            exit_date="2024-02-01",
            asset="Gold",
            strategy="sma_crossover",
            trade_id=1,
        )

        assert flat_pos.is_flat()
        assert pytest.approx(cash_rec, rel=1e-5) == 14985.0
        assert trade.trade_id == 1
        assert trade.asset == "Gold"
        assert trade.entry_date == "2024-01-02"
        assert trade.exit_date == "2024-02-01"
        assert pytest.approx(trade.gross_pnl, rel=1e-5) == 5000.0
        assert pytest.approx(trade.net_pnl, rel=1e-5) == 4975.0
        assert pytest.approx(trade.return_pct, rel=1e-5) == (4975.0 / 10010.0)
        assert trade.holding_period_days == 30

    def test_next_day_open_execution_lifecycle(self):
        """
        Verify that a BUY signal emitted on day t close ONLY executes on day t+1 open,
        and a SELL signal on day t+1 close ONLY executes on day t+2 open.
        """
        tracker = PortfolioTracker(
            initial_capital=10000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="Gold",
            strategy="sma_crossover",
        )

        # Day 1: Signal = BUY at close
        # Morning Day 1: No pending orders yet
        tracker.process_morning_execution(date="2024-01-01", open_price=100.0)
        assert tracker.position.is_flat()
        assert tracker.cash == 10000.0

        # Evening Day 1: Mark to market
        tracker.process_evening_mark_to_market(date="2024-01-01", close_price=105.0)
        assert tracker.equity_curve[0].portfolio_value == 10000.0

        # Evening Day 1: Signal is BUY -> schedules pending order for Day 2 morning
        tracker.evaluate_signal_for_next_session(signal="BUY")
        assert tracker.pending_order == OrderType.BUY

        # Day 2: Morning execution at Day 2 OPEN ($110)
        tracker.process_morning_execution(date="2024-01-02", open_price=110.0)
        assert tracker.position.is_long()
        assert tracker.position.entry_price == 110.0
        assert tracker.position.entry_date == "2024-01-02"
        assert tracker.pending_order is None

        # Evening Day 2: Close price $120 -> position value increases
        tracker.process_evening_mark_to_market(date="2024-01-02", close_price=120.0)
        assert tracker.equity_curve[1].position_value > 0
        assert tracker.equity_curve[1].portfolio_value > 10000.0

        # Evening Day 2: Signal = SELL -> schedules pending SELL for Day 3 morning
        tracker.evaluate_signal_for_next_session(signal="SELL")
        assert tracker.pending_order == OrderType.SELL

        # Day 3: Morning execution at Day 3 OPEN ($125) -> closes position
        tracker.process_morning_execution(date="2024-01-03", open_price=125.0)
        assert tracker.position.is_flat()
        assert len(tracker.trades) == 1
        assert tracker.trades[0].entry_price == 110.0
        assert tracker.trades[0].exit_price == 125.0
        assert tracker.trades[0].net_pnl > 0

    def test_no_duplicate_buys_while_long(self):
        tracker = PortfolioTracker(
            initial_capital=10000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="NVIDIA",
            strategy="momentum",
        )

        # Day 1: BUY signal
        tracker.process_morning_execution("2024-01-01", open_price=50.0)
        tracker.process_evening_mark_to_market("2024-01-01", close_price=50.0)
        tracker.evaluate_signal_for_next_session("BUY")

        # Day 2: Opens position
        tracker.process_morning_execution("2024-01-02", open_price=52.0)
        assert tracker.position.is_long()
        initial_qty = tracker.position.quantity

        tracker.process_evening_mark_to_market("2024-01-02", close_price=55.0)
        # Even if another BUY signal arrives, pending order must NOT be created
        tracker.evaluate_signal_for_next_session("BUY")
        assert tracker.pending_order is None

        # Day 3: Morning
        tracker.process_morning_execution("2024-01-03", open_price=56.0)
        assert tracker.position.quantity == initial_qty

    def test_sell_while_flat_does_nothing(self):
        tracker = PortfolioTracker(
            initial_capital=10000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="Bitcoin",
            strategy="mean_reversion",
        )

        # Day 1: SELL signal while FLAT
        tracker.process_morning_execution("2024-01-01", open_price=40000.0)
        tracker.process_evening_mark_to_market("2024-01-01", close_price=39000.0)
        tracker.evaluate_signal_for_next_session("SELL")
        assert tracker.pending_order is None

        tracker.process_morning_execution("2024-01-02", open_price=38000.0)
        assert tracker.position.is_flat()
        assert len(tracker.trades) == 0
        assert tracker.cash == 10000.0
