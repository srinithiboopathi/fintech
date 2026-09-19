"""
Comprehensive Unit Tests for Quantitative Strategy Mathematics and Signal Generation (Phase 6).
Covers deterministic crossing logic, parameter validation, warm-up safety, and look-ahead bias prevention.
"""
import pytest
import numpy as np
import pandas as pd

from backend.app.strategies.enums import SignalType, StrategyType
from backend.app.strategies.validation import (
    validate_sma_parameters,
    validate_ema_parameters,
    validate_momentum_parameters,
    validate_mean_reversion_parameters,
    validate_strategy_name,
)
from backend.app.strategies.sma_crossover import calculate_sma_crossover_signals
from backend.app.strategies.ema_trend import calculate_ema_trend_signals
from backend.app.strategies.momentum import calculate_momentum_signals
from backend.app.strategies.mean_reversion import calculate_mean_reversion_signals
from backend.app.data.loader import DataLoader


class TestStrategyValidation:
    """Test parameter validation rules and boundary conditions."""

    def test_sma_validation(self):
        # Valid
        validate_sma_parameters(fast_period=10, slow_period=30)

        # Fast >= Slow
        with pytest.raises(ValueError, match="strictly less than"):
            validate_sma_parameters(fast_period=50, slow_period=20)

        with pytest.raises(ValueError, match="strictly less than"):
            validate_sma_parameters(fast_period=20, slow_period=20)

        # Below minimum allowed
        with pytest.raises(ValueError, match="greater than or equal to 2"):
            validate_sma_parameters(fast_period=1, slow_period=20)

    def test_ema_validation(self):
        # Valid
        validate_ema_parameters(short_period=12, long_period=26)

        # Short >= Long
        with pytest.raises(ValueError, match="strictly less than"):
            validate_ema_parameters(short_period=30, long_period=30)

        with pytest.raises(ValueError, match="strictly less than"):
            validate_ema_parameters(short_period=40, long_period=20)

        with pytest.raises(ValueError, match="greater than or equal to 2"):
            validate_ema_parameters(short_period=1, long_period=20)

    def test_momentum_validation(self):
        validate_momentum_parameters(lookback=1)
        validate_momentum_parameters(lookback=20)

        with pytest.raises(ValueError, match="greater than or equal to 1"):
            validate_momentum_parameters(lookback=0)

        with pytest.raises(ValueError):
            validate_momentum_parameters(lookback=-5)

    def test_mean_reversion_validation(self):
        validate_mean_reversion_parameters(window=20, threshold=0.02)

        with pytest.raises(ValueError, match="greater than or equal to 2"):
            validate_mean_reversion_parameters(window=1, threshold=0.02)

        with pytest.raises(ValueError, match="greater than 0"):
            validate_mean_reversion_parameters(window=20, threshold=0.0)

        with pytest.raises(ValueError, match="greater than 0"):
            validate_mean_reversion_parameters(window=20, threshold=-0.05)

    def test_strategy_name_validation(self):
        assert validate_strategy_name("sma_crossover") == StrategyType.SMA_CROSSOVER
        assert validate_strategy_name("SMA-CROSSOVER") == StrategyType.SMA_CROSSOVER
        assert validate_strategy_name("ema_trend") == StrategyType.EMA_TREND
        assert validate_strategy_name("momentum") == StrategyType.MOMENTUM
        assert validate_strategy_name("mean_reversion") == StrategyType.MEAN_REVERSION
        assert validate_strategy_name("MEAN-REVERSION") == StrategyType.MEAN_REVERSION

        with pytest.raises(ValueError, match="Unknown strategy"):
            validate_strategy_name("random_strategy")


class TestSMACrossoverStrategy:
    """Test SMA Crossover crossing events, warm-up behavior, and signal persistence."""

    def test_known_crossover_events(self):
        # Create a series where fast crosses above slow, stays above, then crosses below
        # Fast=3, Slow=5
        # Index 0..4: warmup for slow SMA
        # Index 5+: slow SMA active
        prices = pd.Series([
            10.0, 10.0, 10.0, 10.0, 10.0,  # Slow=10, Fast=10
            12.0, 14.0, 16.0,              # Prices jump up -> Fast jumps above Slow -> BUY at index 5
            16.0, 16.0,                    # Stays above -> HOLD (no duplicate BUY)
            8.0, 6.0, 4.0                  # Prices plunge -> Fast drops below Slow -> SELL
        ])
        df = calculate_sma_crossover_signals(prices, fast_period=3, slow_period=5)

        assert "close" in df.columns
        assert "fast_sma" in df.columns
        assert "slow_sma" in df.columns
        assert "signal" in df.columns

        # Warmup bars (0..3) must be HOLD with slow_sma NaN
        for i in range(4):
            assert pd.isna(df["slow_sma"].iloc[i])
            assert df["signal"].iloc[i] == SignalType.HOLD.value

        # At index 4: fast=10, slow=10 (first full slow SMA bar)
        assert df["signal"].iloc[4] == SignalType.HOLD.value

        # At index 5: price=12, fast=(10+10+12)/3=10.67, slow=(10+10+10+10+12)/5=10.4 -> fast crosses above slow -> BUY
        assert df["signal"].iloc[5] == SignalType.BUY.value

        # At index 6, 7, 8: fast continues to stay above slow -> MUST BE HOLD (no repeated BUY)
        assert df["signal"].iloc[6] == SignalType.HOLD.value
        assert df["signal"].iloc[7] == SignalType.HOLD.value
        assert df["signal"].iloc[8] == SignalType.HOLD.value

        # When prices plunge down, fast crosses below slow -> SELL
        sell_signals = df[df["signal"] == SignalType.SELL.value]
        assert len(sell_signals) >= 1

    def test_empty_series(self):
        empty = pd.Series([], dtype=float)
        df = calculate_sma_crossover_signals(empty, fast_period=20, slow_period=50)
        assert df.empty
        assert list(df.columns) == ["close", "fast_sma", "slow_sma", "signal"]


class TestEMATrendStrategy:
    """Test EMA Trend crossing events and warm-up behavior."""

    def test_ema_crossover_and_no_repeated_signals(self):
        # Generate 100 prices with a clear upward trend shift then downward trend shift
        np.random.seed(42)
        base = np.full(50, 100.0)
        uptrend = np.linspace(100.0, 150.0, 30)
        downtrend = np.linspace(150.0, 80.0, 30)
        prices = pd.Series(np.concatenate([base, uptrend, downtrend]))

        df = calculate_ema_trend_signals(prices, short_period=10, long_period=30)

        # Check warm-up
        for i in range(30):
            assert df["signal"].iloc[i] == SignalType.HOLD.value

        # Check signals exist
        buy_indices = df.index[df["signal"] == SignalType.BUY.value].tolist()
        sell_indices = df.index[df["signal"] == SignalType.SELL.value].tolist()

        assert len(buy_indices) >= 1
        assert len(sell_indices) >= 1

        # Check crossing rule: on the bar following BUY, if short > long, signal must be HOLD
        for buy_idx in buy_indices:
            if buy_idx + 1 < len(df) and df["short_ema"].iloc[buy_idx + 1] > df["long_ema"].iloc[buy_idx + 1]:
                assert df["signal"].iloc[buy_idx + 1] == SignalType.HOLD.value


class TestMomentumStrategy:
    """Test Momentum indicator calculation and zero-crossing triggers."""

    def test_momentum_math_and_signals(self):
        # Lookback=3
        # Prices: [100, 100, 100, 105, 110, 110, 90, 80]
        # t=0..2: warmup -> NaN
        # t=3: 105/100 - 1 = +0.05 -> BUY (crossing from NaN/0 to positive)
        # t=4: 110/100 - 1 = +0.10 -> HOLD (remains positive, no repeated BUY)
        # t=5: 110/100 - 1 = +0.10 -> HOLD
        # t=6: 90/105 - 1 = -0.1428 -> SELL (crosses to negative)
        # t=7: 80/110 - 1 = -0.2727 -> HOLD (remains negative)
        prices = pd.Series([100.0, 100.0, 100.0, 105.0, 110.0, 110.0, 90.0, 80.0])
        df = calculate_momentum_signals(prices, lookback=3)

        # Warm-up check
        assert pd.isna(df["momentum"].iloc[0])
        assert pd.isna(df["momentum"].iloc[1])
        assert pd.isna(df["momentum"].iloc[2])
        assert df["signal"].iloc[0] == SignalType.HOLD.value
        assert df["signal"].iloc[1] == SignalType.HOLD.value
        assert df["signal"].iloc[2] == SignalType.HOLD.value

        # First momentum value at index 3: 0.05
        assert np.isclose(df["momentum"].iloc[3], 0.05)
        assert df["signal"].iloc[3] == SignalType.BUY.value

        # Index 4: momentum is 0.10 > 0, but previous was also > 0 -> HOLD
        assert np.isclose(df["momentum"].iloc[4], 0.10)
        assert df["signal"].iloc[4] == SignalType.HOLD.value

        # Index 6: crosses to negative -> SELL
        assert df["momentum"].iloc[6] < 0.0
        assert df["signal"].iloc[6] == SignalType.SELL.value

        # Index 7: remains negative -> HOLD
        assert df["momentum"].iloc[7] < 0.0
        assert df["signal"].iloc[7] == SignalType.HOLD.value


class TestMeanReversionStrategy:
    """Test Mean Reversion threshold boundaries and signal generation."""

    def test_mean_reversion_oversold_overbought(self):
        # Window=4, Threshold=0.05 (5%)
        # Base price 100:
        # [100, 100, 100, 100] -> MA=100, dev=0 -> HOLD
        # [..., 90] -> MA = (100+100+100+90)/4 = 97.5, dev = (90 - 97.5)/97.5 = -0.0769 <= -0.05 -> BUY
        # [..., 110] -> dev >= 0.05 -> SELL
        # [..., 99] -> dev = (99 - 100)/100 = -0.01 -> within [-0.05, 0.05] -> HOLD
        prices = pd.Series([100.0, 100.0, 100.0, 100.0, 90.0, 110.0, 100.0])
        df = calculate_mean_reversion_signals(prices, window=4, threshold=0.05)

        # Warmup (0..2)
        assert pd.isna(df["moving_average"].iloc[0])
        assert pd.isna(df["deviation"].iloc[0])
        assert df["signal"].iloc[0] == SignalType.HOLD.value

        # Index 3: MA=100, dev=0.0 -> HOLD
        assert np.isclose(df["moving_average"].iloc[3], 100.0)
        assert np.isclose(df["deviation"].iloc[3], 0.0)
        assert df["signal"].iloc[3] == SignalType.HOLD.value

        # Index 4: price=90, dev = (90 - 97.5) / 97.5 = -0.07692 <= -0.05 -> BUY
        assert df["deviation"].iloc[4] <= -0.05
        assert df["signal"].iloc[4] == SignalType.BUY.value

        # Index 5: price=110, MA=(100+100+90+110)/4 = 100.0, dev = (110-100)/100 = 0.10 >= 0.05 -> SELL
        assert df["deviation"].iloc[5] >= 0.05
        assert df["signal"].iloc[5] == SignalType.SELL.value


from backend.app.services.market_service import market_service


class TestLookAheadBiasPrevention:
    """
    CRITICAL: Validates that strategy signals at time t strictly depend ONLY on prices <= t.
    Modifying future prices (> t) with extreme perturbations must have ZERO effect on signals at <= t.
    """

    @pytest.fixture(autouse=True)
    def setup_real_data(self):
        self.gold_df = market_service._get_dataset("Gold").sort_values("date").reset_index(drop=True)
        self.btc_df = market_service._get_dataset("Bitcoin").sort_values("date").reset_index(drop=True)
        self.nvda_df = market_service._get_dataset("NVIDIA").sort_values("date").reset_index(drop=True)


    def test_sma_lookahead_bias(self):
        prices = self.nvda_df["close"].copy()
        t = 200  # Evaluate cutoff point

        # Original calculation
        orig_res = calculate_sma_crossover_signals(prices, fast_period=20, slow_period=50)

        # Perturb all future prices (> t) drastically
        perturbed_prices = prices.copy()
        perturbed_prices.iloc[t + 1:] = perturbed_prices.iloc[t + 1:] * 50.0 + 10000.0

        new_res = calculate_sma_crossover_signals(perturbed_prices, fast_period=20, slow_period=50)

        # Assert signals and indicators up to and including t are strictly identical
        pd.testing.assert_series_equal(orig_res["signal"].iloc[:t + 1], new_res["signal"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["fast_sma"].iloc[:t + 1], new_res["fast_sma"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["slow_sma"].iloc[:t + 1], new_res["slow_sma"].iloc[:t + 1])

    def test_ema_lookahead_bias(self):
        prices = self.gold_df["close"].copy()
        t = 150

        orig_res = calculate_ema_trend_signals(prices, short_period=20, long_period=50)

        perturbed_prices = prices.copy()
        perturbed_prices.iloc[t + 1:] = 0.01  # Extreme drop

        new_res = calculate_ema_trend_signals(perturbed_prices, short_period=20, long_period=50)

        pd.testing.assert_series_equal(orig_res["signal"].iloc[:t + 1], new_res["signal"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["short_ema"].iloc[:t + 1], new_res["short_ema"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["long_ema"].iloc[:t + 1], new_res["long_ema"].iloc[:t + 1])

    def test_momentum_lookahead_bias(self):
        prices = self.btc_df["close"].copy()
        t = 100

        orig_res = calculate_momentum_signals(prices, lookback=20)

        perturbed_prices = prices.copy()
        perturbed_prices.iloc[t + 1:] = perturbed_prices.iloc[t + 1:] * -1.0 + 500000.0

        new_res = calculate_momentum_signals(perturbed_prices, lookback=20)

        pd.testing.assert_series_equal(orig_res["signal"].iloc[:t + 1], new_res["signal"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["momentum"].iloc[:t + 1], new_res["momentum"].iloc[:t + 1])

    def test_mean_reversion_lookahead_bias(self):
        prices = self.nvda_df["close"].copy()
        t = 300

        orig_res = calculate_mean_reversion_signals(prices, window=20, threshold=0.02)

        perturbed_prices = prices.copy()
        perturbed_prices.iloc[t + 1:] = 999999.0

        new_res = calculate_mean_reversion_signals(perturbed_prices, window=20, threshold=0.02)

        pd.testing.assert_series_equal(orig_res["signal"].iloc[:t + 1], new_res["signal"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["moving_average"].iloc[:t + 1], new_res["moving_average"].iloc[:t + 1])
        pd.testing.assert_series_equal(orig_res["deviation"].iloc[:t + 1], new_res["deviation"].iloc[:t + 1])
