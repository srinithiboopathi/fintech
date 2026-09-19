"""
Integration Tests for Portfolio Optimization REST API (Phase 12).
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


class TestPortfolioOptimizeAPI:
    def test_three_asset_optimization_2017(self):
        payload = {
            "assets": ["Gold", "Bitcoin", "NVIDIA"],
            "start_date": "2017-01-01",
            "end_date": "2017-12-31",
            "risk_free_rate": 0.02,
            "min_weight": 0.0,
            "max_weight": 1.0,
            "random_portfolios": 500,
            "frontier_points": 25,
            "random_seed": 42,
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Check metadata
        assert data["assets"] == ["Gold", "Bitcoin", "NVIDIA"]
        assert data["observations"] > 200
        assert data["start_date"] == "2017-01-03" or data["start_date"].startswith("2017")
        assert data["risk_free_rate"] == 0.02

        # Check asset expected returns & covariance matrix
        assert "Gold" in data["asset_expected_returns"]
        assert "Bitcoin" in data["asset_expected_returns"]
        assert "NVIDIA" in data["asset_expected_returns"]
        assert "Gold" in data["covariance_matrix"]

        # Check optimal portfolios
        opts = data["optimal_portfolios"]
        assert "max_sharpe" in opts
        assert "min_volatility" in opts
        assert "equal_weight" in opts

        # Max Sharpe checks
        ms = opts["max_sharpe"]
        assert ms["portfolio_type"] == "Maximum Sharpe"
        assert sum(ms["weights"].values()) == pytest.approx(1.0, abs=1e-4)
        assert ms["volatility"] > 0.0
        assert ms["sharpe_ratio"] >= opts["min_volatility"]["sharpe_ratio"] - 1e-4

        # GMV checks
        gmv = opts["min_volatility"]
        assert gmv["portfolio_type"] == "Minimum Volatility"
        assert sum(gmv["weights"].values()) == pytest.approx(1.0, abs=1e-4)
        assert gmv["volatility"] <= opts["equal_weight"]["volatility"] + 1e-4

        # Equal weight checks
        eq = opts["equal_weight"]
        assert eq["portfolio_type"] == "Equal Weight"
        for a, w in eq["weights"].items():
            assert w == pytest.approx(1.0 / 3.0, abs=1e-4)

        # Check efficient frontier
        frontier = data["efficient_frontier"]
        assert len(frontier) >= 10
        for pt in frontier:
            assert "target_return" in pt
            assert "expected_return" in pt
            assert "volatility" in pt
            assert "sharpe_ratio" in pt
            assert sum(pt["weights"].values()) == pytest.approx(1.0, abs=1e-3)

        # Check random portfolios
        r_ports = data["random_portfolios"]
        assert len(r_ports) == 500
        for rp in r_ports:
            assert rp["volatility"] > 0.0
            assert sum(rp["weights"].values()) == pytest.approx(1.0, abs=1e-4)

        # Check comparison items
        comparison = data["comparison"]
        assert len(comparison) >= 3
        comp_names = [c["name"] for c in comparison]
        assert "Maximum Sharpe" in comp_names
        assert "Minimum Volatility" in comp_names
        assert "Equal Weight" in comp_names

    def test_two_asset_optimization_multi_year(self):
        payload = {
            "assets": ["Gold", "NVIDIA"],
            "start_date": "2020-01-01",
            "end_date": "2023-12-31",
            "risk_free_rate": 0.02,
            "min_weight": 0.05,
            "max_weight": 0.95,
            "random_portfolios": 200,
            "frontier_points": 15,
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["assets"] == ["Gold", "NVIDIA"]
        assert data["observations"] > 500

        opts = data["optimal_portfolios"]
        ms = opts["max_sharpe"]
        assert ms["weights"]["Gold"] >= 0.05 - 1e-5
        assert ms["weights"]["NVIDIA"] <= 0.95 + 1e-5

    def test_with_user_portfolio_weights(self):
        payload = {
            "assets": ["Gold", "Bitcoin", "NVIDIA"],
            "start_date": "2017-01-01",
            "end_date": "2017-12-31",
            "user_weights": {"Gold": 0.5, "Bitcoin": 0.25, "NVIDIA": 0.25},
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 200
        data = response.json()
        opts = data["optimal_portfolios"]
        assert opts["user_portfolio"] is not None
        user_p = opts["user_portfolio"]
        assert user_p["portfolio_type"] == "User Portfolio"
        assert user_p["weights"]["Gold"] == pytest.approx(0.5, abs=1e-4)

        comp_names = [c["name"] for c in data["comparison"]]
        assert "User Portfolio" in comp_names

    def test_infeasible_bounds_error(self):
        payload = {
            "assets": ["Gold", "Bitcoin", "NVIDIA"],
            "min_weight": 0.4,  # 3 * 0.4 = 1.2 > 1.0
            "max_weight": 1.0,
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 422
        assert "exceeds 100%" in response.json()["detail"]

    def test_insufficient_assets_error(self):
        payload = {
            "assets": ["Gold"],
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 422

    def test_invalid_date_range_error(self):
        payload = {
            "assets": ["Gold", "NVIDIA"],
            "start_date": "2023-01-01",
            "end_date": "2020-01-01",
        }
        response = client.post("/api/v1/portfolio/optimize", json=payload)
        assert response.status_code == 422
