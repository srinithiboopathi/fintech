"""
backend/tests/test_risk_metrics.py

Comprehensive Test Suite for Step 5 Returns & Volatility Analysis:
- TEST A: Percentage returns with known dataset [100, 105, 102] -> [None, 5.0, -2.8571]
- TEST B: Rolling sample volatility with known series (ddof=1)
- TEST C: First return observation is strictly None
- TEST D: Insufficient data for requested volatility period yields None
- TEST E: Period = 1 returns None (sample standard deviation ddof=1 is mathematically undefined)
- TEST F: Look-ahead bias prevention (future price shocks do not alter earlier returns or volatility)
- TEST G: Invalid periods (0, -5, 1.5, 'abc' -> HTTP 400)
- TEST H: NVDA, BTC/USD, and XAU/USD live/mock endpoint tests
- TEST I: API response schema validation
"""

import pytest
import math
from pathlib import Path
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.risk_metrics import (
    calculate_daily_returns,
    calculate_rolling_volatility,
    compute_risk_metrics,
    risk_metrics_service,
)
from app.services.cache_manager import CacheManager
from app.models.schemas import CleanHistoricalPoint, RiskMetricsResponse

@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path):
    cm = CacheManager(cache_dir=tmp_path)
    with patch("app.services.market_data.cache_manager", cm):
        with patch("app.routes.market.cache_manager", cm):
            yield cm


# ----------------------------------------------------------------------
# TEST A — Daily Returns Calculation on Known Dataset
# ----------------------------------------------------------------------
def test_daily_returns_known_dataset():
    """
    For prices: [100, 105, 102]
    Expected returns: [None, 5.0, approx -2.857142857]
    """
    prices = [100.0, 105.0, 102.0]
    returns = calculate_daily_returns(prices, precision=4)
    assert returns[0] is None
    assert returns[1] == 5.0
    assert pytest.approx(-2.8571, abs=1e-4) == returns[2]

    # Test unrounded precision
    raw_returns = calculate_daily_returns(prices, precision=None)
    assert raw_returns[0] is None
    assert pytest.approx(5.0) == raw_returns[1]
    assert pytest.approx(-2.857142857142857, rel=1e-6) == raw_returns[2]



# ----------------------------------------------------------------------
# TEST B — Rolling Volatility with Known Series (ddof=1)
# ----------------------------------------------------------------------
def test_rolling_volatility_known_series():
    """
    Given returns: [None, 1.0, 2.0, 3.0, 4.0, 5.0]
    For period = 5:
    Window = [1.0, 2.0, 3.0, 4.0, 5.0]
    Mean = 3.0
    Sum of squared deviations = (1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2
                              = 4 + 1 + 0 + 1 + 4 = 10.0
    Sample variance (ddof=1) = 10.0 / (5 - 1) = 2.5
    Sample std = sqrt(2.5) approx 1.58113883
    """
    returns = [None, 1.0, 2.0, 3.0, 4.0, 5.0]
    vols = calculate_rolling_volatility(returns, period=5, precision=4)

    # Indices 0 to 4 have fewer than 5 valid returns -> None
    assert vols[0] is None
    assert vols[1] is None
    assert vols[2] is None
    assert vols[3] is None
    assert vols[4] is None
    # Index 5 has 5 valid returns (indices 1..5)
    assert vols[5] == 1.5811

    # Raw float check
    raw_vols = calculate_rolling_volatility(returns, period=5, precision=None)
    assert pytest.approx(math.sqrt(2.5), rel=1e-6) == raw_vols[5]


# ----------------------------------------------------------------------
# TEST C — First Return Observation is Strictly None
# ----------------------------------------------------------------------
def test_first_return_strictly_none():
    prices = [50.0, 55.0, 60.0]
    returns = calculate_daily_returns(prices)
    assert returns[0] is None
    assert returns[1] is not None
    assert returns[2] is not None


# ----------------------------------------------------------------------
# TEST D — Insufficient Data Yields None
# ----------------------------------------------------------------------
def test_insufficient_data_yields_none():
    """
    When total observations < volatility_period:
    - All volatility values must be None
    - valid_volatility_count must be 0
    - latest_volatility must be None
    """
    pts = [
        CleanHistoricalPoint(
            timestamp=f"2026-09-{10+i}T00:00:00Z",
            open=100.0 + i, high=105.0 + i, low=95.0 + i, close=100.0 + (i * 2.0),
            volume=1000.0, asset="NVIDIA", symbol="NVDA", source="Twelve Data", is_valid=True
        )
        for i in range(10)
    ]
    # Requesting 20-period volatility on 10 records
    data_pts, summary = compute_risk_metrics(pts, volatility_period=20)
    assert summary.total_records == 10
    assert summary.valid_return_count == 9
    assert summary.valid_volatility_count == 0
    assert summary.latest_volatility is None
    assert all(p.volatility is None for p in data_pts)


# ----------------------------------------------------------------------
# TEST E — Period = 1 (Mathematically Undefined Sample Std -> None)
# ----------------------------------------------------------------------
def test_period_one_returns_none():
    """
    Sample standard deviation with 1 observation has ddof=1, making
    the denominator (N - 1) equal to 0.
    Dividing by zero is mathematically undefined.
    The service must return None rather than inventing a zero or arbitrary value.
    """
    returns = [None, 2.5, -1.2, 3.4, 0.5]
    vols = calculate_rolling_volatility(returns, period=1)
    assert all(v is None for v in vols)


# ----------------------------------------------------------------------
# TEST F — Look-Ahead Bias Prevention
# ----------------------------------------------------------------------
def test_look_ahead_bias_prevention():
    """
    Changing a future closing price must NOT alter any earlier return
    or volatility calculation.
    """
    # 30 days of prices
    base_prices = [100.0 + (i * 1.2) + ((i % 4) * 0.3) for i in range(30)]

    orig_returns = calculate_daily_returns(base_prices)
    orig_vols = calculate_rolling_volatility(orig_returns, period=10)

    # Shock price at Day 25 (index 24)
    shocked_prices = list(base_prices)
    shocked_prices[24] = 999999.0

    shocked_returns = calculate_daily_returns(shocked_prices)
    shocked_vols = calculate_rolling_volatility(shocked_returns, period=10)

    # Days 1 through 24 (indices 0 to 23) must be strictly identical
    for i in range(24):
        assert orig_returns[i] == shocked_returns[i], f"Return leak at index {i}!"
        assert orig_vols[i] == shocked_vols[i], f"Volatility leak at index {i}!"

    # At day 25 (index 24), values must differ
    assert orig_returns[24] != shocked_returns[24]
    assert orig_vols[24] != shocked_vols[24]


# ----------------------------------------------------------------------
# TEST G — Invalid Periods Rejection (HTTP 400)
# ----------------------------------------------------------------------
def test_invalid_period_service_level():
    returns = [None, 1.0, 2.0]
    with pytest.raises(ValueError):
        calculate_rolling_volatility(returns, 0)
    with pytest.raises(ValueError):
        calculate_rolling_volatility(returns, -5)

@pytest.mark.asyncio
async def test_invalid_periods_http_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Period = 0
        resp_zero = await ac.get("/market/nvidia/risk-metrics?volatility_period=0")
        assert resp_zero.status_code == 400
        data_zero = resp_zero.json()
        assert data_zero["error"] == "INVALID_PERIOD"
        assert "positive integer greater than or equal to 1" in data_zero["message"]

        # Period = -5
        resp_neg = await ac.get("/market/nvidia/risk-metrics?volatility_period=-5")
        assert resp_neg.status_code == 400
        assert "positive integer greater than or equal to 1" in resp_neg.json()["message"]

        # Period = 1.5 (decimal)
        resp_dec = await ac.get("/market/nvidia/risk-metrics?volatility_period=1.5")
        assert resp_dec.status_code == 400
        assert "positive integer greater than or equal to 1" in resp_dec.json()["message"]

        # Period = 'abc' (string)
        resp_str = await ac.get("/market/nvidia/risk-metrics?volatility_period=abc")
        assert resp_str.status_code == 400
        assert "positive integer greater than or equal to 1" in resp_str.json()["message"]


# ----------------------------------------------------------------------
# TEST H, I — Asset Endpoints & Schema Validation (NVDA, BTC/USD, XAU/USD)
# ----------------------------------------------------------------------
@pytest.fixture
def mock_30_days_clean_points():
    def _generator(asset_name: str, symbol: str, base_price: float):
        pts = []
        for i in range(30):
            day_str = f"2026-08-{i+1:02d}T00:00:00Z"
            close_p = base_price + (i * 1.5) + ((i % 3) * 0.4)
            pts.append(CleanHistoricalPoint(
                timestamp=day_str,
                open=close_p - 0.5,
                high=close_p + 1.0,
                low=close_p - 1.0,
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
async def test_nvidia_risk_metrics_endpoint(mock_30_days_clean_points):
    nvda_pts = mock_30_days_clean_points("NVIDIA", "NVDA", 110.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="NVIDIA",
            symbol="NVDA",
            source="Twelve Data",
            data_status="clean_verified",
            count=30,
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
            resp = await ac.get("/market/nvidia/risk-metrics?volatility_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "NVIDIA"
        assert data["symbol"] == "NVDA"
        assert data["source"] == "Twelve Data"
        assert data["data_status"] == "calculated"

        summary = data["summary"]
        assert summary["volatility_period"] == 20
        assert summary["total_records"] == 30
        assert summary["valid_return_count"] == 29
        # 30 records -> 29 returns. 20-period volatility has 29 - 20 + 1 = 10 valid windows
        assert summary["valid_volatility_count"] == 10
        assert summary["latest_close"] == nvda_pts[-1].close
        assert summary["latest_return"] is not None
        assert summary["latest_volatility"] is not None

        # Data array assertions
        assert len(data["data"]) == 30
        assert data["data"][0]["return_pct"] is None
        assert data["data"][0]["volatility"] is None
        assert data["data"][-1]["return_pct"] == summary["latest_return"]
        assert data["data"][-1]["volatility"] == summary["latest_volatility"]

        # Validate Schema
        validated = RiskMetricsResponse(**data)
        assert validated.asset == "NVIDIA"

@pytest.mark.asyncio
async def test_bitcoin_risk_metrics_endpoint(mock_30_days_clean_points):
    btc_pts = mock_30_days_clean_points("Bitcoin", "BTC/USD", 62000.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="Bitcoin",
            symbol="BTC/USD",
            source="Twelve Data",
            data_status="clean_verified",
            count=30,
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
            resp = await ac.get("/market/bitcoin/risk-metrics?volatility_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "Bitcoin"
        assert data["symbol"] == "BTC/USD"
        assert data["summary"]["total_records"] == 30
        assert data["summary"]["valid_return_count"] == 29
        assert data["summary"]["valid_volatility_count"] == 10

@pytest.mark.asyncio
async def test_gold_risk_metrics_endpoint(mock_30_days_clean_points):
    gold_pts = mock_30_days_clean_points("Gold", "XAU/USD", 2600.0)
    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_clean:
        from app.models.schemas import CleanMarketDataResponse, DataQualityReport
        mock_clean.return_value = CleanMarketDataResponse(
            asset="Gold",
            symbol="XAU/USD",
            source="Twelve Data",
            data_status="clean_verified",
            count=30,
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
            resp = await ac.get("/market/gold/risk-metrics?volatility_period=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset"] == "Gold"
        assert data["symbol"] == "XAU/USD"
        assert data["summary"]["total_records"] == 30
        assert data["summary"]["valid_return_count"] == 29
        assert data["summary"]["valid_volatility_count"] == 10
