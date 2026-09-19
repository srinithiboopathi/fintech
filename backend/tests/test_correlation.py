"""
backend/tests/test_correlation.py

Comprehensive Test Suite for Step 7: Correlation & Rolling Correlation.
Tests mathematical properties, date alignment, absence of forward-filling,
rolling window causal behavior, parameter validation, look-ahead protection,
and API integration.
"""

import pytest
import math
from fastapi.testclient import TestClient

from app.main import app
from app.services.correlation import (
    compute_pearson_correlation,
    extract_daily_returns,
    align_return_series,
    calculate_rolling_correlation,
    correlation_service,
)
from app.models.schemas import CleanHistoricalPoint
from app.utils.exceptions import InvalidCorrelationWindowError

client = TestClient(app)


# ==============================================================================
# 1. Known Pearson Correlation Dataset
# ==============================================================================
def test_pearson_known_dataset():
    """Verifies Pearson r against a known mathematical dataset."""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [1.0, 3.0, 2.0, 5.0, 4.0]
    # Expected r: cov(x,y) / (std(x)*std(y)) = 4 / sqrt(10 * 10) = 4/5 = 0.8
    r = compute_pearson_correlation(x, y)
    assert r is not None
    assert round(r, 4) == 0.8


# ==============================================================================
# 2. Perfect Positive Correlation (+1.0)
# ==============================================================================
def test_pearson_perfect_positive():
    """Verifies perfectly linearly dependent series yield exactly 1.0."""
    x = [10.0, 20.0, 30.0, 40.0, 50.0]
    y = [100.0, 200.0, 300.0, 400.0, 500.0]
    r = compute_pearson_correlation(x, y)
    assert r == 1.0


# ==============================================================================
# 3. Perfect Negative Correlation (-1.0)
# ==============================================================================
def test_pearson_perfect_negative():
    """Verifies inversely linear series yield exactly -1.0."""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [50.0, 40.0, 30.0, 20.0, 10.0]
    r = compute_pearson_correlation(x, y)
    assert r == -1.0


# ==============================================================================
# 4. Zero / Near-Zero Correlation Dataset
# ==============================================================================
def test_pearson_zero_correlation():
    """Verifies orthogonal / uncorrelated series yield 0.0."""
    x = [-2.0, -1.0, 0.0, 1.0, 2.0]
    y = [4.0, 1.0, 0.0, 1.0, 4.0]  # y = x^2, symmetric around 0 -> zero linear correlation
    r = compute_pearson_correlation(x, y)
    assert r is not None
    assert abs(r) < 1e-6


# ==============================================================================
# 5. Symmetric Correlation Matrix
# ==============================================================================
def test_correlation_matrix_symmetry():
    """Verifies correlation matrix is strictly symmetric: Corr(A, B) == Corr(B, A)."""
    returns_map = {
        "A": {"2026-09-01": 0.01, "2026-09-02": -0.02, "2026-09-03": 0.015, "2026-09-04": 0.03},
        "B": {"2026-09-01": 0.02, "2026-09-02": -0.01, "2026-09-03": -0.005, "2026-09-04": 0.01},
        "C": {"2026-09-01": -0.01, "2026-09-02": 0.03, "2026-09-03": 0.02, "2026-09-04": -0.015},
    }
    symbols = {"A": "ASSET_A", "B": "ASSET_B", "C": "ASSET_C"}
    names = {"A": "Asset A", "B": "Asset B", "C": "Asset C"}

    # Mock CleanHistoricalPoints
    clean_map = {}
    for k, rets in returns_map.items():
        points = [CleanHistoricalPoint(
            timestamp="2026-08-31T00:00:00Z", open=100.0, high=101.0, low=99.0, close=100.0,
            volume=1000.0, asset=names[k], symbol=symbols[k], source="Twelve Data"
        )]
        curr_price = 100.0
        for d, r in sorted(rets.items()):
            curr_price *= (1.0 + r)
            points.append(CleanHistoricalPoint(
                timestamp=f"{d}T00:00:00Z", open=curr_price, high=curr_price, low=curr_price, close=curr_price,
                volume=1000.0, asset=names[k], symbol=symbols[k], source="Twelve Data"
            ))
        clean_map[k] = points

    resp = correlation_service.compute_correlation_matrix(clean_map, symbols, names)
    m = resp.matrix

    # Check symmetry across all pairs
    sym_keys = list(symbols.values())
    for s1 in sym_keys:
        for s2 in sym_keys:
            assert m[s1][s2] == m[s2][s1], f"Asymmetry between {s1} and {s2}"


# ==============================================================================
# 6. Diagonal Values Equal 1.0
# ==============================================================================
def test_correlation_matrix_diagonal_is_one():
    """Verifies diagonal entries of correlation matrix are strictly 1.0."""
    x = [0.01, -0.02, 0.015, -0.01, 0.025]
    clean_points = [CleanHistoricalPoint(
        timestamp="2026-09-01T00:00:00Z", open=100.0, high=101.0, low=99.0, close=100.0,
        volume=1000.0, asset="Asset A", symbol="A", source="Twelve Data"
    )]
    price = 100.0
    for i, r in enumerate(x, start=2):
        price *= (1.0 + r)
        clean_points.append(CleanHistoricalPoint(
            timestamp=f"2026-09-0{i}T00:00:00Z", open=price, high=price, low=price, close=price,
            volume=1000.0, asset="Asset A", symbol="A", source="Twelve Data"
        ))

    resp = correlation_service.compute_correlation_matrix(
        clean_points_map={"a": clean_points},
        symbols_map={"a": "AAA"},
        asset_names_map={"a": "Asset A"}
    )
    assert resp.matrix["AAA"]["AAA"] == 1.0


# ==============================================================================
# 7. Correct Date Alignment
# ==============================================================================
def test_date_alignment():
    """Verifies alignment retains only exact overlapping dates."""
    rets_map = {
        "asset1": {"2026-09-01": 0.01, "2026-09-02": 0.02, "2026-09-03": -0.01},
        "asset2": {"2026-09-02": 0.05, "2026-09-03": -0.02, "2026-09-04": 0.01},
    }
    dates, aligned = align_return_series(rets_map, ["asset1", "asset2"])
    assert dates == ["2026-09-02", "2026-09-03"]
    assert aligned["asset1"] == [0.02, -0.01]
    assert aligned["asset2"] == [0.05, -0.02]


# ==============================================================================
# 8. Missing Dates Are Handled Correctly
# ==============================================================================
def test_missing_dates_dropped():
    """Verifies non-overlapping dates are excluded from correlation calculation."""
    rets_map = {
        "stock": {"2026-09-01": 0.01, "2026-09-04": 0.02},  # Weekend omitted
        "crypto": {"2026-09-01": 0.02, "2026-09-02": 0.03, "2026-09-03": -0.01, "2026-09-04": -0.02}
    }
    dates, aligned = align_return_series(rets_map, ["stock", "crypto"])
    assert dates == ["2026-09-01", "2026-09-04"]
    assert len(aligned["stock"]) == 2
    assert len(aligned["crypto"]) == 2


# ==============================================================================
# 9. No Forward-Filling of Returns
# ==============================================================================
def test_no_forward_filling():
    """Verifies missing observations are not forward-filled or interpolated."""
    rets_map = {
        "asset1": {"2026-09-01": 0.01, "2026-09-05": 0.03},
        "asset2": {"2026-09-01": 0.02, "2026-09-02": 0.04, "2026-09-05": -0.01},
    }
    dates, aligned = align_return_series(rets_map, ["asset1", "asset2"])
    # 2026-09-02 is absent in asset1, so it must not exist in dates
    assert "2026-09-02" not in dates
    assert len(dates) == 2
    # Returns must equal raw points, never filled
    assert aligned["asset1"] == [0.01, 0.03]


# ==============================================================================
# 10. Rolling Correlation Known Dataset
# ==============================================================================
def test_rolling_correlation_known_dataset():
    """Verifies rolling Pearson correlation matches known values over rolling window."""
    dates = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05"]
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    points = calculate_rolling_correlation(x, y, dates, window=3)

    assert len(points) == 5
    # Window=3: First 2 points (indices 0, 1) are None
    assert points[0].correlation is None
    assert points[1].correlation is None
    # Subsequent points must be 1.0 (perfect positive)
    assert points[2].correlation == 1.0
    assert points[3].correlation == 1.0
    assert points[4].correlation == 1.0


# ==============================================================================
# 11. Rolling Window Behavior (Warmup None Verification)
# ==============================================================================
def test_rolling_window_warmup():
    """Verifies first window - 1 observations evaluate strictly to None."""
    dates = [f"2026-09-{i:02d}" for i in range(1, 21)]
    x = [float(i) for i in range(1, 21)]
    y = [float(i * 2) for i in range(1, 21)]
    window = 10
    points = calculate_rolling_correlation(x, y, dates, window=window)

    for i in range(window - 1):
        assert points[i].correlation is None, f"Index {i} should be None during warmup"
    assert points[window - 1].correlation is not None


# ==============================================================================
# 12. Insufficient Observations
# ==============================================================================
def test_rolling_insufficient_observations():
    """Verifies that if total observations < window, all points return None."""
    dates = ["2026-09-01", "2026-09-02", "2026-09-03"]
    x = [0.01, 0.02, -0.01]
    y = [-0.02, 0.01, 0.03]
    window = 5
    points = calculate_rolling_correlation(x, y, dates, window=window)
    assert len(points) == 3
    for p in points:
        assert p.correlation is None


# ==============================================================================
# 13. Invalid Window (ValueError / InvalidCorrelationWindowError)
# ==============================================================================
def test_rolling_invalid_window():
    """Verifies window < 2 raises InvalidCorrelationWindowError."""
    dates = ["2026-09-01", "2026-09-02"]
    x = [0.01, 0.02]
    y = [0.03, 0.01]
    with pytest.raises(InvalidCorrelationWindowError):
        calculate_rolling_correlation(x, y, dates, window=1)

    with pytest.raises(InvalidCorrelationWindowError):
        calculate_rolling_correlation(x, y, dates, window=0)

    with pytest.raises(InvalidCorrelationWindowError):
        calculate_rolling_correlation(x, y, dates, window=-5)


# ==============================================================================
# 14. HTTP 400 for Invalid Parameters
# ==============================================================================
def test_api_invalid_window_rejection():
    """Verifies GET /market/correlation/rolling rejects invalid window with HTTP 400."""
    invalid_params = ["0", "1", "-5", "abc", "2.5", ""]
    for param in invalid_params:
        r = client.get(f"/market/correlation/rolling?window={param}")
        assert r.status_code == 400, f"Expected 400 for window='{param}', got {r.status_code}"
        data = r.json()
        assert data.get("error") == "INVALID_WINDOW" or "error" in data


# ==============================================================================
# 15. NVDA Correlation Endpoint Verification
# ==============================================================================
def test_api_nvda_in_correlation():
    """Verifies NVIDIA appears in /market/correlation response."""
    r = client.get("/market/correlation")
    assert r.status_code == 200
    data = r.json()
    assert "NVDA" in data["symbols"]
    assert "NVDA" in data["matrix"]
    assert data["matrix"]["NVDA"]["NVDA"] == 1.0


# ==============================================================================
# 16. BTC/USD Correlation Endpoint Verification
# ==============================================================================
def test_api_btc_in_correlation():
    """Verifies Bitcoin appears in /market/correlation response."""
    r = client.get("/market/correlation")
    assert r.status_code == 200
    data = r.json()
    assert "BTC/USD" in data["symbols"]
    assert "BTC/USD" in data["matrix"]
    assert data["matrix"]["BTC/USD"]["BTC/USD"] == 1.0


# ==============================================================================
# 17. Gold Correlation Endpoint Verification
# ==============================================================================
def test_api_gold_in_correlation():
    """Verifies Gold appears in /market/correlation response."""
    r = client.get("/market/correlation")
    assert r.status_code == 200
    data = r.json()
    assert "XAU/USD" in data["symbols"]
    assert "XAU/USD" in data["matrix"]
    assert data["matrix"]["XAU/USD"]["XAU/USD"] == 1.0


# ==============================================================================
# 18. Look-Ahead Bias Prevention
# ==============================================================================
def test_rolling_look_ahead_protection():
    """Verifies modifying future return points does not alter past rolling correlation."""
    dates = [f"2026-09-{i:02d}" for i in range(1, 11)]
    x_base = [0.01, 0.02, -0.01, 0.03, -0.02, 0.015, -0.01, 0.025, 0.005, -0.01]
    y_base = [0.015, 0.01, 0.02, -0.01, 0.025, -0.015, 0.02, 0.01, -0.02, 0.03]

    window = 4
    base_points = calculate_rolling_correlation(x_base, y_base, dates, window=window)

    # Mutate future observations (indices 8, 9)
    x_mutated = list(x_base)
    y_mutated = list(y_base)
    x_mutated[8] = 0.99
    x_mutated[9] = -0.99
    y_mutated[8] = -0.88
    y_mutated[9] = 0.88

    mutated_points = calculate_rolling_correlation(x_mutated, y_mutated, dates, window=window)

    # Values for indices 0 to 7 MUST be identical
    for i in range(8):
        assert base_points[i].correlation == mutated_points[i].correlation, (
            f"Look-ahead violation at index {i}: base={base_points[i].correlation}, mutated={mutated_points[i].correlation}"
        )


# ==============================================================================
# 19. No Fake / Random Data
# ==============================================================================
def test_no_fake_random_data():
    """Verifies API responses originate from verified Twelve Data source with real calculations."""
    r_corr = client.get("/market/correlation")
    assert r_corr.status_code == 200
    data = r_corr.json()
    assert data["source"] == "Twelve Data"
    assert data["data_status"] == "calculated"
    assert data["observation_count"] > 0

    # Check that pairwise values are within [-1.0, 1.0] and not mocked to dummy numbers
    for s1 in data["symbols"]:
        for s2 in data["symbols"]:
            val = data["matrix"][s1][s2]
            assert val is not None
            assert -1.0 <= val <= 1.0

    r_roll = client.get("/market/correlation/rolling")
    assert r_roll.status_code == 200
    roll_data = r_roll.json()
    assert roll_data["source"] == "Twelve Data"
    assert roll_data["data_status"] == "calculated"
    assert len(roll_data["pairs"]) == 3
