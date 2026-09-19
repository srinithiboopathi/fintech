"""
Integration Tests for Quantitative Analysis APIs (Phase 4).
Tests all REST endpoints across Gold, Bitcoin, NVIDIA datasets with real parameters.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestIndicatorsEndpoint:
    def test_gold_indicators_default(self):
        response = client.get("/api/v1/quant/Gold/indicators")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["sma_period"] == 20
        assert data["ema_period"] == 20
        assert data["count"] == 6358
        
        first = data["data"][0]
        assert "date" in first
        assert "close" in first
        assert "sma" in first
        assert "ema" in first
        # First 19 SMA values should be null (warmup)
        assert data["data"][0]["sma"] is None
        assert data["data"][18]["sma"] is None
        assert data["data"][19]["sma"] is not None

    def test_bitcoin_indicators_custom_periods(self):
        response = client.get("/api/v1/quant/Bitcoin/indicators?sma_period=5&ema_period=10")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["sma_period"] == 5
        assert data["ema_period"] == 10
        assert data["count"] == 365

    def test_nvidia_indicators_date_filter(self):
        response = client.get("/api/v1/quant/NVIDIA/indicators?start_date=2024-01-01&end_date=2024-03-31")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert all("2024-01-01" <= p["date"] <= "2024-03-31" for p in data["data"])


class TestReturnsEndpoint:
    def test_gold_returns_schema(self):
        response = client.get("/api/v1/quant/Gold/returns")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["count"] == 6358
        
        first = data["data"][0]
        assert first["daily_return"] is None  # first observation has no prior return
        assert first["cumulative_return"] == 0.0

        second = data["data"][1]
        assert second["daily_return"] is not None
        assert second["cumulative_return"] is not None

    def test_bitcoin_returns(self):
        response = client.get("/api/v1/quant/Bitcoin/returns")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["count"] == 365


class TestVolatilityEndpoint:
    def test_gold_volatility(self):
        response = client.get("/api/v1/quant/Gold/volatility?window=30")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["window"] == 30
        assert data["annualization_factor"] == 252
        assert len(data["data"]) == 6358

    def test_bitcoin_volatility_annualization_factor(self):
        response = client.get("/api/v1/quant/Bitcoin/volatility?window=20")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["annualization_factor"] == 365  # 24/7 continuous market


class TestRiskMetricsEndpoint:
    def test_nvidia_risk_metrics(self):
        response = client.get("/api/v1/quant/NVIDIA/risk-metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["records"] == 6778
        assert data["annualization_factor"] == 252
        assert data["annualized_volatility"] > 0
        assert data["sharpe_ratio"] is not None
        assert data["maximum_drawdown"] < 0  # Drawdown is negative

    def test_bitcoin_risk_metrics_with_risk_free_rate(self):
        response = client.get("/api/v1/quant/Bitcoin/risk-metrics?risk_free_rate=0.05")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["risk_free_rate"] == 0.05
        assert data["annualization_factor"] == 365
        assert data["annualized_volatility"] > 0
        assert data["sharpe_ratio"] is not None


class TestRollingPerformanceEndpoint:
    def test_gold_rolling_performance(self):
        response = client.get("/api/v1/quant/Gold/rolling-performance?window=60")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["window"] == 60
        assert len(data["data"]) == 6358
        
        point = data["data"][-1]
        assert "rolling_return" in point
        assert "rolling_volatility" in point
        assert "rolling_sharpe" in point
        assert "drawdown" in point


class TestQuantSummaryEndpoint:
    def test_nvidia_summary(self):
        response = client.get("/api/v1/quant/NVIDIA/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["records"] == 6778
        assert data["latest_close"] > 0
        assert data["cumulative_return"] is not None
        assert data["annualized_volatility"] is not None
        assert data["sharpe_ratio"] is not None
        assert data["maximum_drawdown"] is not None
        
        stats = data["return_statistics"]
        assert stats["positive_days"] > 0
        assert stats["negative_days"] > 0
        assert stats["min"] < 0
        assert stats["max"] > 0

    def test_case_insensitive_asset_names(self):
        for variant in ["gold", "GOLD", "btc", "nvda", "Nvidia"]:
            response = client.get(f"/api/v1/quant/{variant}/summary")
            assert response.status_code == 200
            assert response.json()["records"] > 0


class TestErrorHandlingAndValidation:
    def test_unknown_asset_returns_404(self):
        response = client.get("/api/v1/quant/Ethereum/summary")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower() or "not recognized" in response.json()["detail"].lower()

    def test_invalid_date_format_returns_400(self):
        response = client.get("/api/v1/quant/Gold/returns?start_date=invalid-date")
        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]

    def test_start_date_after_end_date_returns_400(self):
        response = client.get("/api/v1/quant/Gold/indicators?start_date=2024-01-01&end_date=2023-01-01")
        assert response.status_code == 400
        assert "start_date" in response.json()["detail"]

    def test_invalid_parameter_bounds_returns_422(self):
        # Window < 2
        response = client.get("/api/v1/quant/Gold/volatility?window=1")
        assert response.status_code == 422

        # SMA Period < 1
        response = client.get("/api/v1/quant/Gold/indicators?sma_period=0")
        assert response.status_code == 422
