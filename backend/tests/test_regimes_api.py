"""
API Integration Tests for Market Regime Endpoints (Phase 8).
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


class TestRegimesAPI:
    """Test REST endpoints under /api/v1/regimes/."""

    def test_get_gold_regimes_default(self):
        response = client.get("/api/v1/regimes/Gold")
        assert response.status_code == 200
        data = response.json()

        assert data["asset"] == "Gold"
        assert data["trend_window"] == 50
        assert data["volatility_window"] == 20
        assert data["threshold_mode"] == "historical_descriptive"
        assert "summary_statistics" in data
        assert "transitions" in data
        assert "data" in data
        assert len(data["data"]) > 0

        # Check summary structure
        stats = data["summary_statistics"]
        assert "bull" in stats
        assert "bear" in stats
        assert "high_volatility" in stats
        assert "low_volatility" in stats
        assert stats["bull"]["observation_count"] > 0
        assert stats["bear"]["observation_count"] > 0

    def test_get_bitcoin_regimes_expanding_threshold(self):
        response = client.get(
            "/api/v1/regimes/Bitcoin?trend_window=30&volatility_window=14&threshold_mode=expanding_threshold"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["trend_window"] == 30
        assert data["volatility_window"] == 14
        assert data["threshold_mode"] == "expanding_threshold"

    def test_get_nvidia_regimes_with_date_filter(self):
        response = client.get(
            "/api/v1/regimes/NVIDIA?start_date=2024-01-01&end_date=2024-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert len(data["data"]) > 0
        for item in data["data"]:
            assert "2024-01-01" <= item["date"] <= "2024-12-31"

    def test_case_insensitive_and_alias_assets(self):
        # lower case
        res1 = client.get("/api/v1/regimes/gold")
        assert res1.status_code == 200
        assert res1.json()["asset"] == "Gold"

        # alias
        res2 = client.get("/api/v1/regimes/nvda")
        assert res2.status_code == 200
        assert res2.json()["asset"] == "NVIDIA"

        # btc alias
        res3 = client.get("/api/v1/regimes/btc")
        assert res3.status_code == 200
        assert res3.json()["asset"] == "Bitcoin"

    def test_error_handling_invalid_asset(self):
        response = client.get("/api/v1/regimes/InvalidAsset123")
        assert response.status_code == 404
        assert "not recognized" in response.json()["detail"]

    def test_error_handling_invalid_windows(self):
        # trend_window < 2
        res1 = client.get("/api/v1/regimes/Gold?trend_window=1")
        assert res1.status_code in [400, 422]

        # volatility_window < 2
        res2 = client.get("/api/v1/regimes/Gold?volatility_window=0")
        assert res2.status_code in [400, 422]

    def test_error_handling_invalid_date_range(self):
        response = client.get("/api/v1/regimes/Gold?start_date=2024-12-31&end_date=2024-01-01")
        assert response.status_code == 400
        assert "cannot be after" in response.json()["detail"]
