"""
Mathematical Unit Tests for QUANTLAB Correlation and Cross-Asset Engine.
Validates Pearson formulas, matrix symmetry, date alignment, and look-ahead bias guards.
"""
import pytest
import numpy as np
import pandas as pd

from backend.app.correlation.alignment import align_two_asset_returns, align_asset_returns
from backend.app.correlation.matrix import (
    calculate_pearson_correlation,
    calculate_pairwise_correlation,
    calculate_correlation_matrix,
)
from backend.app.correlation.rolling import calculate_rolling_correlation


class TestPearsonCorrelationMath:
    def test_perfect_positive_correlation(self):
        s_a = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        s_b = pd.Series([0.02, 0.04, 0.06, 0.08, 0.10])
        r = calculate_pearson_correlation(s_a, s_b)
        assert pytest.approx(r, rel=1e-6) == 1.0

    def test_perfect_negative_correlation(self):
        s_a = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        s_b = pd.Series([-0.02, -0.04, -0.06, -0.08, -0.10])
        r = calculate_pearson_correlation(s_a, s_b)
        assert pytest.approx(r, rel=1e-6) == -1.0

    def test_zero_correlation(self):
        # Orthogonal series
        s_a = pd.Series([1.0, 0.0, -1.0, 0.0])
        s_b = pd.Series([0.0, 1.0, 0.0, -1.0])
        r = calculate_pearson_correlation(s_a, s_b)
        assert pytest.approx(r, abs=1e-6) == 0.0

    def test_constant_series_zero_volatility(self):
        s_a = pd.Series([0.05, 0.05, 0.05, 0.05])
        s_b = pd.Series([0.01, 0.02, 0.03, 0.04])
        r = calculate_pearson_correlation(s_a, s_b)
        assert r is None  # Must safely return None without crash or division by zero

    def test_insufficient_observations(self):
        s_a = pd.Series([0.01])
        s_b = pd.Series([0.02])
        r = calculate_pearson_correlation(s_a, s_b)
        assert r is None


class TestDateAlignment:
    def test_pairwise_date_alignment_intersection(self):
        df_a = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
            "close": [100.0, 102.0, 101.0, 105.0]
        })
        df_b = pd.DataFrame({
            "date": ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "close": [50.0, 52.0, 51.0, 55.0]
        })
        aligned = align_two_asset_returns(df_a, df_b, "AssetA", "AssetB")
        # Returns for df_a exist for [2023-01-02, 2023-01-03, 2023-01-04]
        # Returns for df_b exist for [2023-01-03, 2023-01-04, 2023-01-05]
        # Overlap should be 2023-01-03 and 2023-01-04 (2 common dates)
        assert len(aligned) == 2
        assert list(aligned["date"]) == ["2023-01-03", "2023-01-04"]
        assert "AssetA" in aligned.columns
        assert "AssetB" in aligned.columns


class TestCorrelationMatrix:
    def test_matrix_properties_and_symmetry(self):
        dates = [f"2023-01-0{i}" for i in range(1, 9)]
        df_gold = pd.DataFrame({"date": dates, "close": [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0]})
        df_btc = pd.DataFrame({"date": dates, "close": [200.0, 205.0, 202.0, 208.0, 212.0, 210.0, 215.0, 220.0]})
        df_nvda = pd.DataFrame({"date": dates, "close": [50.0, 48.0, 52.0, 49.0, 47.0, 51.0, 48.0, 46.0]})

        asset_dfs = {"Gold": df_gold, "Bitcoin": df_btc, "NVIDIA": df_nvda}
        matrix_res = calculate_correlation_matrix(asset_dfs)

        matrix = matrix_res["matrix"]
        assets = matrix_res["assets"]
        
        # 1. Check diagonal is 1.0
        for a in assets:
            assert pytest.approx(matrix[a][a], rel=1e-6) == 1.0
            
        # 2. Check symmetry M[i][j] == M[j][i]
        for a1 in assets:
            for a2 in assets:
                assert pytest.approx(matrix[a1][a2], rel=1e-6) == matrix[a2][a1]


class TestRollingCorrelation:
    def test_rolling_correlation_warmup_and_values(self):
        dates = [f"2023-01-{i:02d}" for i in range(1, 11)]
        prices_a = [100.0 + i for i in range(10)]
        prices_b = [50.0 + 2 * i for i in range(10)]
        
        df_a = pd.DataFrame({"date": dates, "close": prices_a})
        df_b = pd.DataFrame({"date": dates, "close": prices_b})
        
        window = 3
        rolling_df = calculate_rolling_correlation(df_a, df_b, "AssetA", "AssetB", window=window)
        # First 2 return rolling points should be NaN (warmup)
        assert np.isnan(rolling_df["rolling_correlation"].iloc[0])
        assert np.isnan(rolling_df["rolling_correlation"].iloc[1])
        # After warmup, linear relation yields ~ 1.0
        assert pytest.approx(rolling_df["rolling_correlation"].iloc[2], rel=1e-3) == 1.0


class TestCorrelationLookAheadBiasPrevention:
    def test_rolling_correlation_lookahead_independence(self):
        dates = [f"2023-01-{i:02d}" for i in range(1, 21)]
        prices_a = [100.0 + (i % 3) * 2.0 for i in range(20)]
        prices_b = [50.0 + (i % 4) * 1.5 for i in range(20)]
        
        df_a1 = pd.DataFrame({"date": dates, "close": prices_a})
        df_b1 = pd.DataFrame({"date": dates, "close": prices_b})
        
        res1 = calculate_rolling_correlation(df_a1, df_b1, "A", "B", window=5)
        corr_at_8_orig = res1["rolling_correlation"].iloc[8]

        # Mutate future prices from index 11 onwards with extreme perturbations
        mutated_a = list(prices_a)
        mutated_b = list(prices_b)
        for j in range(11, 20):
            mutated_a[j] = 999999.0
            mutated_b[j] = -888888.0

        df_a2 = pd.DataFrame({"date": dates, "close": mutated_a})
        df_b2 = pd.DataFrame({"date": dates, "close": mutated_b})

        res2 = calculate_rolling_correlation(df_a2, df_b2, "A", "B", window=5)
        corr_at_8_mutated = res2["rolling_correlation"].iloc[8]

        # Earlier correlation at time t MUST be completely identical
        assert pytest.approx(corr_at_8_orig, rel=1e-9) == corr_at_8_mutated
