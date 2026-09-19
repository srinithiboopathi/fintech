"""
Integration Tests for Portfolio Analytics REST API (Phase 11).
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestPortfolioAnalyzeAPI:
    def test_three_asset_portfolio_2017(self):
        payload = {
            "weights": {"Gold": 0.4, "Bitcoin": 0.3, "NVIDIA": 0.3},
            "start_date": "2017-01-01",
            "end_date": "2017-12-31",
            "initial_capital": 100000.0,
            "risk_free_rate": 0.02,
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Check weights
        assert data["weights"]["Gold"] == pytest.approx(0.4)
        assert data["weights"]["Bitcoin"] == pytest.approx(0.3)
        assert data["weights"]["NVIDIA"] == pytest.approx(0.3)

        # Check summary metrics
        summary = data["summary"]
        assert summary["initial_capital"] == 100000.0
        assert summary["final_value"] > 0.0
        assert summary["total_return"] is not None
        assert summary["annualized_return"] is not None
        assert summary["annualized_volatility"] > 0.0
        assert summary["sharpe_ratio"] is not None
        assert summary["maximum_drawdown"] <= 0.0
        assert summary["observations"] > 200

        # Check performance contributions
        p_contribs = data["performance_contributions"]
        assert len(p_contribs) == 3
        assets_in_p = {c["asset"] for c in p_contribs}
        assert assets_in_p == {"Gold", "Bitcoin", "NVIDIA"}
        for c in p_contribs:
            assert c["weight"] > 0
            assert c["total_return"] is not None
            assert c["weighted_contribution"] is not None

        # Check risk contributions
        r_contribs = data["risk_contributions"]
        assert len(r_contribs) == 3
        sum_ccr = sum(r["component_risk_contribution"] for r in r_contribs)
        assert sum_ccr == pytest.approx(summary["annualized_volatility"], rel=1e-3)
        sum_pct = sum(r["percentage_risk_contribution"] for r in r_contribs)
        assert sum_pct == pytest.approx(1.0, rel=1e-3)

        # Check covariance matrix
        cov = data["covariance_matrix"]
        assert "Gold" in cov and "Bitcoin" in cov and "NVIDIA" in cov
        assert cov["Gold"]["Gold"] > 0
        assert cov["Bitcoin"]["Bitcoin"] > 0
        assert cov["NVIDIA"]["NVIDIA"] > 0

        # Check data points
        assert len(data["data"]) == summary["observations"]
        first_point = data["data"][0]
        assert "date" in first_point
        assert "portfolio_return" in first_point
        assert "portfolio_value" in first_point
        assert "drawdown" in first_point

        # Check comparison series
        assert len(data["comparison"]) == summary["observations"]
        first_comp = data["comparison"][0]
        assert first_comp["portfolio"] == pytest.approx(100.0 * (1.0 + data["data"][0]["cumulative_return"]), rel=1e-3)
        assert "Gold" in first_comp["assets"]
        assert "Bitcoin" in first_comp["assets"]
        assert "NVIDIA" in first_comp["assets"]

    def test_two_asset_portfolio_longer_range(self):
        payload = {
            "weights": {"Gold": 0.6, "NVIDIA": 0.4},
            "start_date": "2020-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 50000.0,
            "risk_free_rate": 0.02,
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "Bitcoin" not in data["weights"]
        assert len(data["performance_contributions"]) == 2
        assert len(data["risk_contributions"]) == 2
        assert data["summary"]["observations"] > 800

    def test_single_asset_portfolio(self):
        payload = {
            "weights": {"Gold": 1.0},
            "start_date": "2022-01-01",
            "end_date": "2022-12-31",
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["weights"]) == 1
        assert data["risk_contributions"][0]["percentage_risk_contribution"] == pytest.approx(1.0, 1e-4)

    def test_invalid_weight_sum_fails(self):
        payload = {
            "weights": {"Gold": 0.4, "Bitcoin": 0.3},  # sums to 0.7
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 422
        assert "must sum to 100%" in response.json()["detail"]

    def test_negative_weight_fails(self):
        payload = {
            "weights": {"Gold": 0.8, "Bitcoin": -0.2},
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 422
        assert "cannot be negative" in response.json()["detail"]

    def test_weight_greater_than_one_fails(self):
        payload = {
            "weights": {"Gold": 1.2},
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 422
        assert "cannot exceed 100%" in response.json()["detail"]

    def test_unknown_asset_fails(self):
        payload = {
            "weights": {"Apple": 0.5, "Gold": 0.5},
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 422
        assert "Unknown asset identifier" in response.json()["detail"]

    def test_bitcoin_date_out_of_range_handling(self):
        # Bitcoin dataset only has 2017 data
        payload = {
            "weights": {"Bitcoin": 0.5, "Gold": 0.5},
            "start_date": "2022-01-01",
            "end_date": "2022-12-31",
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        # Should return 400 with helpful message about overlapping observations or Bitcoin availability
        assert response.status_code == 400
        assert "observations" in response.json()["detail"].lower() or "bitcoin" in response.json()["detail"].lower()

    def test_invalid_capital_fails(self):
        payload = {
            "weights": {"Gold": 1.0},
            "initial_capital": -1000.0,
        }
        response = client.post("/api/v1/portfolio/analyze", json=payload)
        assert response.status_code == 422
