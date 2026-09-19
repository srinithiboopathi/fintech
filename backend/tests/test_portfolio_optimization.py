"""
Unit Tests for Portfolio Optimization & Efficient Frontier Engine.
Mathematical correctness, solver constraints, Kuhn-Tucker conditions, and edge cases.
"""
import pytest
import numpy as np
import pandas as pd
from fastapi import HTTPException

from backend.app.portfolio.optimization.constraints import validate_optimization_parameters
from backend.app.portfolio.optimization.optimizer import (
    calculate_portfolio_stats,
    optimize_equal_weight,
    optimize_min_volatility,
    optimize_max_sharpe,
    optimize_for_target_return,
)
from backend.app.portfolio.optimization.frontier import (
    generate_efficient_frontier,
    generate_random_portfolios,
    get_max_feasible_expected_return,
)


@pytest.fixture
def sample_market_inputs():
    """Provides deterministic expected returns and covariance matrix for 3 assets."""
    assets = ["Gold", "Bitcoin", "NVIDIA"]
    # Annualized returns
    mu = np.array([0.08, 0.65, 0.35], dtype=float)
    # Annualized standard deviations: Gold=15%, BTC=70%, NVDA=45%
    # Correlations: Gold-BTC=0.05, Gold-NVDA=0.10, BTC-NVDA=0.30
    vols = np.array([0.15, 0.70, 0.45], dtype=float)
    corr = np.array([
        [1.00, 0.05, 0.10],
        [0.05, 1.00, 0.30],
        [0.10, 0.30, 1.00],
    ], dtype=float)
    cov = np.outer(vols, vols) * corr
    return assets, mu, cov


class TestOptimizationValidation:
    def test_valid_parameters_normalization(self):
        assets = ["gold", "BTC", "nvidia"]
        canon = validate_optimization_parameters(
            assets=assets,
            min_weight=0.0,
            max_weight=1.0,
            random_portfolios=1000,
            frontier_points=30,
            risk_free_rate=0.02,
        )
        assert canon == ["Gold", "Bitcoin", "NVIDIA"]

    def test_insufficient_assets_rejection(self):
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold"])
        assert exc.value.status_code == 422
        assert "requires at least 2 distinct assets" in exc.value.detail

        # Duplicate asset name resolving to 1 asset
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "gold"])
        assert exc.value.status_code == 422

    def test_unknown_asset_rejection(self):
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "UNKNOWN_COIN"])
        assert exc.value.status_code == 422
        assert "Unknown asset identifier" in exc.value.detail

    def test_invalid_weight_bounds_rejection(self):
        # Negative min_weight
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], min_weight=-0.1)
        assert exc.value.status_code == 422

        # Max weight > 1.0
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], max_weight=1.5)
        assert exc.value.status_code == 422

        # Min weight > Max weight
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], min_weight=0.6, max_weight=0.4)
        assert exc.value.status_code == 422

    def test_infeasible_simplex_bounds_rejection(self):
        # 3 assets with min_weight = 0.4 -> sum of min weights = 1.2 > 1.0
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(
                assets=["Gold", "Bitcoin", "NVIDIA"],
                min_weight=0.4,
                max_weight=1.0,
            )
        assert exc.value.status_code == 422
        assert "exceeds 100%" in exc.value.detail

        # 3 assets with max_weight = 0.3 -> sum of max weights = 0.9 < 1.0
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(
                assets=["Gold", "Bitcoin", "NVIDIA"],
                min_weight=0.0,
                max_weight=0.3,
            )
        assert exc.value.status_code == 422
        assert "cannot reach 100%" in exc.value.detail

    def test_invalid_counts_and_dates_rejection(self):
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], random_portfolios=50)
        assert exc.value.status_code == 422

        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], frontier_points=5)
        assert exc.value.status_code == 422

        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(assets=["Gold", "Bitcoin"], risk_free_rate=-0.01)
        assert exc.value.status_code == 422

        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(
                assets=["Gold", "Bitcoin"],
                start_date="2020-01-02",
                end_date="2020-01-01",
            )
        assert exc.value.status_code == 422

    def test_user_weights_validation(self):
        # Valid user weights
        uw = {"Gold": 0.5, "Bitcoin": 0.5}
        canon = validate_optimization_parameters(assets=["Gold", "Bitcoin"], user_weights=uw)
        assert canon == ["Gold", "Bitcoin"]

        # User weight sum != 1
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(
                assets=["Gold", "Bitcoin"],
                user_weights={"Gold": 0.4, "Bitcoin": 0.4},
            )
        assert exc.value.status_code == 422
        assert "must sum to 100%" in exc.value.detail

        # Asset not in universe
        with pytest.raises(HTTPException) as exc:
            validate_optimization_parameters(
                assets=["Gold", "Bitcoin"],
                user_weights={"Gold": 0.5, "NVIDIA": 0.5},
            )
        assert exc.value.status_code == 422


class TestPortfolioSolvers:
    def test_calculate_portfolio_stats(self, sample_market_inputs):
        _, mu, cov = sample_market_inputs
        w = np.array([0.4, 0.3, 0.3])
        exp_ret, var, vol, sharpe = calculate_portfolio_stats(w, mu, cov, risk_free_rate=0.02)

        expected_ret_val = 0.4 * 0.08 + 0.3 * 0.65 + 0.3 * 0.35
        assert exp_ret == pytest.approx(expected_ret_val, rel=1e-5)
        assert var > 0.0
        assert vol == pytest.approx(np.sqrt(var), rel=1e-6)
        assert sharpe == pytest.approx((exp_ret - 0.02) / vol, rel=1e-5)

    def test_equal_weight_optimization(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        res = optimize_equal_weight(assets, mu, cov, min_weight=0.0, max_weight=1.0, risk_free_rate=0.02)
        assert res["portfolio_type"] == "Equal Weight"
        for a in assets:
            assert res["weights"][a] == pytest.approx(1.0 / 3.0, rel=1e-4)
        assert res["expected_return"] == pytest.approx(float(np.mean(mu)), rel=1e-4)

        # Infeasible equal weight when min_weight > 1/3
        with pytest.raises(HTTPException) as exc:
            optimize_equal_weight(assets, mu, cov, min_weight=0.35, max_weight=1.0)
        assert exc.value.status_code == 422

    def test_min_volatility_gmv(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        gmv = optimize_min_volatility(assets, mu, cov, min_weight=0.0, max_weight=1.0, risk_free_rate=0.02)
        assert gmv["portfolio_type"] == "Minimum Volatility"

        # Weights sum to 1
        sum_w = sum(gmv["weights"].values())
        assert sum_w == pytest.approx(1.0, abs=1e-5)

        # All weights within bounds [0, 1]
        for w in gmv["weights"].values():
            assert 0.0 <= w <= 1.0

        # GMV volatility must be less than or equal to Equal Weight volatility
        eq = optimize_equal_weight(assets, mu, cov, 0.0, 1.0, 0.02)
        assert gmv["volatility"] <= eq["volatility"] + 1e-6

        # Gold should have highest weight because it has the lowest standalone volatility (15%)
        assert gmv["weights"]["Gold"] > gmv["weights"]["Bitcoin"]

    def test_max_sharpe_tangency(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        max_sh = optimize_max_sharpe(assets, mu, cov, min_weight=0.0, max_weight=1.0, risk_free_rate=0.02)
        assert max_sh["portfolio_type"] == "Maximum Sharpe"

        # Weights sum to 1
        sum_w = sum(max_sh["weights"].values())
        assert sum_w == pytest.approx(1.0, abs=1e-5)

        # Max Sharpe ratio must be greater than or equal to GMV Sharpe ratio and Equal Weight Sharpe ratio
        gmv = optimize_min_volatility(assets, mu, cov, 0.0, 1.0, 0.02)
        eq = optimize_equal_weight(assets, mu, cov, 0.0, 1.0, 0.02)
        assert max_sh["sharpe_ratio"] >= gmv["sharpe_ratio"] - 1e-5
        assert max_sh["sharpe_ratio"] >= eq["sharpe_ratio"] - 1e-5

    def test_bounds_enforcement_in_optimizer(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        min_w, max_w = 0.15, 0.60
        gmv = optimize_min_volatility(assets, mu, cov, min_weight=min_w, max_weight=max_w)
        for w in gmv["weights"].values():
            assert w >= min_w - 1e-5
            assert w <= max_w + 1e-5

        max_sh = optimize_max_sharpe(assets, mu, cov, min_weight=min_w, max_weight=max_w)
        for w in max_sh["weights"].values():
            assert w >= min_w - 1e-5
            assert w <= max_w + 1e-5

    def test_optimize_for_target_return(self, sample_market_inputs):
        _, mu, cov = sample_market_inputs
        target = 0.25
        opt_w = optimize_for_target_return(mu, cov, target_return=target, min_weight=0.0, max_weight=1.0)
        assert opt_w is not None
        assert np.sum(opt_w) == pytest.approx(1.0, abs=1e-5)
        achieved = float(np.dot(opt_w, mu))
        assert achieved == pytest.approx(target, abs=1e-3)

        # Infeasible target return (higher than max asset return)
        infeasible_w = optimize_for_target_return(mu, cov, target_return=1.50, min_weight=0.0, max_weight=1.0)
        assert infeasible_w is None


class TestEfficientFrontierAndRandomSampling:
    def test_efficient_frontier_generation(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        gmv = optimize_min_volatility(assets, mu, cov, 0.0, 1.0, 0.02)
        frontier = generate_efficient_frontier(
            asset_names=assets,
            expected_returns=mu,
            cov_matrix=cov,
            gmv_return=gmv["expected_return"],
            min_weight=0.0,
            max_weight=1.0,
            frontier_points=25,
            risk_free_rate=0.02,
        )

        assert len(frontier) >= 10
        # Frontier returns must be monotonically increasing
        for i in range(1, len(frontier)):
            assert frontier[i]["expected_return"] >= frontier[i - 1]["expected_return"] - 1e-5
            # Volatility must also increase as expected return increases beyond GMV
            assert frontier[i]["volatility"] >= frontier[i - 1]["volatility"] - 1e-5
            # All weights must sum to 1
            sum_w = sum(frontier[i]["weights"].values())
            assert sum_w == pytest.approx(1.0, abs=1e-4)

    def test_random_portfolios_sum_and_bounds(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        random_ports = generate_random_portfolios(
            asset_names=assets,
            expected_returns=mu,
            cov_matrix=cov,
            num_portfolios=1000,
            min_weight=0.05,
            max_weight=0.70,
            risk_free_rate=0.02,
            random_seed=42,
        )

        assert len(random_ports) == 1000
        for p in random_ports:
            sum_w = sum(p["weights"].values())
            assert sum_w == pytest.approx(1.0, abs=1e-5)
            for w in p["weights"].values():
                assert w >= 0.05 - 1e-5
                assert w <= 0.70 + 1e-5
            assert p["volatility"] > 0.0
            assert p["expected_return"] is not None

    def test_random_portfolios_seed_reproducibility(self, sample_market_inputs):
        assets, mu, cov = sample_market_inputs
        p1 = generate_random_portfolios(assets, mu, cov, num_portfolios=200, random_seed=42)
        p2 = generate_random_portfolios(assets, mu, cov, num_portfolios=200, random_seed=42)
        p3 = generate_random_portfolios(assets, mu, cov, num_portfolios=200, random_seed=99)

        # p1 and p2 must be identical
        for i in range(len(p1)):
            assert p1[i]["expected_return"] == pytest.approx(p2[i]["expected_return"], abs=1e-9)
            assert p1[i]["volatility"] == pytest.approx(p2[i]["volatility"], abs=1e-9)
            assert p1[i]["sharpe_ratio"] == pytest.approx(p2[i]["sharpe_ratio"], abs=1e-9)

        # p1 and p3 should differ
        assert p1[0]["expected_return"] != p3[0]["expected_return"] or p1[0]["volatility"] != p3[0]["volatility"]

    def test_zero_volatility_safety(self):
        assets = ["AssetA", "AssetB"]
        mu = np.array([0.05, 0.05])
        cov = np.zeros((2, 2))
        res = optimize_equal_weight(assets, mu, cov, 0.0, 1.0, 0.02)
        assert res["volatility"] == 0.0
        assert res["sharpe_ratio"] == 0.0
