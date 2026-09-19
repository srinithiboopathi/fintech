"""
Deterministic unit tests for QuantLab Backtesting Engine, Execution, Portfolio, and Benchmark.
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.strategies.base import BaseStrategy
from backend.app.backtesting.transaction_costs import TransactionCostModel
from backend.app.backtesting.position_sizing import FullCapitalSizer
from backend.app.backtesting.execution import ExecutionHandler, Trade
from backend.app.backtesting.portfolio import PortfolioTracker
from backend.app.backtesting.engine import BacktestEngine, run_backtest


class MockSignalStrategy(BaseStrategy):
    """Simple strategy returning a pre-defined signal series for testing."""
    def __init__(self, signals: list):
        super().__init__(name="MockSignalStrategy")
        self.signal_list = signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(self.signal_list[:len(df)], index=df.index)


class TestTransactionCosts:
    def test_cost_calculation(self):
        model = TransactionCostModel(cost_pct=0.001)
        # $10,000 trade -> $10 cost
        assert model.calculate_cost(10000.0) == pytest.approx(10.0)
        assert model.calculate_cost(-5000.0) == pytest.approx(5.0)

    def test_invalid_cost_pct_raises(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            TransactionCostModel(cost_pct=-0.01)


class TestPositionSizing:
    def test_full_capital_sizer(self):
        sizer = FullCapitalSizer(fraction=1.0)
        assert sizer.calculate_allocation(current_equity=100000.0, available_cash=50000.0, signal=1, price=100.0) == 100000.0
        assert sizer.calculate_allocation(current_equity=100000.0, available_cash=50000.0, signal=0, price=100.0) == 0.0

    def test_invalid_fraction_raises(self):
        with pytest.raises(ValueError, match="Allocation fraction"):
            FullCapitalSizer(fraction=0.0)
        with pytest.raises(ValueError, match="Allocation fraction"):
            FullCapitalSizer(fraction=1.5)


class TestBacktestEngineDeterministic:
    def test_complete_trade_lifecycle_and_accounting(self):
        # 6 trading days: Flat (days 0, 1), Long (days 2, 3), Flat (days 4, 5)
        dates = pd.date_range("2024-01-01", periods=6, freq="D")
        prices = [100.0, 100.0, 100.0, 120.0, 90.0, 90.0]
        df = pd.DataFrame({"Close": prices}, index=dates)

        # Signal array: Buy at day 2, hold day 3, sell at day 4
        signals = [0, 0, 1, 1, 0, 0]
        mock_strategy = MockSignalStrategy(signals)

        engine = BacktestEngine(initial_capital=100000.0, transaction_cost=0.001)
        result = engine.run(df, mock_strategy)

        # Verify trade count: 1 BUY and 1 SELL
        assert result.number_of_trades == 2
        buy_trade = result.trades[0]
        sell_trade = result.trades[1]

        assert buy_trade.action == "BUY"
        assert buy_trade.price == 100.0
        assert buy_trade.position == 1
        # Trade cost = 100000 / 1.001 * 0.001 = ~99.90
        assert buy_trade.transaction_cost == pytest.approx(99.90, rel=1e-3)

        assert sell_trade.action == "SELL"
        assert sell_trade.price == 90.0
        assert sell_trade.position == 0

        # Total transaction costs paid
        assert result.transaction_costs_paid == pytest.approx(buy_trade.transaction_cost + sell_trade.transaction_cost)

        # Portfolio value tracking
        history = result.portfolio_history
        assert len(history) == 6
        # On day 3, price reached 120.0 -> peak equity
        assert history["equity"].iloc[3] == pytest.approx(buy_trade.quantity * 120.0, rel=1e-3)
        # Final value reflects sold position into cash minus fees
        assert result.final_portfolio_value == pytest.approx(history["equity"].iloc[-1])
        assert result.total_return == pytest.approx((result.final_portfolio_value - 100000.0) / 100000.0)

        # Maximum drawdown must be negative (from peak at day 3 to trough at day 4)
        assert result.maximum_drawdown < 0.0

    def test_buy_and_hold_benchmark(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = [100.0, 110.0, 120.0]
        df = pd.DataFrame({"Close": prices}, index=dates)

        engine = BacktestEngine(initial_capital=100000.0, transaction_cost=0.001)
        bench = engine.run_buy_and_hold(df)

        assert bench.total_return > 0.19  # ~20% gain minus entry fee
        assert bench.maximum_drawdown == pytest.approx(0.0)  # Monotonically rising -> 0 drawdown

    def test_empty_dataframe_handling(self):
        engine = BacktestEngine(initial_capital=50000.0)
        empty_df = pd.DataFrame(columns=["Close"])
        mock_strategy = MockSignalStrategy([])

        result = engine.run(empty_df, mock_strategy)
        assert result.number_of_trades == 0
        assert result.final_portfolio_value == 50000.0
        assert result.total_return == 0.0
        assert result.maximum_drawdown == 0.0
