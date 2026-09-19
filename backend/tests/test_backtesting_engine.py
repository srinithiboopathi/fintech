"""
Integration and End-to-End Tests for Backtest Engine (Phase 7).
Validates multi-asset execution, deterministic simulation, and look-ahead bias guards.
"""
import pytest
import pandas as pd
import numpy as np

from backend.app.backtesting.engine import backtest_engine
from backend.app.services.market_service import market_service
from backend.app.strategies.sma_crossover import calculate_sma_crossover_signals
from backend.app.backtesting.portfolio import PortfolioTracker


class TestBacktestEngineEndToEnd:
    """Test full backtest runs across assets and strategies."""

    def test_sma_crossover_gold(self):
        res = backtest_engine.run(
            asset="Gold",
            strategy="sma_crossover",
            start_date="2023-01-01",
            end_date="2024-12-31",
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            strategy_parameters={"fast_period": 20, "slow_period": 50},
        )

        assert res["backtest"]["asset"] == "Gold"
        assert res["strategy"]["name"] == "sma_crossover"
        assert res["performance"]["initial_capital"] == 100000.0
        assert len(res["equity_curve"]) > 0
        assert "benchmark" in res
        assert "comparison" in res

    def test_ema_trend_bitcoin(self):
        res = backtest_engine.run(
            asset="Bitcoin",
            strategy="ema_trend",
            initial_capital=50000.0,
            position_size=0.8,
            transaction_cost=0.001,
            strategy_parameters={"short_period": 10, "long_period": 30},
        )

        assert res["backtest"]["asset"] == "Bitcoin"
        assert res["strategy"]["name"] == "ema_trend"
        assert res["performance"]["initial_capital"] == 50000.0
        assert len(res["equity_curve"]) == 365

    def test_momentum_nvidia(self):
        res = backtest_engine.run(
            asset="NVIDIA",
            strategy="momentum",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            strategy_parameters={"lookback": 20},
        )

        assert res["backtest"]["asset"] == "NVIDIA"
        assert res["strategy"]["name"] == "momentum"
        assert len(res["equity_curve"]) > 200

    def test_mean_reversion_gold(self):
        res = backtest_engine.run(
            asset="Gold",
            strategy="mean_reversion",
            start_date="2024-01-01",
            end_date="2024-12-31",
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            strategy_parameters={"window": 20, "threshold": 0.02},
        )

        assert res["backtest"]["asset"] == "Gold"
        assert res["strategy"]["name"] == "mean_reversion"

    def test_deterministic_repeated_execution(self):
        run1 = backtest_engine.run(
            asset="Gold",
            strategy="sma_crossover",
            start_date="2023-01-01",
            end_date="2024-12-31",
            initial_capital=100000.0,
        )

        run2 = backtest_engine.run(
            asset="Gold",
            strategy="sma_crossover",
            start_date="2023-01-01",
            end_date="2024-12-31",
            initial_capital=100000.0,
        )

        assert run1["performance"]["final_portfolio_value"] == run2["performance"]["final_portfolio_value"]
        assert run1["performance"]["total_return"] == run2["performance"]["total_return"]
        assert len(run1["trades"]) == len(run2["trades"])
        assert len(run1["equity_curve"]) == len(run2["equity_curve"])

    def test_validation_errors(self):
        # Invalid asset
        with pytest.raises(KeyError, match="not recognized"):
            backtest_engine.run(asset="NonExistentAsset", strategy="sma_crossover")

        # Invalid strategy
        with pytest.raises(ValueError, match="Unknown strategy"):
            backtest_engine.run(asset="Gold", strategy="fake_strategy")

        # Invalid capital
        with pytest.raises(ValueError, match="initial_capital"):
            backtest_engine.run(asset="Gold", strategy="sma_crossover", initial_capital=-1000)

        # Invalid position size
        with pytest.raises(ValueError, match="position_size"):
            backtest_engine.run(asset="Gold", strategy="sma_crossover", position_size=1.5)

        # Invalid dates (start > end)
        with pytest.raises(ValueError, match="cannot be greater than"):
            backtest_engine.run(
                asset="Gold",
                strategy="sma_crossover",
                start_date="2024-12-31",
                end_date="2024-01-01",
            )


class TestBacktestLookAheadBiasPrevention:
    """
    CRITICAL LOOK-AHEAD TEST:
    Verifies that all strategy signals, order execution decisions, trade fills,
    and portfolio equity values at time <= T are 100% independent of future price perturbations (> T).
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.df = market_service._get_dataset("Gold").sort_values("date").reset_index(drop=True)

    def test_backtest_simulation_lookahead_independence(self):
        # Cutoff index T in historical dataset
        T = 250
        cutoff_date = str(self.df["date"].iloc[T])

        # Run unperturbed simulation up to cutoff date
        res_orig = backtest_engine.run(
            asset="Gold",
            strategy="sma_crossover",
            start_date=str(self.df["date"].iloc[0]),
            end_date=cutoff_date,
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            strategy_parameters={"fast_period": 20, "slow_period": 50},
        )

        # Perturb future data (> T) in a separate simulation pipeline
        df_perturbed = self.df.copy()
        df_perturbed.loc[T + 1:, "open"] = df_perturbed.loc[T + 1:, "open"] * 100.0 + 50000.0
        df_perturbed.loc[T + 1:, "high"] = df_perturbed.loc[T + 1:, "high"] * 100.0 + 60000.0
        df_perturbed.loc[T + 1:, "low"] = 0.01
        df_perturbed.loc[T + 1:, "close"] = df_perturbed.loc[T + 1:, "close"] * 100.0 + 50000.0

        # Calculate signals on perturbed data
        sig_perturbed = calculate_sma_crossover_signals(
            df_perturbed["close"],
            fast_period=20,
            slow_period=50,
        )
        df_perturbed["signal"] = sig_perturbed["signal"]

        # Run portfolio tracker on perturbed dataframe up to T
        tracker_perturbed = PortfolioTracker(
            initial_capital=100000.0,
            position_size=1.0,
            transaction_cost=0.001,
            asset="Gold",
            strategy="sma_crossover",
        )

        for i in range(T + 1):
            curr_d = str(df_perturbed["date"].iloc[i])
            open_p = float(df_perturbed["open"].iloc[i])
            close_p = float(df_perturbed["close"].iloc[i])
            sig_val = str(df_perturbed["signal"].iloc[i])

            tracker_perturbed.process_morning_execution(curr_d, open_p)
            tracker_perturbed.process_evening_mark_to_market(curr_d, close_p)
            tracker_perturbed.evaluate_signal_for_next_session(sig_val)

        # Assert equity curve and portfolio values up to T are strictly identical
        orig_curve = res_orig["equity_curve"]
        perturbed_curve = [pt.to_dict() for pt in tracker_perturbed.equity_curve]

        assert len(orig_curve) == len(perturbed_curve)
        for i in range(len(orig_curve)):
            assert orig_curve[i]["date"] == perturbed_curve[i]["date"]
            assert orig_curve[i]["portfolio_value"] == perturbed_curve[i]["portfolio_value"]
            assert orig_curve[i]["cash"] == perturbed_curve[i]["cash"]
            assert orig_curve[i]["position_quantity"] == perturbed_curve[i]["position_quantity"]

        # Assert trades completed up to T are strictly identical
        orig_trades = res_orig["trades"]
        perturbed_trades = [t.to_dict() for t in tracker_perturbed.trades]
        assert len(orig_trades) == len(perturbed_trades)
        for i in range(len(orig_trades)):
            assert orig_trades[i] == perturbed_trades[i]
