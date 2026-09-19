"""
Unit Tests for Portfolio Analytics Engine (Mathematical correctness & edge cases).
"""
import pytest
import numpy as np
import pandas as pd
from fastapi import HTTPException

from backend.app.portfolio.validation import (
    validate_portfolio_weights,
    validate_portfolio_parameters,
)
from backend.app.portfolio.metrics import (
    calculate_portfolio_daily_returns,
    calculate_portfolio_cumulative_returns,
    calculate_portfolio_value_series,
    calculate_portfolio_performance_summary,
    calculate_performance_contributions,
)
from backend.app.portfolio.risk import calculate_portfolio_risk_contributions


def test_weights_sum_validation_exact_and_tolerance():
    # Valid exact sum
    w1 = {"Gold": 0.4, "Bitcoin": 0.3, "NVIDIA": 0.3}
    norm1 = validate_portfolio_weights(w1)
    assert sum(norm1.values()) == pytest.approx(1.0, 1e-4)

    # Valid floating point sum
    w2 = {"Gold": 0.33333, "Bitcoin": 0.33333, "NVIDIA": 0.33334}
    norm2 = validate_portfolio_weights(w2)
    assert sum(norm2.values()) == pytest.approx(1.0, 1e-4)

    # Invalid sum (< 1.0)
    w_under = {"Gold": 0.4, "NVIDIA": 0.4}
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_weights(w_under)
    assert exc.value.status_code == 422
    assert "must sum to 100%" in exc.value.detail

    # Invalid sum (> 1.0)
    w_over = {"Gold": 0.6, "Bitcoin": 0.5}
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_weights(w_over)
    assert exc.value.status_code == 422


def test_negative_weight_rejection():
    w = {"Gold": 0.8, "Bitcoin": -0.2}
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_weights(w)
    assert exc.value.status_code == 422
    assert "cannot be negative" in exc.value.detail


def test_weight_greater_than_one_rejection():
    w = {"Gold": 1.5}
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_weights(w)
    assert exc.value.status_code == 422
    assert "cannot exceed 100%" in exc.value.detail


def test_validate_portfolio_parameters():
    # Valid parameters
    validate_portfolio_parameters(100000.0, 0.02, "2017-01-01", "2017-12-31")

    # Invalid capital (<= 0)
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_parameters(-100.0, 0.02)
    assert exc.value.status_code == 422
    assert "Initial capital must be strictly positive" in exc.value.detail

    # Invalid risk-free rate (< 0)
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_parameters(1000.0, -0.05)
    assert exc.value.status_code == 422
    assert "Risk-free rate cannot be negative" in exc.value.detail

    # Invalid date range (start > end)
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_parameters(1000.0, 0.02, "2020-01-02", "2020-01-01")
    assert exc.value.status_code == 422
    assert "Start date" in exc.value.detail


def test_unknown_asset_rejection():
    w = {"FakeCoin": 1.0}
    with pytest.raises(HTTPException) as exc:
        validate_portfolio_weights(w)
    assert exc.value.status_code == 422
    assert "Unknown asset" in exc.value.detail


def test_deterministic_daily_weighted_returns():
    # Asset A: +10% on day 1, +5% on day 2
    # Asset B: -10% on day 1, +5% on day 2
    df = pd.DataFrame({
        "date": ["2020-01-01", "2020-01-02"],
        "Gold": [0.10, 0.05],
        "NVIDIA": [-0.10, 0.05],
    })
    weights = {"Gold": 0.5, "NVIDIA": 0.5}

    port_ret = calculate_portfolio_daily_returns(df, weights)
    # Day 1: 0.5 * 0.10 + 0.5 * (-0.10) = 0.0
    # Day 2: 0.5 * 0.05 + 0.5 * 0.05 = 0.05
    assert port_ret.iloc[0] == pytest.approx(0.0)
    assert port_ret.iloc[1] == pytest.approx(0.05)


def test_cumulative_returns_and_portfolio_value():
    daily_ret = pd.Series([0.10, -0.05, 0.02])
    cum_ret = calculate_portfolio_cumulative_returns(daily_ret)

    # Expected:
    # t1: 1.10 - 1 = 0.10
    # t2: 1.10 * 0.95 - 1 = 1.045 - 1 = 0.045
    # t3: 1.045 * 1.02 - 1 = 1.0659 - 1 = 0.0659
    assert cum_ret.iloc[0] == pytest.approx(0.10)
    assert cum_ret.iloc[1] == pytest.approx(0.045)
    assert cum_ret.iloc[2] == pytest.approx(0.0659)

    initial_capital = 100000.0
    val_series = calculate_portfolio_value_series(cum_ret, initial_capital)
    assert val_series.iloc[0] == pytest.approx(110000.0)
    assert val_series.iloc[1] == pytest.approx(104500.0)
    assert val_series.iloc[2] == pytest.approx(106590.0)


def test_portfolio_performance_summary_metrics():
    # 252 days of constant 0.001 (0.1%) daily return
    daily_ret = pd.Series([0.001] * 252)
    cum_ret = calculate_portfolio_cumulative_returns(daily_ret)

    summary = calculate_portfolio_performance_summary(
        portfolio_daily_returns=daily_ret,
        cumulative_returns=cum_ret,
        initial_capital=100000.0,
        risk_free_rate=0.02,
    )

    expected_total_return = (1.001 ** 252) - 1.0
    assert summary["total_return"] == pytest.approx(expected_total_return, rel=1e-3)
    assert summary["observations"] == 252
    assert summary["final_value"] == pytest.approx(100000.0 * (1.0 + expected_total_return), rel=1e-2)
    assert summary["maximum_drawdown"] == pytest.approx(0.0)  # Monotonic increase


def test_performance_contributions():
    df = pd.DataFrame({
        "date": ["2020-01-01", "2020-01-02"],
        "Gold": [0.02, 0.01],    # Total return: (1.02)(1.01)-1 = 0.0302
        "NVIDIA": [0.05, 0.05],  # Total return: (1.05)(1.05)-1 = 0.1025
    })
    weights = {"Gold": 0.6, "NVIDIA": 0.4}

    contribs = calculate_performance_contributions(df, weights)
    assert len(contribs) == 2

    gold_c = next(c for c in contribs if c["asset"] == "Gold")
    nvda_c = next(c for c in contribs if c["asset"] == "NVIDIA")

    assert gold_c["total_return"] == pytest.approx(0.0302, rel=1e-3)
    assert gold_c["weighted_contribution"] == pytest.approx(0.6 * 0.0302, rel=1e-3)

    assert nvda_c["total_return"] == pytest.approx(0.1025, rel=1e-3)
    assert nvda_c["weighted_contribution"] == pytest.approx(0.4 * 0.1025, rel=1e-3)

    total_weighted = gold_c["weighted_contribution"] + nvda_c["weighted_contribution"]
    assert (gold_c["contribution_percentage"] + nvda_c["contribution_percentage"]) == pytest.approx(1.0, 1e-4)


def test_risk_contributions_euler_decomposition():
    np.random.seed(42)
    n_days = 252
    # Generate correlated synthetic return series
    r_gold = np.random.normal(0.0002, 0.01, n_days)
    r_nvda = np.random.normal(0.0010, 0.025, n_days)

    df = pd.DataFrame({
        "date": pd.date_range("2021-01-01", periods=n_days).strftime("%Y-%m-%d"),
        "Gold": r_gold,
        "NVIDIA": r_nvda,
    })
    weights = {"Gold": 0.4, "NVIDIA": 0.6}

    risk_result = calculate_portfolio_risk_contributions(df, weights, annualization_factor=252)

    port_vol = risk_result["portfolio_volatility"]
    assert port_vol > 0.0

    contribs = risk_result["contributions"]
    assert len(contribs) == 2

    # Euler's theorem: sum(CCR_i) must equal total portfolio volatility
    sum_ccr = sum(c["component_risk_contribution"] for c in contribs)
    assert sum_ccr == pytest.approx(port_vol, rel=1e-4)

    # Percentage risk contributions must sum to 100%
    sum_pct_cr = sum(c["percentage_risk_contribution"] for c in contribs)
    assert sum_pct_cr == pytest.approx(1.0, rel=1e-4)


def test_single_asset_portfolio():
    # 100% Gold portfolio
    np.random.seed(123)
    r_gold = np.random.normal(0.0005, 0.012, 100)
    df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=100).strftime("%Y-%m-%d"),
        "Gold": r_gold,
    })
    weights = {"Gold": 1.0}

    port_ret = calculate_portfolio_daily_returns(df, weights)
    np.testing.assert_array_almost_equal(port_ret.values, r_gold)

    risk_result = calculate_portfolio_risk_contributions(df, weights, annualization_factor=252)
    gold_ann_vol = float(np.std(r_gold, ddof=1) * np.sqrt(252))

    assert risk_result["portfolio_volatility"] == pytest.approx(gold_ann_vol, rel=1e-3)
    contrib = risk_result["contributions"][0]
    assert contrib["percentage_risk_contribution"] == pytest.approx(1.0, 1e-4)
