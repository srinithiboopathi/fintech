"""
API Integration Tests for Strategy Robustness Endpoints (Phase 8).
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestRobustnessAPI:
    """Test REST endpoints under /api/v1/robustness/."""

    def test_run_robustness_sma_gold(self):
        payload = {
            "asset": "Gold",
            "strategy": "sma_crossover",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000.0,
            "transaction_costs": [0.0, 0.001],
            "strategy_parameter_grid": {
                "fast_period": [10, 20],
                "slow_period": [50],
            },
        }
        response = client.post("/api/v1/robustness/run", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["asset"] == "Gold"
        assert data["strategy"] == "sma_crossover"
        assert "summary" in data
        assert "results" in data
        assert len(data["results"]) == 4  # 2 params * 2 costs * 1 period
        assert data["summary"]["total_configurations"] == 4

        # Validate result structure
        first_res = data["results"][0]
        assert "parameters" in first_res
        assert "transaction_cost" in first_res
        assert "total_return" in first_res
        assert "sharpe_ratio" in first_res
        assert "maximum_drawdown" in first_res

    def test_run_robustness_multi_period_sweep(self):
        payload = {
            "asset": "Bitcoin",
            "strategy": "momentum",
            "periods": [
                {"start_date": "2017-01-01", "end_date": "2017-06-30"},
                {"start_date": "2017-07-01", "end_date": "2017-12-31"},
            ],
            "strategy_parameter_grid": {
                "lookback": [10, 20],
            },
            "transaction_costs": [0.001],
        }
        response = client.post("/api/v1/robustness/run", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 4  # 2 params * 1 cost * 2 periods

    def test_get_robustness_strategies_catalog(self):
        response = client.get("/api/v1/robustness/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) == 4

    def test_error_handling_invalid_asset(self):
        payload = {
            "asset": "NonExistentAsset",
            "strategy": "sma_crossover",
        }
        response = client.post("/api/v1/robustness/run", json=payload)
        assert response.status_code == 404

    def test_error_handling_invalid_strategy(self):
        payload = {
            "asset": "Gold",
            "strategy": "fake_strategy",
        }
        response = client.post("/api/v1/robustness/run", json=payload)
        assert response.status_code == 400

    def test_error_handling_exceed_max_configurations(self):
        # 10 fast * 15 slow = 150 combinations > max_configurations (100)
        payload = {
            "asset": "Gold",
            "strategy": "sma_crossover",
            "strategy_parameter_grid": {
                "fast_period": list(range(5, 15)),
                "slow_period": list(range(20, 35)),
            },
            "max_configurations": 100,
        }
        response = client.post("/api/v1/robustness/run", json=payload)
        assert response.status_code == 400
        assert "exceeding the maximum safety limit" in response.json()["detail"]
