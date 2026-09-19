"""
API Integration Tests for Backtesting Endpoints (Phase 7).
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestBacktestingAPI:
    """Test REST endpoints under /api/v1/backtesting/."""

    def test_run_backtest_sma_crossover_gold(self):
        payload = {
            "asset": "Gold",
            "strategy": "sma_crossover",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000.0,
            "position_size": 1.0,
            "transaction_cost": 0.001,
            "risk_free_rate": 0.0,
            "strategy_parameters": {
                "fast_period": 20,
                "slow_period": 50,
            },
        }
        response = client.post("/api/v1/backtesting/run", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["backtest"]["asset"] == "Gold"
        assert data["strategy"]["name"] == "sma_crossover"
        assert "performance" in data
        assert "benchmark" in data
        assert "comparison" in data
        assert len(data["equity_curve"]) > 0
        assert data["performance"]["initial_capital"] == 100000.0

    def test_run_backtest_all_strategies(self):
        # EMA Trend
        res_ema = client.post("/api/v1/backtesting/run", json={
            "asset": "Bitcoin",
            "strategy": "ema_trend",
            "initial_capital": 50000.0,
            "strategy_parameters": {"short_period": 10, "long_period": 30},
        })
        assert res_ema.status_code == 200
        assert res_ema.json()["strategy"]["name"] == "ema_trend"

        # Momentum
        res_mom = client.post("/api/v1/backtesting/run", json={
            "asset": "NVIDIA",
            "strategy": "momentum",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "strategy_parameters": {"lookback": 15},
        })
        assert res_mom.status_code == 200
        assert res_mom.json()["strategy"]["name"] == "momentum"

        # Mean Reversion
        res_mr = client.post("/api/v1/backtesting/run", json={
            "asset": "Gold",
            "strategy": "mean_reversion",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "strategy_parameters": {"window": 20, "threshold": 0.02},
        })
        assert res_mr.status_code == 200
        assert res_mr.json()["strategy"]["name"] == "mean_reversion"

    def test_get_strategies_catalog(self):
        response = client.get("/api/v1/backtesting/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) == 4

        names = [s["name"] for s in data["strategies"]]
        assert "sma_crossover" in names
        assert "ema_trend" in names
        assert "momentum" in names
        assert "mean_reversion" in names

    def test_error_handling_invalid_asset(self):
        payload = {
            "asset": "UnknownStock",
            "strategy": "sma_crossover",
        }
        res = client.post("/api/v1/backtesting/run", json=payload)
        assert res.status_code == 404
        assert "not recognized" in res.json()["detail"]

    def test_error_handling_invalid_strategy(self):
        payload = {
            "asset": "Gold",
            "strategy": "invalid_strat",
        }
        res = client.post("/api/v1/backtesting/run", json=payload)
        assert res.status_code == 400
        assert "Unknown strategy" in res.json()["detail"]

    def test_error_handling_invalid_parameters(self):
        # Initial capital <= 0
        res1 = client.post("/api/v1/backtesting/run", json={
            "asset": "Gold",
            "strategy": "sma_crossover",
            "initial_capital": -100,
        })
        assert res1.status_code in [400, 422]

        # Position size > 1.0
        res2 = client.post("/api/v1/backtesting/run", json={
            "asset": "Gold",
            "strategy": "sma_crossover",
            "position_size": 1.5,
        })
        assert res2.status_code in [400, 422]

        # Fast period >= slow period
        res3 = client.post("/api/v1/backtesting/run", json={
            "asset": "Gold",
            "strategy": "sma_crossover",
            "strategy_parameters": {"fast_period": 50, "slow_period": 20},
        })
        assert res3.status_code == 400
        assert "strictly less than" in res3.json()["detail"]

        # Date start > end
        res4 = client.post("/api/v1/backtesting/run", json={
            "asset": "Gold",
            "strategy": "sma_crossover",
            "start_date": "2024-12-31",
            "end_date": "2024-01-01",
        })
        assert res4.status_code == 400
