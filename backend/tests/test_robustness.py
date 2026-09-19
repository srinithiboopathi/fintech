"""
Unit and Integration Tests for Strategy Robustness Lab (Phase 8).
Tests parameter grids, sensitivity sweeps, safety limits, deterministic execution, and constraints.
"""
import pytest
import pandas as pd
import numpy as np

from backend.app.robustness.models import BacktestConfig, RobustnessResult
from backend.app.robustness.validation import (
    validate_robustness_inputs,
    validate_grid_size,
    MAX_CONFIGURATIONS,
)
from backend.app.robustness.parameter_grid import (
    generate_strategy_parameter_combinations,
    build_backtest_configurations,
)
from backend.app.robustness.comparison import summarize_robustness_results
from backend.app.robustness.runner import RobustnessRunner
from backend.app.services.robustness_service import RobustnessService


@pytest.fixture
def robustness_runner():
    return RobustnessRunner()


@pytest.fixture
def robustness_service():
    return RobustnessService()


class TestRobustnessGridGeneration:
    def test_sma_parameter_combinations(self):
        grid = {"fast_period": [10, 20], "slow_period": [30, 50]}
        combos = generate_strategy_parameter_combinations("sma_crossover", grid)
        assert len(combos) == 4
        for c in combos:
            assert c["fast_period"] < c["slow_period"]

    def test_sma_invalid_combinations_filtered(self):
        # fast_period >= slow_period should be filtered out
        grid = {"fast_period": [10, 50], "slow_period": [20, 50]}
        combos = generate_strategy_parameter_combinations("sma_crossover", grid)
        # (10, 20): valid, (10, 50): valid, (50, 20): invalid, (50, 50): invalid
        assert len(combos) == 2
        for c in combos:
            assert c["fast_period"] < c["slow_period"]

    def test_ema_parameter_combinations(self):
        grid = {"short_period": [5, 12], "long_period": [26, 50]}
        combos = generate_strategy_parameter_combinations("ema_trend", grid)
        assert len(combos) == 4
        for c in combos:
            assert c["short_period"] < c["long_period"]

    def test_momentum_parameter_combinations(self):
        grid = {"lookback": [10, 20, 30]}
        combos = generate_strategy_parameter_combinations("momentum", grid)
        assert len(combos) == 3
        assert [c["lookback"] for c in combos] == [10, 20, 30]

    def test_mean_reversion_parameter_combinations(self):
        grid = {"window": [20, 50], "threshold": [1.5, 2.0]}
        combos = generate_strategy_parameter_combinations("mean_reversion", grid)
        assert len(combos) == 4

    def test_empty_grid_uses_strategy_defaults(self):
        combos = generate_strategy_parameter_combinations("sma_crossover", {})
        assert len(combos) == 1
        assert combos[0] == {"fast_period": 20, "slow_period": 50}

    def test_cartesian_product_configurations(self):
        param_grid = {"fast_period": [10, 20], "slow_period": [50]}
        costs = [0.0, 0.001]
        periods = [
            {"start_date": "2020-01-01", "end_date": "2022-12-31"},
            {"start_date": "2023-01-01", "end_date": "2024-12-31"},
        ]
        configs = build_backtest_configurations(
            strategy="sma_crossover",
            grid=param_grid,
            transaction_costs=costs,
            periods=periods,
            initial_capital=100000.0,
            position_size=1.0,
            risk_free_rate=0.0,
        )
        # 2 param combos * 2 costs * 2 periods = 8 configurations
        assert len(configs) == 8


class TestRobustnessValidation:
    def test_max_configuration_limit_exceeded(self):
        with pytest.raises(ValueError, match="exceeding the maximum safety limit"):
            validate_grid_size(150, max_limit=100)

    def test_invalid_strategy_name(self):
        with pytest.raises(ValueError, match="Unknown strategy"):
            validate_robustness_inputs(
                asset="Gold",
                strategy="magic_wand_strategy",
                initial_capital=100000.0,
                position_size=1.0,
                transaction_costs=[0.001],
            )

    def test_invalid_transaction_cost(self):
        with pytest.raises(ValueError, match="Transaction cost must be non-negative"):
            validate_robustness_inputs(
                asset="Gold",
                strategy="sma_crossover",
                initial_capital=100000.0,
                position_size=1.0,
                transaction_costs=[-0.01],
            )


class TestRobustnessExecution:
    def test_sma_robustness_sweep(self, robustness_runner):
        result = robustness_runner.run_sweep(
            asset="Gold",
            strategy="sma_crossover",
            parameter_grid={"fast_period": [10, 20], "slow_period": [50]},
            transaction_costs=[0.0, 0.001],
            periods=[{"start_date": "2022-01-01", "end_date": "2024-12-31"}],
            max_configurations=10,
        )
        assert result["asset"] == "Gold"
        assert result["strategy"] == "sma_crossover"
        assert result["summary"]["total_configurations"] == 4
        assert len(result["results"]) == 4

        # Check all required fields are present in results
        for item in result["results"]:
            assert "parameters" in item
            assert "transaction_cost" in item
            assert "total_return" in item
            assert "annualized_return" in item
            assert "sharpe_ratio" in item
            assert "maximum_drawdown" in item
            assert "number_of_trades" in item
            assert "win_rate" in item

        # Check summary ranges
        ranges = result["summary"]["metrics_ranges"]
        assert ranges["return_range"]["min"] <= ranges["return_range"]["max"]
        assert ranges["sharpe_range"]["min"] <= ranges["sharpe_range"]["max"]
        assert ranges["drawdown_range"]["min"] <= ranges["drawdown_range"]["max"]

    def test_deterministic_repeated_execution(self, robustness_runner):
        run1 = robustness_runner.run_sweep(
            asset="NVIDIA",
            strategy="momentum",
            parameter_grid={"lookback": [10, 20]},
            transaction_costs=[0.001],
            periods=[{"start_date": "2023-01-01", "end_date": "2024-12-31"}],
        )
        run2 = robustness_runner.run_sweep(
            asset="NVIDIA",
            strategy="momentum",
            parameter_grid={"lookback": [10, 20]},
            transaction_costs=[0.001],
            periods=[{"start_date": "2023-01-01", "end_date": "2024-12-31"}],
        )
        assert run1 == run2

    def test_no_ranking_or_best_selection(self, robustness_runner):
        result = robustness_runner.run_sweep(
            asset="Bitcoin",
            strategy="ema_trend",
            parameter_grid={"short_period": [10], "long_period": [30, 50]},
            transaction_costs=[0.0, 0.002],
        )
        # Verify no "best" or ranking key exists in response
        assert "best" not in result
        assert "rank" not in result
        assert "winner" not in result
        assert "best_configuration" not in result["summary"]
