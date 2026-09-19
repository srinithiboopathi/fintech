"""
Mathematical Unit Tests for QUANTLAB Quantitative Indicator and Performance Engine.
Validates all formulas against deterministic manual benchmarks, warmups, and look-ahead bias guards.
"""
import pytest
import numpy as np
import pandas as pd

from backend.app.quant.indicators import calculate_sma, calculate_ema
from backend.app.quant.returns import calculate_daily_returns, calculate_cumulative_returns
from backend.app.quant.volatility import (
    calculate_rolling_volatility,
    calculate_annualized_volatility,
    calculate_rolling_annualized_volatility,
    get_annualization_factor,
)
from backend.app.quant.sharpe import calculate_sharpe_ratio, calculate_rolling_sharpe
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown
from backend.app.quant.rolling import calculate_rolling_returns, calculate_rolling_metrics


class TestSMA:
    def test_sma_manual_benchmark(self):
        prices = pd.Series([10.0, 20.0, 30.0])
        sma3 = calculate_sma(prices, period=3)
        assert np.isnan(sma3.iloc[0])
        assert np.isnan(sma3.iloc[1])
        assert pytest.approx(sma3.iloc[2], rel=1e-6) == 20.0

    def test_sma_warmup_periods(self):
        prices = pd.Series([100.0 + i for i in range(10)])
        period = 5
        sma = calculate_sma(prices, period=period)
        assert sma.iloc[:period - 1].isna().all()
        assert not sma.iloc[period - 1:].isna().any()
        # Period 5 on [100, 101, 102, 103, 104] -> mean is 102.0
        assert pytest.approx(sma.iloc[4], rel=1e-6) == 102.0

    def test_sma_invalid_period(self):
        prices = pd.Series([10.0, 20.0])
        with pytest.raises(ValueError):
            calculate_sma(prices, period=0)
        with pytest.raises(ValueError):
            calculate_sma(prices, period=-5)


class TestEMA:
    def test_ema_deterministic_calculation(self):
        # prices: [10.0, 12.0, 14.0], period = 2 -> alpha = 2 / (2 + 1) = 2/3
        # EMA_0 = 10.0
        # EMA_1 = (2/3) * 12.0 + (1/3) * 10.0 = 8.0 + 3.333333 = 11.333333
        # EMA_2 = (2/3) * 14.0 + (1/3) * 11.333333 = 9.333333 + 3.777778 = 13.111111
        prices = pd.Series([10.0, 12.0, 14.0])
        ema2 = calculate_ema(prices, period=2)
        assert pytest.approx(ema2.iloc[0], rel=1e-5) == 10.0
        assert pytest.approx(ema2.iloc[1], rel=1e-5) == 11.333333
        assert pytest.approx(ema2.iloc[2], rel=1e-5) == 13.111111

    def test_ema_invalid_period(self):
        prices = pd.Series([10.0, 20.0])
        with pytest.raises(ValueError):
            calculate_ema(prices, period=0)


class TestReturns:
    def test_daily_returns_manual(self):
        prices = pd.Series([10.0, 12.0, 15.0])
        returns = calculate_daily_returns(prices)
        assert np.isnan(returns.iloc[0])
        assert pytest.approx(returns.iloc[1], rel=1e-6) == 0.20  # (12 - 10) / 10
        assert pytest.approx(returns.iloc[2], rel=1e-6) == 0.25  # (15 - 12) / 12

    def test_cumulative_returns_manual(self):
        # Returns: [NaN, 0.20, 0.25]
        # Wealth: [1.0, 1.20, 1.20 * 1.25 = 1.50]
        # Cumulative return: [0.0, 0.20, 0.50]
        returns = pd.Series([np.nan, 0.20, 0.25])
        cum_ret = calculate_cumulative_returns(returns)
        assert pytest.approx(cum_ret.iloc[0], rel=1e-6) == 0.0
        assert pytest.approx(cum_ret.iloc[1], rel=1e-6) == 0.20
        assert pytest.approx(cum_ret.iloc[2], rel=1e-6) == 0.50


class TestVolatility:
    def test_annualization_factors(self):
        assert get_annualization_factor("Gold") == 252
        assert get_annualization_factor("NVIDIA") == 252
        assert get_annualization_factor("Bitcoin") == 365
        assert get_annualization_factor("BTC") == 365
        assert get_annualization_factor("btc-usd") == 365

    def test_rolling_and_annualized_volatility(self):
        returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.025, 0.005])
        window = 3
        rolling_vol = calculate_rolling_volatility(returns, window=window)
        assert rolling_vol.iloc[:window - 1].isna().all()
        # Window 3 for items [0.01, -0.02, 0.015]
        expected_std = float(returns.iloc[:3].std(ddof=1))
        assert pytest.approx(rolling_vol.iloc[2], rel=1e-6) == expected_std

        # Annualized volatility
        ann_vol = calculate_annualized_volatility(returns, annualization_factor=252)
        total_std = float(returns.std(ddof=1))
        assert pytest.approx(ann_vol, rel=1e-6) == total_std * np.sqrt(252)


class TestSharpeRatio:
    def test_sharpe_manual_benchmark(self):
        # Returns with known mean and std
        returns = pd.Series([0.01, 0.02, 0.03])
        # mean = 0.02, std(ddof=1) = 0.01
        # risk_free_rate = 0.0 -> daily_rf = 0.0
        # Sharpe = (0.02 / 0.01) * sqrt(252) = 2.0 * sqrt(252)
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate_annual=0.0, annualization_factor=252)
        expected = 2.0 * np.sqrt(252)
        assert pytest.approx(sharpe, rel=1e-6) == expected

    def test_sharpe_with_risk_free_rate(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        rf_annual = 0.0252  # daily rf = 0.0252 / 252 = 0.0001
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate_annual=rf_annual, annualization_factor=252)
        # excess returns: [0.01 - 0.0001, 0.02 - 0.0001, 0.03 - 0.0001]
        # mean excess = 0.02 - 0.0001 = 0.0199, std = 0.01
        expected = (0.0199 / 0.01) * np.sqrt(252)
        assert pytest.approx(sharpe, rel=1e-6) == expected

    def test_zero_volatility_sharpe_protection(self):
        # Constant returns have standard deviation = 0.0
        flat_returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        sharpe = calculate_sharpe_ratio(flat_returns, risk_free_rate_annual=0.0)
        assert sharpe is None  # Must safely return None without crash or division by zero


class TestDrawdown:
    def test_max_drawdown_benchmark(self):
        # Prices: 100 -> 120 -> 90 -> 110 -> 80
        # Peak:   100 -> 120 -> 120 -> 120 -> 120
        # DD:     0.0 -> 0.0 -> -0.25 -> -0.0833 -> -0.3333
        # MDD:    -0.333333 (-33.33%)
        prices = pd.Series([100.0, 120.0, 90.0, 110.0, 80.0])
        dd_series = calculate_drawdown_series(prices)
        assert pytest.approx(dd_series.iloc[0], rel=1e-6) == 0.0
        assert pytest.approx(dd_series.iloc[1], rel=1e-6) == 0.0
        assert pytest.approx(dd_series.iloc[2], rel=1e-6) == -0.25
        assert pytest.approx(dd_series.iloc[4], rel=1e-6) == -0.3333333

        mdd = calculate_max_drawdown(dd_series)
        assert pytest.approx(mdd, rel=1e-6) == -0.3333333


class TestRollingPerformance:
    def test_rolling_returns(self):
        prices = pd.Series([100.0, 110.0, 120.0, 130.0])
        rolling2 = calculate_rolling_returns(prices, window=2)
        assert np.isnan(rolling2.iloc[0])
        assert np.isnan(rolling2.iloc[1])
        assert pytest.approx(rolling2.iloc[2], rel=1e-6) == 0.20  # (120 - 100) / 100
        assert pytest.approx(rolling2.iloc[3], rel=1e-6) == 0.18181818  # (130 - 110) / 110


class TestLookAheadBiasPrevention:
    """
    Strict validation to ensure that any metric at time t depends EXCLUSIVELY
    on observations at or prior to time t.
    """
    def test_sma_lookahead_independence(self):
        base_prices = [100.0 + i for i in range(20)]
        df1 = pd.Series(base_prices)
        
        # Calculate SMA on series 1
        sma1 = calculate_sma(df1, period=5)
        val_at_10_original = sma1.iloc[10]

        # Mutate future prices after index 10
        mutated_prices = list(base_prices)
        for j in range(11, 20):
            mutated_prices[j] = 999999.0  # extreme future perturbation

        df2 = pd.Series(mutated_prices)
        sma2 = calculate_sma(df2, period=5)
        val_at_10_mutated = sma2.iloc[10]

        # Value at index 10 MUST be identical despite future perturbations
        assert pytest.approx(val_at_10_original, rel=1e-9) == val_at_10_mutated

    def test_ema_lookahead_independence(self):
        base_prices = [50.0 + 2 * i for i in range(20)]
        df1 = pd.Series(base_prices)
        ema1 = calculate_ema(df1, period=10)
        val_at_10_original = ema1.iloc[10]

        # Mutate future
        mutated_prices = list(base_prices)
        for j in range(11, 20):
            mutated_prices[j] = -1000.0

        df2 = pd.Series(mutated_prices)
        ema2 = calculate_ema(df2, period=10)
        val_at_10_mutated = ema2.iloc[10]

        assert pytest.approx(val_at_10_original, rel=1e-9) == val_at_10_mutated

    def test_returns_and_volatility_lookahead_independence(self):
        base_prices = pd.Series([100.0, 102.0, 101.0, 105.0, 104.0, 108.0, 110.0, 109.0, 112.0, 115.0])
        returns1 = calculate_daily_returns(base_prices)
        vol1 = calculate_rolling_volatility(returns1, window=3)
        vol_at_5_orig = vol1.iloc[5]

        # Mutate future prices from index 6 onwards
        mutated_prices = base_prices.copy()
        mutated_prices.iloc[6:] = 5000.0
        returns2 = calculate_daily_returns(mutated_prices)
        vol2 = calculate_rolling_volatility(returns2, window=3)
        vol_at_5_mutated = vol2.iloc[5]

        assert pytest.approx(vol_at_5_orig, rel=1e-9) == vol_at_5_mutated
