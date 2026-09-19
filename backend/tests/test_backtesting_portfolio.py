"""
Unit Tests for Portfolio Accounting, Equity Curves, and Daily Mark-to-Market (Phase 7).
"""
import pytest
import numpy as np
import pandas as pd

from backend.app.backtesting.portfolio import PortfolioTracker
from backend.app.backtesting.performance import calculate_portfolio_performance


class TestPortfolioAccounting:
    """Test cash ledger, mark-to-market valuations, and equity curve tracking."""

    def test_daily_equity_curve_and_drawdown(self):
        tracker = PortfolioTracker(
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.0,
            asset="Gold",
            strategy="sma_crossover",
        )

        # Sequence of 5 days:
        # Day 1: flat, close=100 -> port=100k, ret=0, cum_ret=0, dd=0
        tracker.process_morning_execution("2024-01-01", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-01", close_price=100.0)
        tracker.evaluate_signal_for_next_session("BUY")

        # Day 2: enters at open=100 (1,000 units), close=120 -> port=120k, ret=20%, cum_ret=20%, dd=0
        tracker.process_morning_execution("2024-01-02", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-02", close_price=120.0)
        tracker.evaluate_signal_for_next_session("HOLD")

        # Day 3: holds, close=90 -> port=90k, ret = (90k/120k)-1 = -25%, cum_ret=-10%, peak=120k, dd = (90k-120k)/120k = -25%
        tracker.process_morning_execution("2024-01-03", open_price=120.0)
        tracker.process_evening_mark_to_market("2024-01-03", close_price=90.0)
        tracker.evaluate_signal_for_next_session("HOLD")

        # Day 4: holds, close=150 -> port=150k, peak=150k, dd=0
        tracker.process_morning_execution("2024-01-04", open_price=90.0)
        tracker.process_evening_mark_to_market("2024-01-04", close_price=150.0)
        tracker.evaluate_signal_for_next_session("SELL")

        # Day 5: exits at open=150 (cash becomes 150k), close=150 -> port=150k
        tracker.process_morning_execution("2024-01-05", open_price=150.0)
        tracker.process_evening_mark_to_market("2024-01-05", close_price=150.0)
        tracker.evaluate_signal_for_next_session("HOLD")

        curve = tracker.equity_curve
        assert len(curve) == 5

        # Day 1 checks
        assert curve[0].portfolio_value == 100000.0
        assert curve[0].daily_return == 0.0
        assert curve[0].cumulative_return == 0.0
        assert curve[0].drawdown == 0.0

        # Day 2 checks
        assert curve[1].portfolio_value == 120000.0
        assert pytest.approx(curve[1].daily_return, rel=1e-5) == 0.20
        assert pytest.approx(curve[1].cumulative_return, rel=1e-5) == 0.20
        assert curve[1].drawdown == 0.0

        # Day 3 checks
        assert curve[2].portfolio_value == 90000.0
        assert pytest.approx(curve[2].daily_return, rel=1e-5) == -0.25
        assert pytest.approx(curve[2].cumulative_return, rel=1e-5) == -0.10
        assert pytest.approx(curve[2].drawdown, rel=1e-5) == -0.25

        # Day 4 checks
        assert curve[3].portfolio_value == 150000.0
        assert curve[3].drawdown == 0.0

        # Day 5 checks
        assert curve[4].portfolio_value == 150000.0
        assert curve[4].cash == 150000.0
        assert curve[4].position_quantity == 0.0

    def test_open_position_at_end_of_backtest(self):
        tracker = PortfolioTracker(
            initial_capital=50000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="NVIDIA",
            strategy="momentum",
        )

        # Day 1: Signal = BUY
        tracker.process_morning_execution("2024-01-01", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-01", close_price=100.0)
        tracker.evaluate_signal_for_next_session("BUY")

        # Day 2: Enters at open=100
        tracker.process_morning_execution("2024-01-02", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-02", close_price=110.0)
        tracker.evaluate_signal_for_next_session("HOLD")

        # Backtest terminates here without a SELL signal
        open_pos = tracker.get_open_position_summary(final_close=110.0)

        assert open_pos is not None
        assert open_pos["asset"] == "NVIDIA"
        assert open_pos["entry_price"] == 100.0
        assert open_pos["current_price"] == 110.0
        assert open_pos["unrealized_pnl"] > 0
        assert len(tracker.trades) == 0  # No completed trades fabricated

    def test_performance_analytics_calculation(self):
        tracker = PortfolioTracker(
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="Gold",
            strategy="sma_crossover",
        )

        # Run minimal 3-day profitable trade
        tracker.process_morning_execution("2024-01-01", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-01", close_price=100.0)
        tracker.evaluate_signal_for_next_session("BUY")

        tracker.process_morning_execution("2024-01-02", open_price=100.0)
        tracker.process_evening_mark_to_market("2024-01-02", close_price=110.0)
        tracker.evaluate_signal_for_next_session("SELL")

        tracker.process_morning_execution("2024-01-03", open_price=110.0)
        tracker.process_evening_mark_to_market("2024-01-03", close_price=110.0)
        tracker.evaluate_signal_for_next_session("HOLD")

        perf = calculate_portfolio_performance(
            equity_curve=tracker.equity_curve,
            trades=tracker.trades,
            initial_capital=100000.0,
            asset="Gold",
            risk_free_rate=0.0,
        )

        assert perf["initial_capital"] == 100000.0
        assert perf["final_portfolio_value"] > 100000.0
        assert perf["total_return"] > 0.0
        assert perf["number_of_trades"] == 1
        assert perf["winning_trades"] == 1
        assert perf["losing_trades"] == 0
        assert perf["win_rate"] == 1.0
        assert perf["net_profit"] > 0.0
        assert perf["gross_profit"] > 0.0
        assert perf["gross_loss"] == 0.0
