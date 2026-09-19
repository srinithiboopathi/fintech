"""
Integration Tests for Correlation and Asset Comparison REST API Endpoints (Phase 5).
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestCorrelationMatrixEndpoint:
    def test_default_all_assets_matrix(self):
        response = client.get("/api/v1/correlation/matrix")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert len(data["assets"]) == 3
        assert "Gold" in data["assets"]
        assert "Bitcoin" in data["assets"]
        assert "NVIDIA" in data["assets"]

        matrix = data["matrix"]
        # Check diagonal
        assert matrix["Gold"]["Gold"] == 1.0
        assert matrix["Bitcoin"]["Bitcoin"] == 1.0
        assert matrix["NVIDIA"]["NVIDIA"] == 1.0

        # Check symmetry
        assert matrix["Gold"]["Bitcoin"] == matrix["Bitcoin"]["Gold"]
        assert matrix["Gold"]["NVIDIA"] == matrix["NVIDIA"]["Gold"]
        assert matrix["Bitcoin"]["NVIDIA"] == matrix["NVIDIA"]["Bitcoin"]

        # Check observation counts exist
        counts = data["observation_counts"]
        assert counts["Gold"]["Bitcoin"] > 0
        assert counts["Gold"]["NVIDIA"] > 0

    def test_custom_subset_matrix(self):
        response = client.get("/api/v1/correlation/matrix?assets=Gold,NVIDIA")
        assert response.status_code == 200
        data = response.json()
        assert len(data["assets"]) == 2
        assert "Gold" in data["assets"]
        assert "NVIDIA" in data["assets"]
        assert "Bitcoin" not in data["assets"]

    def test_matrix_with_date_range(self):
        response = client.get("/api/v1/correlation/matrix?assets=Gold,NVIDIA&start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] >= "2024-01-01"
        assert data["end_date"] <= "2024-12-31"


class TestPairCorrelationEndpoint:
    def test_gold_bitcoin_pair(self):
        response = client.get("/api/v1/correlation/pair?asset_a=Gold&asset_b=Bitcoin")
        assert response.status_code == 200
        data = response.json()
        assert data["asset_a"] == "Gold"
        assert data["asset_b"] == "Bitcoin"
        assert data["observations"] > 0
        assert -1.0 <= data["correlation"] <= 1.0

    def test_bitcoin_nvidia_pair(self):
        response = client.get("/api/v1/correlation/pair?asset_a=Bitcoin&asset_b=NVIDIA")
        assert response.status_code == 200
        data = response.json()
        assert data["asset_a"] == "Bitcoin"
        assert data["asset_b"] == "NVIDIA"
        assert data["observations"] > 0
        assert -1.0 <= data["correlation"] <= 1.0

    def test_case_insensitive_pair(self):
        response = client.get("/api/v1/correlation/pair?asset_a=gold&asset_b=nvda")
        assert response.status_code == 200
        data = response.json()
        assert data["asset_a"] == "Gold"
        assert data["asset_b"] == "NVIDIA"


class TestRollingCorrelationEndpoint:
    def test_gold_nvidia_rolling_correlation(self):
        response = client.get("/api/v1/correlation/rolling?asset_a=Gold&asset_b=NVIDIA&window=60")
        assert response.status_code == 200
        data = response.json()
        assert data["asset_a"] == "Gold"
        assert data["asset_b"] == "NVIDIA"
        assert data["window"] == 60
        assert data["count"] > 1000

        # Check structure of points
        point = data["data"][-1]
        assert "date" in point
        assert "correlation" in point
        assert -1.0 <= point["correlation"] <= 1.0

    def test_bitcoin_gold_rolling_with_date_filter(self):
        response = client.get("/api/v1/correlation/rolling?asset_a=Gold&asset_b=Bitcoin&window=30&start_date=2017-06-01&end_date=2017-12-31")
        assert response.status_code == 200
        data = response.json()
        assert all("2017-06-01" <= p["date"] <= "2017-12-31" for p in data["data"])


class TestAssetComparisonEndpoint:
    def test_all_assets_comparison(self):
        response = client.get("/api/v1/correlation/comparison")
        assert response.status_code == 200
        data = response.json()
        assert len(data["assets"]) == 3
        
        symbols = [a["asset"] for a in data["assets"]]
        assert "Gold" in symbols
        assert "Bitcoin" in symbols
        assert "NVIDIA" in symbols

        for asset_metric in data["assets"]:
            assert asset_metric["records"] > 0
            assert asset_metric["total_return"] is not None
            assert asset_metric["annualized_volatility"] is not None
            assert asset_metric["sharpe_ratio"] is not None
            assert asset_metric["maximum_drawdown"] is not None

    def test_subset_comparison_with_date_filter(self):
        response = client.get("/api/v1/correlation/comparison?assets=Gold,NVIDIA&start_date=2020-01-01&end_date=2024-12-31")
        assert response.status_code == 200
        data = response.json()
        assert len(data["assets"]) == 2
        assert data["aligned_records"] is not None
        assert data["aligned_records"] > 0


class TestCorrelationErrorHandling:
    def test_unknown_asset_in_pair_returns_404(self):
        response = client.get("/api/v1/correlation/pair?asset_a=Gold&asset_b=INVALID")
        assert response.status_code == 404

    def test_unknown_asset_in_matrix_returns_404(self):
        response = client.get("/api/v1/correlation/matrix?assets=Gold,INVALID")
        assert response.status_code == 404

    def test_invalid_date_format_returns_400(self):
        response = client.get("/api/v1/correlation/pair?asset_a=Gold&asset_b=Bitcoin&start_date=not-a-date")
        assert response.status_code == 400

    def test_start_after_end_returns_400(self):
        response = client.get("/api/v1/correlation/matrix?start_date=2025-01-01&end_date=2020-01-01")
        assert response.status_code == 400

    def test_invalid_window_returns_422(self):
        response = client.get("/api/v1/correlation/rolling?asset_a=Gold&asset_b=Bitcoin&window=1")
        assert response.status_code == 422
