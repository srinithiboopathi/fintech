"""
API Integration Tests for Strategy Signal Endpoints (Phase 6).
Tests route responses, schema compliance, date slicing, multi-asset compatibility, and error handling.
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestStrategyAPI:
    """Test REST API routes under /api/v1/strategies/."""

    def test_sma_crossover_default(self):
        response = client.get("/api/v1/strategies/Gold/sma-crossover")
        assert response.status_code == 200
        data = response.json()

        assert data["asset"] == "Gold"
        assert data["strategy"] == "sma_crossover"
        assert data["parameters"] == {"fast_period": 20, "slow_period": 50}
        assert data["count"] > 0
        assert data["summary"]["total"] == data["count"]
        assert data["summary"]["buy"] >= 0
        assert data["summary"]["sell"] >= 0
        assert data["summary"]["hold"] > 0

        first_pt = data["data"][0]
        assert "date" in first_pt
        assert "close" in first_pt
        assert "signal" in first_pt
        assert "fast_sma" in first_pt
        assert "slow_sma" in first_pt

    def test_sma_crossover_custom_params_and_dates(self):
        response = client.get(
            "/api/v1/strategies/NVIDIA/sma-crossover",
            params={
                "fast_period": 10,
                "slow_period": 30,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["parameters"]["fast_period"] == 10
        assert data["parameters"]["slow_period"] == 30
        assert data["start_date"] == "2024-01-01"
        assert data["end_date"] == "2024-12-31"

        # Verify that because indicators were computed on full history,
        # the first slice point (2024-01-02) already has valid non-null SMAs!
        for pt in data["data"]:
            assert pt["date"] >= "2024-01-01"
            assert pt["date"] <= "2024-12-31"
            assert pt["fast_sma"] is not None
            assert pt["slow_sma"] is not None

    def test_ema_trend_default_and_custom(self):
        response = client.get(
            "/api/v1/strategies/Bitcoin/ema-trend",
            params={"short_period": 10, "long_period": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["strategy"] == "ema_trend"
        assert data["parameters"] == {"short_period": 10, "long_period": 30}
        assert data["count"] > 0
        assert "short_ema" in data["data"][0]
        assert "long_ema" in data["data"][0]

    def test_momentum_default_and_custom(self):
        response = client.get(
            "/api/v1/strategies/Gold/momentum",
            params={"lookback": 15, "start_date": "2023-01-01", "end_date": "2023-12-31"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["strategy"] == "momentum"
        assert data["parameters"] == {"lookback": 15}
        assert data["count"] > 0
        assert "momentum" in data["data"][0]

    def test_mean_reversion_default_and_custom(self):
        response = client.get(
            "/api/v1/strategies/NVIDIA/mean-reversion",
            params={"window": 30, "threshold": 0.05},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["strategy"] == "mean_reversion"
        assert data["parameters"] == {"window": 30, "threshold": 0.05}
        assert data["count"] > 0
        assert "moving_average" in data["data"][0]
        assert "deviation" in data["data"][0]

    def test_unified_signals_endpoint(self):
        # SMA Crossover via unified endpoint
        res_sma = client.get(
            "/api/v1/strategies/Gold/signals",
            params={"strategy": "sma_crossover", "fast_period": 20, "slow_period": 50},
        )
        assert res_sma.status_code == 200
        assert res_sma.json()["strategy"] == "sma_crossover"

        # EMA Trend
        res_ema = client.get(
            "/api/v1/strategies/Bitcoin/signals",
            params={"strategy": "ema_trend", "short_period": 10, "long_period": 20},
        )
        assert res_ema.status_code == 200
        assert res_ema.json()["strategy"] == "ema_trend"

        # Momentum
        res_mom = client.get(
            "/api/v1/strategies/NVIDIA/signals",
            params={"strategy": "momentum", "lookback": 10},
        )
        assert res_mom.status_code == 200
        assert res_mom.json()["strategy"] == "momentum"

        # Mean Reversion
        res_mr = client.get(
            "/api/v1/strategies/Gold/signals",
            params={"strategy": "mean_reversion", "window": 20, "threshold": 0.03},
        )
        assert res_mr.status_code == 200
        assert res_mr.json()["strategy"] == "mean_reversion"

    def test_case_insensitive_asset_names(self):
        res1 = client.get("/api/v1/strategies/gold/sma-crossover")
        assert res1.status_code == 200
        assert res1.json()["asset"] == "Gold"

        res2 = client.get("/api/v1/strategies/BITCOIN/momentum")
        assert res2.status_code == 200
        assert res2.json()["asset"] == "Bitcoin"

        res3 = client.get("/api/v1/strategies/nvidia/mean-reversion")
        assert res3.status_code == 200
        assert res3.json()["asset"] == "NVIDIA"

    def test_error_handling_invalid_asset(self):
        res = client.get("/api/v1/strategies/UnknownAsset/sma-crossover")
        assert res.status_code == 404
        assert "not recognized" in res.json()["detail"]

    def test_error_handling_invalid_dates(self):
        # Bad format
        res = client.get("/api/v1/strategies/Gold/sma-crossover?start_date=2024-13-45")
        assert res.status_code == 400

        # Start > End
        res2 = client.get("/api/v1/strategies/Gold/sma-crossover?start_date=2024-12-31&end_date=2024-01-01")
        assert res2.status_code == 400
        assert "cannot be greater than" in res2.json()["detail"]

    def test_error_handling_invalid_strategy_parameters(self):
        # fast >= slow
        res1 = client.get("/api/v1/strategies/Gold/sma-crossover?fast_period=50&slow_period=20")
        assert res1.status_code == 400
        assert "strictly less than" in res1.json()["detail"]

        # short >= long
        res2 = client.get("/api/v1/strategies/Gold/ema-trend?short_period=50&long_period=50")
        assert res2.status_code == 400

        # invalid threshold
        res3 = client.get("/api/v1/strategies/Gold/mean-reversion?threshold=-0.05")
        assert res3.status_code in [400, 422]

        # invalid unified strategy
        res4 = client.get("/api/v1/strategies/Gold/signals?strategy=non_existent_strat")
        assert res4.status_code == 400
        assert "Unknown strategy" in res4.json()["detail"]
