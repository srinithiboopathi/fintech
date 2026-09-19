"""
Unit tests for technical indicators (SMA, EMA) in QuantLab.
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.quant.indicators import calculate_sma, calculate_ema


class TestSMA:
    def test_sma_deterministic_values(self):
        prices = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        sma_3 = calculate_sma(prices, window=3)

        assert np.isnan(sma_3.iloc[0])
        assert np.isnan(sma_3.iloc[1])
        assert sma_3.iloc[2] == pytest.approx(20.0)
        assert sma_3.iloc[3] == pytest.approx(30.0)
        assert sma_3.iloc[4] == pytest.approx(40.0)

    def test_sma_window_one(self):
        prices = pd.Series([15.5, 17.2, 16.8])
        sma_1 = calculate_sma(prices, window=1)
        pd.testing.assert_series_equal(sma_1, prices)

    def test_sma_empty_series(self):
        empty_series = pd.Series([], dtype=float)
        result = calculate_sma(empty_series, window=3)
        assert result.empty

    def test_sma_invalid_window_raises(self):
        prices = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="Window must be a positive integer"):
            calculate_sma(prices, window=0)
        with pytest.raises(ValueError, match="Window must be a positive integer"):
            calculate_sma(prices, window=-5)


class TestEMA:
    def test_ema_deterministic_calculation(self):
        prices = pd.Series([10.0, 20.0, 30.0, 40.0])
        ema_2 = calculate_ema(prices, span=2, adjust=False)

        # For span=2, alpha = 2 / (2 + 1) = 2/3
        # t=0: 10.0
        # t=1: (2/3)*20 + (1/3)*10 = 13.3333 + 3.3333 = 16.666667
        # t=2: (2/3)*30 + (1/3)*16.666667 = 20 + 5.555556 = 25.555556
        assert ema_2.iloc[0] == pytest.approx(10.0)
        assert ema_2.iloc[1] == pytest.approx(16.666667, rel=1e-4)
        assert ema_2.iloc[2] == pytest.approx(25.555556, rel=1e-4)

    def test_ema_empty_series(self):
        empty_series = pd.Series([], dtype=float)
        result = calculate_ema(empty_series, span=5)
        assert result.empty

    def test_ema_invalid_span_raises(self):
        prices = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="Span must be a positive integer"):
            calculate_ema(prices, span=0)
