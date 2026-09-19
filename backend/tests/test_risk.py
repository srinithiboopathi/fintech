"""
Unit tests for returns, volatility, Sharpe ratio, drawdown, and rolling metrics.
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.quant.returns import (
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_cumulative_returns_from_prices,
)
from backend.app.quant.volatility import calculate_annualized_volatility
from backend.app.quant.sharpe import calculate_sharpe_ratio
from backend.app.quant.drawdown import (
    calculate_peak_value,
    calculate_drawdown,
    calculate_max_drawdown,
)
from backend.app.quant.rolling import (
    calculate_rolling_volatility,
    calculate_rolling_correlation,
)


class TestReturns:
    def test_daily_returns(self):
        prices = pd.Series([100.0, 105.0, 99.75])
        returns = calculate_daily_returns(prices)
        assert np.isnan(returns.iloc[0])
        assert returns.iloc[1] == pytest.approx(0.05)
        assert returns.iloc[2] == pytest.approx(-0.05)

    def test_daily_returns_fill_zero(self):
        prices = pd.Series([100.0, 110.0])
        returns = calculate_daily_returns(prices, fill_zero=True)
        assert returns.iloc[0] == pytest.approx(0.0)
        assert returns.iloc[1] == pytest.approx(0.10)

    def test_cumulative_returns_compounded(self):
        daily_ret = pd.Series([np.nan, 0.05, -0.05])
        cum_ret = calculate_cumulative_returns(daily_ret, compound=True)
        assert cum_ret.iloc[0] == pytest.approx(0.0)
        assert cum_ret.iloc[1] == pytest.approx(0.05)
        # (1 + 0.05) * (1 - 0.05) - 1 = -0.0025
        assert cum_ret.iloc[2] == pytest.approx(-0.0025)

    def test_cumulative_returns_from_prices(self):
        prices = pd.Series([100.0, 120.0, 90.0])
        cum_ret = calculate_cumulative_returns_from_prices(prices)
        assert cum_ret.iloc[0] == pytest.approx(0.0)
        assert cum_ret.iloc[1] == pytest.approx(0.20)
        assert cum_ret.iloc[2] == pytest.approx(-0.10)

    def test_empty_returns(self):
        empty = pd.Series([], dtype=float)
        assert calculate_daily_returns(empty).empty
        assert calculate_cumulative_returns(empty).empty
        assert calculate_cumulative_returns_from_prices(empty).empty


class TestVolatility:
    def test_annualized_volatility(self):
        returns = pd.Series([0.01, -0.01, 0.02, -0.01, 0.01])
        daily_std = returns.std(ddof=1)
        expected_vol = float(daily_std * np.sqrt(252))

        calc_vol = calculate_annualized_volatility(returns, trading_days=252)
        assert calc_vol == pytest.approx(expected_vol)

    def test_volatility_insufficient_data(self):
        assert calculate_annualized_volatility(pd.Series([0.05])) == 0.0
        assert calculate_annualized_volatility(pd.Series([], dtype=float)) == 0.0


class TestSharpeRatio:
    def test_sharpe_deterministic(self):
        returns = pd.Series([0.001, 0.002, 0.0015, 0.0018, 0.0012])
        rf = 0.02
        daily_rf = rf / 252
        excess = returns - daily_rf
        expected_sharpe = float((excess.mean() / excess.std(ddof=1)) * np.sqrt(252))

        calc_sharpe = calculate_sharpe_ratio(returns, risk_free_rate=rf, trading_days=252)
        assert calc_sharpe == pytest.approx(expected_sharpe)

    def test_sharpe_zero_variance(self):
        flat_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        assert calculate_sharpe_ratio(flat_returns) == 0.0

    def test_sharpe_empty(self):
        assert calculate_sharpe_ratio(pd.Series([], dtype=float)) == 0.0


class TestDrawdown:
    def test_drawdown_metrics(self):
        prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0])
        peaks = calculate_peak_value(prices)
        assert peaks.tolist() == [100.0, 120.0, 120.0, 120.0, 120.0]

        dd = calculate_drawdown(prices)
        assert dd.iloc[0] == pytest.approx(0.0)
        assert dd.iloc[1] == pytest.approx(0.0)
        assert dd.iloc[2] == pytest.approx((90.0 - 120.0) / 120.0)  # -0.25
        assert dd.iloc[3] == pytest.approx((110.0 - 120.0) / 120.0) # -0.08333
        assert dd.iloc[4] == pytest.approx((80.0 - 120.0) / 120.0)  # -0.33333

        max_dd = calculate_max_drawdown(prices)
        assert max_dd == pytest.approx(-1.0 / 3.0)

    def test_empty_drawdown(self):
        empty = pd.Series([], dtype=float)
        assert calculate_peak_value(empty).empty
        assert calculate_drawdown(empty).empty
        assert calculate_max_drawdown(empty) == 0.0


class TestRolling:
    def test_rolling_volatility(self):
        returns = pd.Series([0.01, -0.01, 0.02, -0.01, 0.01, 0.005])
        roll_vol = calculate_rolling_volatility(returns, window=3, trading_days=252)

        assert np.isnan(roll_vol.iloc[0])
        assert np.isnan(roll_vol.iloc[1])
        expected_window_3 = returns.iloc[:3].std(ddof=1) * np.sqrt(252)
        assert roll_vol.iloc[2] == pytest.approx(expected_window_3)

    def test_rolling_correlation_perfect(self):
        idx = pd.date_range("2024-01-01", periods=10, freq="D")
        s1 = pd.Series(np.arange(1.0, 11.0), index=idx)
        s2 = pd.Series(np.arange(1.0, 11.0) * 2.5, index=idx)

        roll_corr = calculate_rolling_correlation(s1, s2, window=5)
        assert np.isnan(roll_corr.iloc[3])
        # Perfect linear correlation must be 1.0
        assert roll_corr.iloc[4] == pytest.approx(1.0)
        assert roll_corr.iloc[9] == pytest.approx(1.0)
