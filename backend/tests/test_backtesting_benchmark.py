"""
Unit Tests for Buy-and-Hold Benchmark Simulation and Strategy Comparison (Phase 7).
"""
import pytest
import pandas as pd
import numpy as np

from backend.app.backtesting.benchmark import (
    calculate_buy_and_hold_benchmark,
    calculate_strategy_comparison,
)


class TestBenchmarkEngine:
    """Test Buy-and-Hold benchmark simulation and comparative differentials."""

    def test_buy_and_hold_synthetic(self):
        # 4-day price series: [100, 110, 120, 150]
        dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
        df = pd.DataFrame({
            "date": dates,
            "open": [100.0, 110.0, 120.0, 150.0],
            "high": [105.0, 115.0, 125.0, 155.0],
            "low": [95.0, 105.0, 115.0, 145.0],
            "close": [100.0, 110.0, 120.0, 150.0],
            "volume": [1000, 1000, 1000, 1000],
        })

        initial_capital = 100000.0
        fee_pct = 0.001  # 0.1%

        res = calculate_buy_and_hold_benchmark(
            df=df,
            initial_capital=initial_capital,
            transaction_cost=fee_pct,
            asset="Gold",
            risk_free_rate=0.0,
        )

        assert res["initial_capital"] == 100000.0
        assert res["final_value"] > 149000.0
        assert res["total_return"] > 0.49
        assert len(res["equity_curve"]) == 4

        # Initial day check (100,000 minus 0.1% entry fee = 99,900.10)
        first_pt = res["equity_curve"][0]
        assert pytest.approx(first_pt.portfolio_value, rel=1e-3) == 99900.10


    def test_strategy_comparison_differentials(self):
        strat_perf = {
            "total_return": 0.25,
            "annualized_return": 0.25,
            "annualized_volatility": 0.15,
            "sharpe_ratio": 1.50,
            "maximum_drawdown": -0.10,
        }

        bench_perf = {
            "total_return": 0.15,
            "annualized_return": 0.15,
            "annualized_volatility": 0.20,
            "sharpe_ratio": 0.75,
            "maximum_drawdown": -0.25,
        }

        comp = calculate_strategy_comparison(strat_perf, bench_perf)

        assert pytest.approx(comp["return_difference"], rel=1e-5) == 0.10
        assert pytest.approx(comp["annualized_return_difference"], rel=1e-5) == 0.10
        assert pytest.approx(comp["volatility_difference"], rel=1e-5) == -0.05
        assert pytest.approx(comp["sharpe_difference"], rel=1e-5) == 0.75
        assert pytest.approx(comp["mdd_difference"], rel=1e-5) == 0.15
