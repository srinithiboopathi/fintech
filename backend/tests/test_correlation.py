"""
Deterministic unit tests for QuantLab Cross-Asset Correlation Engine.
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.correlation.matrix import (
    align_price_series,
    calculate_multi_asset_returns,
    calculate_correlation_matrix,
    compute_cross_asset_correlation_matrix,
)
from backend.app.correlation.rolling import (
    calculate_rolling_pairwise_correlation,
    calculate_multi_asset_rolling_correlations,
)


class TestCorrelationMatrix:
    def test_perfect_positive_correlation(self):
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        # Prices move proportionately: identical returns
        prices_a = pd.Series([100.0 * (1.02 ** i) for i in range(10)], index=dates, name="AssetA")
        prices_b = pd.Series([50.0 * (1.02 ** i) for i in range(10)], index=dates, name="AssetB")

        corr = compute_cross_asset_correlation_matrix({"AssetA": prices_a, "AssetB": prices_b})
        assert corr.loc["AssetA", "AssetB"] == pytest.approx(1.0)
        assert corr.loc["AssetB", "AssetA"] == pytest.approx(1.0)
        assert corr.loc["AssetA", "AssetA"] == pytest.approx(1.0)
        assert corr.loc["AssetB", "AssetB"] == pytest.approx(1.0)

    def test_perfect_negative_correlation(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns_df = pd.DataFrame(
            {
                "AssetA": [0.02, -0.01, 0.03, -0.02, 0.01],
                "AssetB": [-0.02, 0.01, -0.03, 0.02, -0.01],
            },
            index=dates,
        )
        corr = calculate_correlation_matrix(returns_df)
        assert corr.loc["AssetA", "AssetB"] == pytest.approx(-1.0)
        assert corr.loc["AssetB", "AssetA"] == pytest.approx(-1.0)

    def test_independent_sample_data(self):
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        # Orthogonal return vectors with mean = 0
        returns_df = pd.DataFrame(
            {
                "AssetA": [0.01, -0.01, 0.01, -0.01],
                "AssetB": [0.01, 0.01, -0.01, -0.01],
            },
            index=dates,
        )
        corr = calculate_correlation_matrix(returns_df)
        assert corr.loc["AssetA", "AssetB"] == pytest.approx(0.0, abs=1e-7)

    def test_missing_dates_alignment(self):
        # Asset A trades Jan 1, Jan 2, Jan 4
        s_a = pd.Series([10.0, 11.0, 12.0], index=["2024-01-01", "2024-01-02", "2024-01-04"], name="Gold")
        # Asset B trades Jan 1, Jan 3, Jan 4
        s_b = pd.Series([100.0, 105.0, 110.0], index=["2024-01-01", "2024-01-03", "2024-01-04"], name="BTC")

        # Inner join: only Jan 1 and Jan 4
        aligned_inner = align_price_series({"Gold": s_a, "BTC": s_b}, join="inner")
        assert len(aligned_inner) == 2
        assert list(aligned_inner.index.strftime("%Y-%m-%d")) == ["2024-01-01", "2024-01-04"]

        # Outer join: Jan 1, 2, 3, 4
        aligned_outer = align_price_series({"Gold": s_a, "BTC": s_b}, join="outer")
        assert len(aligned_outer) == 4
        assert np.isnan(aligned_outer.loc["2024-01-02", "BTC"])
        assert np.isnan(aligned_outer.loc["2024-01-03", "Gold"])

    def test_empty_input_handling(self):
        empty_dict = {}
        empty_aligned = align_price_series(empty_dict)
        assert empty_aligned.empty

        empty_df = pd.DataFrame()
        assert calculate_multi_asset_returns(empty_df).empty
        assert calculate_correlation_matrix(empty_df).empty
        assert compute_cross_asset_correlation_matrix(empty_df).empty


class TestRollingCorrelation:
    def test_rolling_correlation_deterministic(self):
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        s1 = pd.Series(np.arange(1.0, 11.0), index=dates, name="A")
        s2 = pd.Series(np.arange(1.0, 11.0) * 3.0, index=dates, name="B")

        roll = calculate_rolling_pairwise_correlation(s1, s2, window=5)
        # First 4 elements should be NaN (min_periods = window = 5)
        for i in range(4):
            assert np.isnan(roll.iloc[i])
        # Elements 4 through 9 are exactly 1.0
        for i in range(4, 10):
            assert roll.iloc[i] == pytest.approx(1.0)

    def test_insufficient_rolling_data(self):
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        s1 = pd.Series(range(10), index=dates, name="AssetA")
        s2 = pd.Series(range(10), index=dates, name="AssetB")

        # Default window is 30, but dataset has only 10 rows
        roll = calculate_rolling_pairwise_correlation(s1, s2, window=30)
        assert len(roll) == 10
        assert roll.isna().all()

    def test_multi_asset_rolling_correlations(self):
        dates = pd.date_range("2024-01-01", periods=40, freq="D")
        returns_df = pd.DataFrame(
            {
                "Gold": np.random.RandomState(42).normal(0.001, 0.01, 40),
                "Bitcoin": np.random.RandomState(43).normal(0.002, 0.03, 40),
                "NVIDIA": np.random.RandomState(44).normal(0.003, 0.025, 40),
            },
            index=dates,
        )

        roll_df = calculate_multi_asset_rolling_correlations(returns_df, window=30)
        assert set(roll_df.columns) == {"Gold_Bitcoin", "Gold_NVIDIA", "Bitcoin_NVIDIA"}
        assert len(roll_df) == 40
        assert roll_df["Gold_Bitcoin"].iloc[:29].isna().all()
        assert not np.isnan(roll_df["Gold_Bitcoin"].iloc[29])

    def test_empty_rolling_input(self):
        empty = pd.Series([], dtype=float)
        roll = calculate_rolling_pairwise_correlation(empty, empty, window=30)
        assert roll.empty

        empty_df = pd.DataFrame()
        multi_roll = calculate_multi_asset_rolling_correlations(empty_df)
        assert multi_roll.empty
