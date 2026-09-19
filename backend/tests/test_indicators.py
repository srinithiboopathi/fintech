"""
backend/tests/test_indicators.py

Comprehensive Test Suite for Step 4 Quantitative Indicators (SMA & EMA):
- Test A: SMA with manually calculated known dataset
- Test B: EMA with manually calculated known dataset using SMA initialization
- Test C: Period greater than available data (all null, zero valid count)
- Test D: Period = 1 (SMA == close, EMA == close)
- Test E: Invalid periods (0, -5, decimal, 'abc' -> HTTP 400)
- Test F: Chronological ascending ordering
- Test G: Look-ahead bias prevention (changing future price leaves earlier indicators invariant)
- Test H: NVDA indicator endpoint
- Test I: BTC/USD indicator endpoint
- Test J: XAU/USD indicator endpoint
- Test K: API response schema validation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.indicators import calculate_sma, calculate_ema, compute_indicators, indicator_service
from app.services.cache_manager import CacheManager
from app.models.schemas import CleanHistoricalPoint, IndicatorsResponse

@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path):
    cm = CacheManager(cache_dir=tmp_path)
    with patch("app.services.market_data.cache_manager", cm):
        with patch("app.routes.market.cache_manager", cm):
            yield cm


# ----------------------------------------------------------------------
# A. SMA with a Manually Calculated Known Dataset
# ----------------------------------------------------------------------
def test_sma_known_dataset():
    """
    Test SMA with a manually calculated sequence:
    prices = [10, 20, 30, 40, 50], period = 3
    Expected SMA: [None, None, 20.0, 30.0, 40.0]
    """
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    sma = calculate_sma(prices, period=3)
    assert sma == [None, None, 20.0, 30.0, 40.0]

    # Additional manual calculation: period = 2
    # [None, (10+20)/2, (20+30)/2, (30+40)/2, (40+50)/2]
    sma_2 = calculate_sma(prices, period=2)
    assert sma_2 == [None, 15.0, 25.0, 35.0, 45.0]


# ----------------------------------------------------------------------
# B. EMA with a Manually Calculated Known Dataset Using SMA Initialization
# ----------------------------------------------------------------------
def test_ema_known_dataset():
    """
    Test EMA with manually calculated sequences using SMA seed initialization:
    Multiplier: alpha = 2 / (3 + 1) = 0.5
    Linear dataset: prices = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0], period = 3
    - index 0, 1: None
    - index 2: SMA = (2+4+6)/3 = 4.0
    - index 3: 8.0 * 0.5 + 4.0 * 0.5 = 6.0
    - index 4: 10.0 * 0.5 + 6.0 * 0.5 = 8.0
    - index 5: 12.0 * 0.5 + 8.0 * 0.5 = 10.0
    Expected EMA: [None, None, 4.0, 6.0, 8.0, 10.0]
    """
    prices = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    ema = calculate_ema(prices, period=3)
    assert ema == [None, None, 4.0, 6.0, 8.0, 10.0]

    # Non-linear dataset:
    # prices = [10.0, 11.0, 12.0, 14.0, 13.0], period = 3, alpha = 0.5
    # index 2: SMA = (10+11+12)/3 = 11.0
    # index 3: 14.0 * 0.5 + 11.0 * 0.5 = 7.0 + 5.5 = 12.5
    # index 4: 13.0 * 0.5 + 12.5 * 0.5 = 6.5 + 6.25 = 12.75
    prices_2 = [10.0, 11.0, 12.0, 14.0, 13.0]
    ema_2 = calculate_ema(prices_2, period=3)
    assert ema_2 == [None, None, 11.0, 12.5, 12.75]


# ----------------------------------------------------------------------
# C. Period Greater Than Available Data
# ----------------------------------------------------------------------
def test_period_greater_than_available_data():
    """
    When period > len(data):
    - all indicator values must be None
    - valid indicator counts must be zero
    - latest SMA and latest EMA must be None
    """
    prices = [10.0, 20.0, 30.0]
    sma = calculate_sma(prices, period=5)
    ema = calculate_ema(prices, period=5)
    assert sma == [None, None, None]
    assert ema == [None, None, None]

    # Test via compute_indicators
    pts = [
        CleanHistoricalPoint(
            timestamp=f"2026-09-{10+i}T00:00:00Z",
            open=10.0 + i, high=12.0 + i, low=9.0 + i, close=10.0 + i,
            volume=100.0, asset="NVIDIA", symbol="NVDA", source="Twelve Data", is_valid=True
        )
        for i in range(5)
    ]
    data_pts, summary = compute_indicators(pts, sma_period=10, ema_period=10)
    assert summary.total_records == 5
    assert summary.valid_sma_count == 0
    assert summary.valid_ema_count == 0
    assert summary.latest_sma is None
    assert summary.latest_ema is None
    assert all(p.sma is None for p in data_pts)
    assert all(p.ema is None for p in data_pts)


# ----------------------------------------------------------------------
# D. Period = 1
# ----------------------------------------------------------------------
def test_period_one_equals_close_price():
    """
    When period = 1:
    - SMA should equal close price exactly at every step
    - EMA should equal close price exactly at every step
    """
    prices = [10.5, 20.25, 30.75, 42.1]
    sma = calculate_sma(prices, period=1)
    ema = calculate_ema(prices, period=1)
    assert sma == prices
    assert ema == prices


# ----------------------------------------------------------------------
# E. Invalid Periods (0, -5, decimal, 'abc' -> HTTP 400)
# ----------------------------------------------------------------------
def test_invalid_periods_service_level():
    prices = [10.0, 20.0, 30.0]
    with pytest.raises(ValueError):
        calculate_sma(prices, 0)
    with pytest.raises(ValueError):
        calculate_sma(prices, -5)
    with pytest.raises(ValueError):
        calculate_ema(prices, 0)
    with pytest.raises(ValueError):
        calculate_ema(prices, -5)

@pytest.mark.asyncio
async def test_invalid_periods_http_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Period = 0
        resp_zero = await ac.get("/market/nvidia/indicators?sma_period=0")
        assert resp_zero.status_code == 400
        data_zero = resp_zero.json()
        assert data_zero["error"] == "INVALID_PERIOD"
        assert "positive integers greater than or equal to 1" in data_zero["message"]

        # Period = -5
        resp_neg = await ac.get("/market/nvidia/indicators?sma_period=-5")
        assert resp_neg.status_code == 400
        assert "positive integers greater than or equal to 1" in resp_neg.json()["message"]

        # Period = decimal
        resp_dec = await ac.get("/market/nvidia/indicators?sma_period=1.5")
        assert resp_dec.status_code == 400
        assert "positive integers greater than or equal to 1" in resp_dec.json()["message"]

        # Period = string 'abc'
        resp_str = await ac.get("/market/nvidia/indicators?sma_period=abc")
        assert resp_str.status_code == 400
        assert "positive integers greater than or equal to 1" in resp_str.json()["message"]

        # EMA period invalid
        resp_ema_zero = await ac.get("/market/nvidia/indicators?ema_period=0")
        assert resp_ema_zero.status_code == 400
        resp_ema_dec = await ac.get("/market/nvidia/indicators?ema_period=2.5")
        assert resp_ema_dec.status_code == 400
        resp_ema_str = await ac.get("/market/nvidia/indicators?ema_period=xyz")
        assert resp_ema_str.status_code == 400


# ----------------------------------------------------------------------
# F. Chronological Ordering
# ----------------------------------------------------------------------
def test_chronological_ordering():
    # Pass records in shuffled order to compute_indicators
    pts = [
        CleanHistoricalPoint(
            timestamp="2026-09-03T00:00:00Z", open=12.0, high=13.0, low=11.0, close=12.5,
            volume=100.0, asset="NVIDIA", symbol="NVDA", source="Twelve Data", is_valid=True
        ),
        CleanHistoricalPoint(
            timestamp="2026-09-01T00:00:00Z", open=10.0, high=11.0, low=9.0, close=10.5,
            volume=100.0, asset="NVIDIA", symbol="NVDA", source="Twelve Data", is_valid=True
        ),
        CleanHistoricalPoint(
            timestamp="2026-09-02T00:00:00Z", open=11.0, high=12.0, low=10.0, close=11.5,
            volume=100.0, asset="NVIDIA", symbol="NVDA", source="Twelve Data", is_valid=True
        ),
    ]
    data_pts, summary = compute_indicators(pts, sma_period=2, ema_period=2)
    timestamps = [p.timestamp for p in data_pts]
    assert timestamps == ["2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z", "2026-09-03T00:00:00Z"]
    assert timestamps == sorted(timestamps)


# ----------------------------------------------------------------------
# G. Look-Ahead Bias Prevention Test
# ----------------------------------------------------------------------
def test_look_ahead_bias_prevention():
    """
    CRITICAL TEST:
    Prove that changing a future price does NOT change any earlier SMA or EMA value.
    Example: If price at day 25 changes, indicator values for days 1–24 must remain
    exactly identical.
    """
    # 30-day simulated prices
    base_prices = [100.0 + (i * 1.5) + ((i % 3) * 0.5) for i in range(30)]

    original_sma = calculate_sma(base_prices, period=10)
    original_ema = calculate_ema(base_prices, period=10)

    # Modify price at Day 25 (index 24)
    modified_prices = list(base_prices)
    modified_prices[24] = 999999.0  # Massive price shock on day 25

    modified_sma = calculate_sma(modified_prices, period=10)
    modified_ema = calculate_ema(modified_prices, period=10)

    # Days 1 through 24 (indices 0 to 23) MUST be exactly identical
    for i in range(24):
        assert original_sma[i] == modified_sma[i], f"SMA look-ahead leak at index {i}!"
        assert original_ema[i] == modified_ema[i], f"EMA look-ahead leak at index {i}!"

    # At day 25 (index 24), values must differ
    assert original_sma[24] != modified_sma[24]
    assert original_ema[24] != modified_ema[24]


# ----------------------------------------------------------------------
# H, I, J, K. Asset Endpoint and Schema Tests (NVDA, BTC/USD, XAU/USD)
# ----------------------------------------------------------------------
@pytest.fixture
def mock_30_days_clean_points():
    def _generator(asset_name: str, symbol: str, base_price: float):
        pts = []
        for i in range(30):
            day_str = f"2026-08-{i+1:02d}T00:00:00Z"
            close_p = base_price + i * 2.0
            pts.append(CleanHistoricalPoint(
                timestamp=day_str,
                open=close_p - 1.0,
                high=close_p + 2.0,
                low=close_p - 2.0,
                close=close_p,
                volume=1000.0 if "BTC" not in symbol and "XAU" not in symbol else None,
                asset=asset_name,
                symbol=symbol,
                source="Twelve Data",
                is_valid=True
            ))
        return pts
    return _generator

@pytest.mark.asyncio
async def test_nvidia_indicators_endpoint(mock_30_days_clean_points):
    nvda_pts = mock_30_days_clean_points("NVIDIA", "NVDA", 110.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="NVIDIA",
            symbol="NVDA",
            source="Twelve Data",
            data_status="clean_verified",
            count=len(nvda_pts),
            quality_report=DataQualityReport(
                total_records=30, raw_records=30, duplicates_removed=0,
                invalid_records_dropped=0, missing_close_count=0,
                missing_volume_count=0, ohlc_anomalies_detected=0,
                quality_status="pristine"
            ),
            data=nvda_pts
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/market/nvidia/indicators?sma_period=20&ema_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "NVIDIA"
        assert data["symbol"] == "NVDA"
        assert data["source"] == "Twelve Data"
        assert data["data_status"] == "calculated"
        
        # Validate summary
        summary = data["summary"]
        assert summary["requested_sma_period"] == 20
        assert summary["requested_ema_period"] == 20
        assert summary["total_records"] == 30
        assert summary["valid_sma_count"] == 11  # 30 - 20 + 1 = 11
        assert summary["valid_ema_count"] == 11
        assert summary["latest_close"] == nvda_pts[-1].close
        assert summary["latest_sma"] is not None
        assert summary["latest_ema"] is not None

        # Validate data array
        assert len(data["data"]) == 30
        assert data["data"][0]["sma"] is None
        assert data["data"][0]["ema"] is None
        assert data["data"][19]["sma"] is not None
        assert data["data"][19]["ema"] is not None
        assert data["data"][-1]["sma"] == summary["latest_sma"]
        assert data["data"][-1]["ema"] == summary["latest_ema"]

        # Validate Schema
        validated = IndicatorsResponse(**data)
        assert validated.asset == "NVIDIA"

@pytest.mark.asyncio
async def test_bitcoin_indicators_endpoint(mock_30_days_clean_points):
    btc_pts = mock_30_days_clean_points("Bitcoin", "BTC/USD", 62000.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="Bitcoin",
            symbol="BTC/USD",
            source="Twelve Data",
            data_status="clean_verified",
            count=len(btc_pts),
            quality_report=DataQualityReport(
                total_records=30, raw_records=30, duplicates_removed=0,
                invalid_records_dropped=0, missing_close_count=0,
                missing_volume_count=30, ohlc_anomalies_detected=0,
                quality_status="pristine"
            ),
            data=btc_pts
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/market/bitcoin/indicators?sma_period=20&ema_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "Bitcoin"
        assert data["symbol"] == "BTC/USD"
        assert data["summary"]["total_records"] == 30
        assert data["summary"]["valid_sma_count"] == 11
        assert data["summary"]["valid_ema_count"] == 11

@pytest.mark.asyncio
async def test_gold_indicators_endpoint(mock_30_days_clean_points):
    gold_pts = mock_30_days_clean_points("Gold", "XAU/USD", 2600.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="Gold",
            symbol="XAU/USD",
            source="Twelve Data",
            data_status="clean_verified",
            count=len(gold_pts),
            quality_report=DataQualityReport(
                total_records=30, raw_records=30, duplicates_removed=0,
                invalid_records_dropped=0, missing_close_count=0,
                missing_volume_count=30, ohlc_anomalies_detected=0,
                quality_status="pristine"
            ),
            data=gold_pts
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/market/gold/indicators?sma_period=20&ema_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "Gold"
        assert data["symbol"] == "XAU/USD"
        assert data["summary"]["total_records"] == 30
        assert data["summary"]["valid_sma_count"] == 11
        assert data["summary"]["valid_ema_count"] == 11
