"""
Unit and Integration Tests for Market Regime & Volatility Analysis (Phase 8).
Tests deterministic trend/volatility classification, threshold modes, statistics, transitions, and look-ahead bias.
"""
import pytest
import numpy as np
import pandas as pd

from backend.app.regimes.enums import MarketRegime, VolatilityState, ThresholdMode
from backend.app.regimes.validation import validate_regime_parameters
from backend.app.regimes.classification import classify_market_regimes
from backend.app.regimes.statistics import (
    calculate_regime_summary_statistics,
    detect_state_transitions,
)
from backend.app.services.regime_service import regime_service


@pytest.fixture
def sample_market_data():
    """Generates synthetic price series for direct deterministic testing."""
    dates = pd.date_range("2020-01-01", periods=150, freq="B").strftime("%Y-%m-%d")
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.015, size=150)
    prices = 100.0 * np.cumprod(1.0 + returns)
    return pd.DataFrame({"date": dates, "close": prices})


class TestRegimeValidation:
    def test_valid_parameters(self):
        validate_regime_parameters(trend_window=50, volatility_window=20, threshold_mode="historical_descriptive")
        validate_regime_parameters(trend_window=10, volatility_window=10, threshold_mode="expanding_threshold")

    def test_invalid_trend_window(self):
        with pytest.raises(ValueError, match="trend_window"):
            validate_regime_parameters(trend_window=1)

    def test_invalid_volatility_window(self):
        with pytest.raises(ValueError, match="volatility_window"):
            validate_regime_parameters(volatility_window=0)

    def test_invalid_threshold_mode(self):
        with pytest.raises(ValueError, match="threshold_mode"):
            validate_regime_parameters(threshold_mode="machine_learning_predictor")


class TestRegimeClassification:
    def test_warmup_periods(self, sample_market_data):
        trend_window = 30
        volatility_window = 20
        df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=trend_window,
            volatility_window=volatility_window,
        )
        
        # Warmup for trend: first trend_window - 1 (29) rows must have trend_value = NaN and regime = None
        for i in range(trend_window - 1):
            assert pd.isna(df["trend_value"].iloc[i])
            assert df["regime"].iloc[i] is None

        # Row trend_window - 1 (index 29) must have a valid trend_value and regime
        assert pd.notna(df["trend_value"].iloc[trend_window - 1])
        assert df["regime"].iloc[trend_window - 1] in [MarketRegime.BULL.value, MarketRegime.BEAR.value]

    def test_bull_bear_classification_logic(self, sample_market_data):
        df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=10,
            volatility_window=10,
        )
        classified = df.dropna(subset=["trend_value"]).copy()
        for _, row in classified.iterrows():
            if row["close"] > row["trend_value"]:
                assert row["regime"] == MarketRegime.BULL.value
            else:
                assert row["regime"] == MarketRegime.BEAR.value

    def test_historical_descriptive_threshold_mode(self, sample_market_data):
        df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="historical_descriptive",
        )
        valid_vols = df["rolling_volatility"].dropna()
        expected_median = float(valid_vols.median())
        
        # All rows should have the same constant historical descriptive threshold
        assert np.isclose(df["volatility_threshold"].iloc[0], expected_median)
        assert np.isclose(df["volatility_threshold"].iloc[-1], expected_median)

        # High/low classifications
        classified_vol = df.dropna(subset=["rolling_volatility"]).copy()
        for _, row in classified_vol.iterrows():
            if row["rolling_volatility"] > row["volatility_threshold"]:
                assert row["volatility_state"] == VolatilityState.HIGH_VOLATILITY.value
            else:
                assert row["volatility_state"] == VolatilityState.LOW_VOLATILITY.value

    def test_expanding_threshold_mode(self, sample_market_data):
        df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="expanding_threshold",
        )
        # Expanding threshold should vary over time
        valid_thresholds = df["volatility_threshold"].dropna()
        assert len(valid_thresholds) > 0
        # The threshold at step t should equal the median of rolling_volatility up to step t
        for idx in range(30, 60):
            expected = df["rolling_volatility"].iloc[: idx + 1].median()
            actual = df["volatility_threshold"].iloc[idx]
            assert np.isclose(expected, actual)


class TestRegimeStatisticsAndTransitions:
    def test_summary_statistics_metrics(self, sample_market_data):
        df = classify_market_regimes(sample_market_data, asset="Gold", trend_window=15, volatility_window=15)
        stats = calculate_regime_summary_statistics(df, asset="Gold")

        assert "bull" in stats
        assert "bear" in stats
        assert "high_volatility" in stats
        assert "low_volatility" in stats
        assert stats["total_observations"] == len(sample_market_data)

        bull_obs = stats["bull"]["observation_count"]
        bear_obs = stats["bear"]["observation_count"]
        assert bull_obs + bear_obs == stats["classified_trend_observations"]

        # Percentages sum to approx 1.0
        if stats["classified_trend_observations"] > 0:
            assert np.isclose(stats["bull"]["percentage"] + stats["bear"]["percentage"], 1.0, atol=0.01)

    def test_state_transitions_detection(self):
        dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
        # Regime sequence: BULL -> BULL -> BEAR -> BEAR -> BULL
        # Volatility sequence: LOW -> HIGH -> HIGH -> LOW -> LOW
        df = pd.DataFrame({
            "date": dates,
            "regime": ["BULL", "BULL", "BEAR", "BEAR", "BULL"],
            "volatility_state": ["LOW_VOLATILITY", "HIGH_VOLATILITY", "HIGH_VOLATILITY", "LOW_VOLATILITY", "LOW_VOLATILITY"],
        })
        transitions = detect_state_transitions(df)
        assert len(transitions) == 4

        # Transition 1: vol LOW -> HIGH on 2024-01-02
        assert transitions[0]["date"] == "2024-01-02"
        assert transitions[0]["transition_type"] == "volatility"
        assert transitions[0]["from_state"] == "LOW_VOLATILITY"
        assert transitions[0]["to_state"] == "HIGH_VOLATILITY"

        # Transition 2: regime BULL -> BEAR on 2024-01-03
        assert transitions[1]["date"] == "2024-01-03"
        assert transitions[1]["transition_type"] == "regime"
        assert transitions[1]["from_state"] == "BULL"
        assert transitions[1]["to_state"] == "BEAR"


class TestLookAheadBias:
    """
    CRITICAL QUANTITATIVE VERIFICATION:
    Verifies that future data perturbations do NOT leak into historical indicator calculations.
    """

    def test_indicator_and_expanding_threshold_no_lookahead(self, sample_market_data):
        cutoff_idx = 75  # time t
        
        # 1. Calculate baseline regimes with expanding threshold
        base_df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="expanding_threshold",
        )
        
        # 2. Perturb prices ONLY after cutoff_idx
        perturbed_data = sample_market_data.copy()
        perturbed_data.loc[cutoff_idx + 1 :, "close"] = perturbed_data.loc[cutoff_idx + 1 :, "close"] * 2.5
        
        # 3. Recalculate regimes on perturbed dataset
        perturbed_df = classify_market_regimes(
            perturbed_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="expanding_threshold",
        )
        
        # 4. Strictly assert that up to cutoff_idx, all values are IDENTICAL
        pd.testing.assert_series_equal(
            base_df["trend_value"].iloc[: cutoff_idx + 1],
            perturbed_df["trend_value"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            base_df["rolling_volatility"].iloc[: cutoff_idx + 1],
            perturbed_df["rolling_volatility"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            base_df["volatility_threshold"].iloc[: cutoff_idx + 1],
            perturbed_df["volatility_threshold"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            base_df["regime"].iloc[: cutoff_idx + 1],
            perturbed_df["regime"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            base_df["volatility_state"].iloc[: cutoff_idx + 1],
            perturbed_df["volatility_state"].iloc[: cutoff_idx + 1],
            check_names=False,
        )

    def test_historical_descriptive_preserves_local_indicators(self, sample_market_data):
        cutoff_idx = 75
        base_df = classify_market_regimes(
            sample_market_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="historical_descriptive",
        )
        
        perturbed_data = sample_market_data.copy()
        perturbed_data.loc[cutoff_idx + 1 :, "close"] = perturbed_data.loc[cutoff_idx + 1 :, "close"] * 3.0
        
        perturbed_df = classify_market_regimes(
            perturbed_data,
            asset="Gold",
            trend_window=20,
            volatility_window=20,
            threshold_mode="historical_descriptive",
        )
        
        # Trend and rolling volatility up to cutoff must be strictly unchanged
        pd.testing.assert_series_equal(
            base_df["trend_value"].iloc[: cutoff_idx + 1],
            perturbed_df["trend_value"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
        pd.testing.assert_series_equal(
            base_df["rolling_volatility"].iloc[: cutoff_idx + 1],
            perturbed_df["rolling_volatility"].iloc[: cutoff_idx + 1],
            check_names=False,
        )
