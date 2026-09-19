"""
backend/tests/test_market_regimes.py

Comprehensive Automated Test Suite for Step 11: Market Regime Analysis.
Verifies:
1. Bullish classification (close > SMA)
2. Bearish classification (close < SMA)
3. Sideways and unknown handling
4. Low volatility classification
5. High volatility classification
6. Combined regimes (BULLISH_LOW_VOL, BULLISH_HIGH_VOL, BEARISH_LOW_VOL, etc.)
7. Insufficient data handling
8. Configurable periods (trend_period, volatility_window)
9. Invalid parameter validation (HTTP 400)
10. Chronological ordering preservation
11. Zero look-ahead bias protection
12. API regimes endpoint (GET /market/{asset}/regimes)
13. API regimes summary endpoint (GET /market/{asset}/regimes/summary)
14. NVDA regime analysis integration
15. BTC/USD regime analysis integration
16. XAU/USD regime analysis integration
17. Deterministic repeatability
18. Zero fake or synthetic random data
19. Strategy performance by regime attribution
20. Unsupported asset rejection
"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.schemas import CleanHistoricalPoint
from app.services.market_regimes import MarketRegimeService
from app.utils.exceptions import (
    InvalidRegimeParameterError,
    InsufficientHistoricalDataError,
)

app = create_app()
client = TestClient(app)
regime_service = MarketRegimeService()


def make_clean_points(prices, start_date="2026-01-01"):
    """Helper creating deterministic CleanHistoricalPoint sequence."""
    base_dt = datetime.fromisoformat(f"{start_date}T00:00:00")
    points = []
    for i, p in enumerate(prices):
        dt = base_dt + timedelta(days=i)
        ts = dt.strftime("%Y-%m-%dT00:00:00Z")
        points.append(
            CleanHistoricalPoint(
                timestamp=ts,
                open=round(p * 0.99, 4),
                high=round(p * 1.02, 4),
                low=round(p * 0.98, 4),
                close=float(p),
                volume=1000.0,
                asset="NVIDIA",
                symbol="NVDA",
                source="Twelve Data",
            )
        )
    return points


# ==============================================================================
# 1. BULLISH CLASSIFICATION
# ==============================================================================
def test_bullish_classification():
    """1. Verifies trend is classified as BULLISH when close > SMA."""
    # Prices: 5 observations of 100, then 110
    prices = [100.0, 100.0, 100.0, 100.0, 100.0, 110.0]
    pts = make_clean_points(prices)
    # trend_period=5 -> at index 5, SMA of [100, 100, 100, 100, 110] is 102.0
    # Close is 110 > 102.0 -> BULLISH
    regimes, _ = regime_service.classify_regimes(
        pts,
        trend_period=5,
        volatility_window=2,
        volatility_threshold=1.0,
    )
    assert regimes[5].trend_state == "BULLISH"
    assert regimes[5].sma == 102.0
    assert regimes[5].close == 110.0


# ==============================================================================
# 2. BEARISH CLASSIFICATION
# ==============================================================================
def test_bearish_classification():
    """2. Verifies trend is classified as BEARISH when close < SMA."""
    prices = [100.0, 100.0, 100.0, 100.0, 100.0, 90.0]
    pts = make_clean_points(prices)
    # trend_period=5 -> at index 5, SMA is 98.0, Close is 90.0 < 98.0 -> BEARISH
    regimes, _ = regime_service.classify_regimes(
        pts,
        trend_period=5,
        volatility_window=2,
        volatility_threshold=1.0,
    )
    assert regimes[5].trend_state == "BEARISH"
    assert regimes[5].sma == 98.0
    assert regimes[5].close == 90.0


# ==============================================================================
# 3. SIDEWAYS AND UNKNOWN HANDLING
# ==============================================================================
def test_sideways_and_unknown_handling():
    """3. Verifies UNKNOWN during warmup and SIDEWAYS when close is within neutral band or equal to SMA."""
    prices = [100.0, 100.0, 100.0, 100.0, 100.0]
    pts = make_clean_points(prices)

    regimes, _ = regime_service.classify_regimes(
        pts,
        trend_period=5,
        volatility_window=2,
        volatility_threshold=1.0,
    )

    # During warmup (indices 0..3), trend is UNKNOWN
    for i in range(4):
        assert regimes[i].trend_state == "UNKNOWN"
        assert regimes[i].sma is None
        assert regimes[i].combined_regime == "UNKNOWN"

    # At index 4: SMA=100.0, Close=100.0 -> close == SMA -> SIDEWAYS
    assert regimes[4].trend_state == "SIDEWAYS"
    assert regimes[4].sma == 100.0

    # With trend_threshold = 0.05 (5% neutral band)
    prices_band = [100.0, 100.0, 100.0, 100.0, 100.0, 101.0]
    pts_band = make_clean_points(prices_band)
    # SMA at index 5 = (100+100+100+100+101)/5 = 100.2
    # Close = 101.0 is within 5% band (100.2 +/- 5.01) -> SIDEWAYS
    regimes_band, _ = regime_service.classify_regimes(
        pts_band,
        trend_period=5,
        volatility_window=2,
        volatility_threshold=1.0,
        trend_threshold=0.05,
    )
    assert regimes_band[5].trend_state == "SIDEWAYS"


# ==============================================================================
# 4. LOW VOLATILITY CLASSIFICATION
# ==============================================================================
def test_low_volatility_classification():
    """4. Verifies volatility state is LOW_VOLATILITY when rolling volatility <= threshold."""
    # Gentle 0.1% daily movements -> low volatility
    prices = [100.0, 100.1, 100.2, 100.1, 100.2, 100.1, 100.2]
    pts = make_clean_points(prices)

    regimes, _ = regime_service.classify_regimes(
        pts,
        trend_period=3,
        volatility_window=3,
        volatility_threshold=1.0,  # 1.0% threshold
    )
    for i in range(3, len(regimes)):
        assert regimes[i].volatility_state == "LOW_VOLATILITY"
        assert regimes[i].rolling_volatility is not None
        assert regimes[i].rolling_volatility <= 1.0


# ==============================================================================
# 5. HIGH VOLATILITY CLASSIFICATION
# ==============================================================================
def test_high_volatility_classification():
    """5. Verifies volatility state is HIGH_VOLATILITY when rolling volatility > threshold."""
    # Wild 10% daily swings -> high volatility
    prices = [100.0, 110.0, 95.0, 115.0, 90.0, 120.0, 85.0]
    pts = make_clean_points(prices)

    regimes, _ = regime_service.classify_regimes(
        pts,
        trend_period=3,
        volatility_window=3,
        volatility_threshold=1.0,  # 1.0% threshold
    )
    for i in range(3, len(regimes)):
        assert regimes[i].volatility_state == "HIGH_VOLATILITY"
        assert regimes[i].rolling_volatility is not None
        assert regimes[i].rolling_volatility > 1.0


# ==============================================================================
# 6. COMBINED REGIMES
# ==============================================================================
def test_combined_regimes():
    """6. Verifies exact combined regimes: BULLISH_LOW_VOL, BULLISH_HIGH_VOL, BEARISH_LOW_VOL, BEARISH_HIGH_VOL, etc."""
    # Steady upward trend with low volatility -> BULLISH_LOW_VOL
    steady_up = [100.0, 100.2, 100.4, 100.6, 100.8, 101.0, 101.2, 101.4]
    pts_up = make_clean_points(steady_up)
    regimes_up, _ = regime_service.classify_regimes(
        pts_up,
        trend_period=3,
        volatility_window=3,
        volatility_threshold=0.5,
    )
    assert regimes_up[-1].trend_state == "BULLISH"
    assert regimes_up[-1].volatility_state == "LOW_VOLATILITY"
    assert regimes_up[-1].combined_regime == "BULLISH_LOW_VOL"

    # Volatile downward trend -> BEARISH_HIGH_VOL
    volatile_down = [100.0, 105.0, 92.0, 98.0, 80.0, 88.0, 70.0, 77.0]
    pts_down = make_clean_points(volatile_down)
    regimes_down, _ = regime_service.classify_regimes(
        pts_down,
        trend_period=3,
        volatility_window=3,
        volatility_threshold=1.0,
    )
    assert regimes_down[-1].trend_state == "BEARISH"
    assert regimes_down[-1].volatility_state == "HIGH_VOLATILITY"
    assert regimes_down[-1].combined_regime == "BEARISH_HIGH_VOL"


# ==============================================================================
# 7. INSUFFICIENT DATA HANDLING
# ==============================================================================
def test_insufficient_data_handling():
    """7. Verifies UNKNOWN combined regime when observations < trend_period or volatility_window."""
    short_prices = [100.0, 101.0, 102.0]
    pts = make_clean_points(short_prices)

    # Trend period 50, vol window 20 -> far exceeds length 3
    regimes, _ = regime_service.classify_regimes(pts, trend_period=50, volatility_window=20)
    assert len(regimes) == 3
    for r in regimes:
        assert r.combined_regime == "UNKNOWN"
        assert r.trend_state == "UNKNOWN"
        assert r.volatility_state == "UNKNOWN"

    # Empty data raises InsufficientHistoricalDataError
    with pytest.raises(InsufficientHistoricalDataError):
        regime_service.classify_regimes([], trend_period=5, volatility_window=2)


# ==============================================================================
# 8. CONFIGURABLE PERIODS
# ==============================================================================
def test_configurable_periods():
    """8. Verifies custom trend_period and volatility_window are properly applied."""
    prices = [100.0 + i for i in range(30)]
    pts = make_clean_points(prices)

    regimes, params = regime_service.classify_regimes(
        pts,
        trend_period=10,
        volatility_window=5,
        volatility_threshold=2.5,
        trend_threshold=0.01,
    )
    assert params.trend_period == 10
    assert params.volatility_window == 5
    assert params.volatility_threshold == 2.5
    assert params.trend_threshold == 0.01

    # First 9 observations should have sma=None
    for i in range(9):
        assert regimes[i].sma is None
    # From index 9 onward, sma must be a valid float
    for i in range(9, 30):
        assert isinstance(regimes[i].sma, float)


# ==============================================================================
# 9. INVALID PARAMETERS REJECTION
# ==============================================================================
def test_invalid_parameters_rejection():
    """9. Verifies invalid parameter values raise InvalidRegimeParameterError (HTTP 400)."""
    pts = make_clean_points([100.0, 101.0, 102.0, 103.0, 104.0])

    # trend_period < 1
    with pytest.raises(InvalidRegimeParameterError):
        regime_service.classify_regimes(pts, trend_period=0)

    # volatility_window < 2
    with pytest.raises(InvalidRegimeParameterError):
        regime_service.classify_regimes(pts, volatility_window=1)

    # trend_period > 500 (unbounded protection)
    with pytest.raises(InvalidRegimeParameterError):
        regime_service.classify_regimes(pts, trend_period=501)

    # negative volatility_threshold
    with pytest.raises(InvalidRegimeParameterError):
        regime_service.classify_regimes(pts, volatility_threshold=-1.5)

    # trend_threshold > 1.0
    with pytest.raises(InvalidRegimeParameterError):
        regime_service.classify_regimes(pts, trend_threshold=1.5)


# ==============================================================================
# 10. CHRONOLOGICAL ORDERING
# ==============================================================================
def test_chronological_ordering():
    """10. Verifies returned points are strictly in ascending chronological order."""
    prices = [100.0, 102.0, 101.0, 103.0, 105.0]
    pts = make_clean_points(prices)
    # Reverse input to test sorting
    reversed_pts = list(reversed(pts))

    regimes, _ = regime_service.classify_regimes(reversed_pts, trend_period=2, volatility_window=2)
    timestamps = [r.timestamp for r in regimes]
    assert timestamps == sorted(timestamps)


# ==============================================================================
# 11. ZERO LOOK-AHEAD BIAS PROTECTION
# ==============================================================================
def test_look_ahead_protection():
    """11. Verifies mutating future prices does NOT alter earlier regime classifications."""
    base_prices = [100.0, 101.0, 102.0, 101.5, 102.5, 103.0, 102.0, 104.0, 103.5, 105.0]
    pts_base = make_clean_points(base_prices)

    regimes_base, _ = regime_service.classify_regimes(
        pts_base,
        trend_period=3,
        volatility_window=3,
    )

    # Mutate prices at future indices 8 and 9 wildly
    mutated_prices = list(base_prices)
    mutated_prices[8] = 500.0
    mutated_prices[9] = 20.0
    pts_mutated = make_clean_points(mutated_prices)

    regimes_mutated, _ = regime_service.classify_regimes(
        pts_mutated,
        trend_period=3,
        volatility_window=3,
    )

    # Indices 0 to 7 MUST remain strictly identical in all regime fields
    for i in range(8):
        assert regimes_base[i].timestamp == regimes_mutated[i].timestamp
        assert regimes_base[i].close == regimes_mutated[i].close
        assert regimes_base[i].sma == regimes_mutated[i].sma
        assert regimes_base[i].rolling_volatility == regimes_mutated[i].rolling_volatility
        assert regimes_base[i].trend_state == regimes_mutated[i].trend_state
        assert regimes_base[i].volatility_state == regimes_mutated[i].volatility_state
        assert regimes_base[i].combined_regime == regimes_mutated[i].combined_regime


# ==============================================================================
# 12. API REGIMES ENDPOINT
# ==============================================================================
def test_api_regimes_endpoint():
    """12. Verifies GET /market/nvidia/regimes returns 200 and expected schema."""
    resp = client.get("/market/nvidia/regimes?trend_period=20&volatility_window=10")
    assert resp.status_code == 200
    data = resp.json()

    assert data["asset"] == "NVIDIA"
    assert data["symbol"] == "NVDA"
    assert "parameters" in data
    assert data["parameters"]["trend_period"] == 20
    assert data["parameters"]["volatility_window"] == 10
    assert "data" in data
    assert len(data["data"]) > 0

    first_pt = data["data"][0]
    assert "timestamp" in first_pt
    assert "close" in first_pt
    assert "trend_state" in first_pt
    assert "volatility_state" in first_pt
    assert "combined_regime" in first_pt


# ==============================================================================
# 13. API REGIMES SUMMARY ENDPOINT
# ==============================================================================
def test_api_regimes_summary_endpoint():
    """13. Verifies GET /market/nvidia/regimes/summary returns 200 and distribution sum to ~100%."""
    resp = client.get("/market/nvidia/regimes/summary?trend_period=20&volatility_window=10")
    assert resp.status_code == 200
    data = resp.json()

    assert data["asset"] == "NVIDIA"
    assert "regimes" in data
    assert len(data["regimes"]) > 0

    total_pct = sum(item["percentage"] for item in data["regimes"])
    assert 99.0 <= total_pct <= 101.0  # Floating point sum around 100%

    for item in data["regimes"]:
        assert "regime" in item
        assert "observation_count" in item
        assert "percentage" in item


# ==============================================================================
# 14. LIVE DATA: NVDA
# ==============================================================================
def test_nvda_regimes_live():
    """14. Verifies live cleaned data for NVDA produces valid regimes."""
    resp = client.get("/market/nvidia/regimes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["observation_count"] > 0
    # Check that regimes include at least one valid combination
    combined_set = set(pt["combined_regime"] for pt in data["data"])
    assert len(combined_set) > 0


# ==============================================================================
# 15. LIVE DATA: BTC/USD
# ==============================================================================
def test_btc_usd_regimes_live():
    """15. Verifies live cleaned data for BTC/USD produces valid regimes."""
    resp = client.get("/market/bitcoin/regimes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["observation_count"] > 0
    assert data["symbol"] == "BTC/USD"


# ==============================================================================
# 16. LIVE DATA: XAU/USD
# ==============================================================================
def test_xau_usd_regimes_live():
    """16. Verifies live cleaned data for XAU/USD produces valid regimes."""
    resp = client.get("/market/gold/regimes")
    assert resp.status_code == 200
    data = resp.json()
    assert data["observation_count"] > 0
    assert data["symbol"] == "XAU/USD"


# ==============================================================================
# 17. DETERMINISTIC REPEATABILITY
# ==============================================================================
def test_deterministic_repeatability():
    """17. Verifies identical input produces identical regime classifications."""
    prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0]
    pts = make_clean_points(prices)

    run1, p1 = regime_service.classify_regimes(pts, trend_period=3, volatility_window=3)
    run2, p2 = regime_service.classify_regimes(pts, trend_period=3, volatility_window=3)

    assert len(run1) == len(run2)
    assert p1.volatility_threshold == p2.volatility_threshold
    for i in range(len(run1)):
        assert run1[i].model_dump() == run2[i].model_dump()


# ==============================================================================
# 18. NO FAKE OR RANDOM DATA
# ==============================================================================
def test_no_fake_random_data():
    """18. Verifies regime calculations derive exclusively from real cleaned prices."""
    resp = client.get("/market/nvidia/regimes")
    assert resp.status_code == 200
    data = resp.json()

    # Compare first clean price against clean data endpoint
    clean_resp = client.get("/market/nvidia/data")
    clean_data = clean_resp.json()

    assert data["data"][0]["close"] == clean_data["data"][0]["close"]
    assert data["data"][0]["timestamp"] == clean_data["data"][0]["timestamp"]


# ==============================================================================
# 19. STRATEGY PERFORMANCE BY REGIME
# ==============================================================================
def test_strategy_performance_by_regime():
    """19. Verifies GET /market/nvidia/regimes/performance returns factual metrics without rankings."""
    resp = client.get("/market/nvidia/regimes/performance?trend_period=20&volatility_window=10")
    assert resp.status_code == 200
    data = resp.json()

    assert "performances" in data
    assert len(data["performances"]) > 0

    strategies_seen = set()
    for item in data["performances"]:
        assert "strategy" in item
        assert "regime" in item
        assert "observations" in item
        assert "trades" in item
        assert "total_return" in item
        assert "maximum_drawdown" in item
        # Invariant: No subjective words in output
        item_str = str(item).lower()
        assert "winner" not in item_str
        assert "loser" not in item_str
        assert "best" not in item_str
        assert "worst" not in item_str
        strategies_seen.add(item["strategy"])

    assert len(strategies_seen) == 4


# ==============================================================================
# 20. UNSUPPORTED ASSET REJECTION (HTTP 400)
# ==============================================================================
def test_unsupported_asset_rejected():
    """20. Verifies querying an unsupported asset returns HTTP 400."""
    resp = client.get("/market/dogecoin/regimes")
    assert resp.status_code == 400
    assert resp.json()["error"] == "UNSUPPORTED_ASSET"
