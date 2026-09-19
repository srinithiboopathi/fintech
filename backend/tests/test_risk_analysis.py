"""
backend/tests/test_risk_analysis.py

Comprehensive Test Suite for Step 6 Risk Analysis:
- Sharpe Ratio calculation with known dataset and risk-free rates
- Sharpe Ratio handles zero standard deviation (returns None)
- Sharpe Ratio handles insufficient returns (< 2 returns yields None)
- Maximum Drawdown calculation with known sequence
- Maximum Drawdown monotonically increasing prices (drawdown = 0.0)
- Maximum Drawdown single price observation
- Zero Look-Ahead Bias prevention
- Invalid query parameters validation (service level and HTTP 400)
- Endpoints for NVIDIA, Bitcoin, and Gold
"""

import math
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.schemas import (
    CleanHistoricalPoint,
    CleanMarketDataResponse,
    DataQualityReport,
    RiskAnalysisResponse,
)
from app.services.cache_manager import CacheManager
from app.services.risk_analysis import (
    calculate_sharpe_ratio,
    calculate_drawdown,
    compute_risk_analysis,
    risk_analysis_service,
)


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path):
    cm = CacheManager(cache_dir=tmp_path)
    with patch("app.services.market_data.cache_manager", cm):
        with patch("app.routes.market.cache_manager", cm):
            yield cm


# ----------------------------------------------------------------------
# 1. Sharpe Ratio Calculation with Known Dataset
# ----------------------------------------------------------------------
def test_sharpe_ratio_known_dataset():
    """
    Returns series: [1.0, 2.0, 3.0, 4.0, 5.0] (in percent)
    m = 5
    mean = 3.0%
    sample variance (ddof=1) = ((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 4
                             = (4 + 1 + 0 + 1 + 4) / 4 = 10 / 4 = 2.5
    sample std = sqrt(2.5) approx 1.58113883%
    
    1. Zero risk-free rate (TEST B):
       Daily excess return = 3.0 - 0 = 3.0%
       Daily Sharpe = 3.0 / sqrt(2.5) approx 1.897366596
       Annualized (N = 252): 1.897366596 * sqrt(252) approx 30.11976...
       Rounded (4 decimals): 30.1198
    """
    returns = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Test with risk_free_rate = 0.0
    sharpe_rf0 = calculate_sharpe_ratio(returns, risk_free_rate=0.0, annualization_factor=252, precision=4)
    expected_sharpe_0 = round((3.0 / math.sqrt(2.5)) * math.sqrt(252), 4)
    assert sharpe_rf0 == expected_sharpe_0
    assert sharpe_rf0 == 30.1198

    # Test with risk_free_rate = 2.0%
    daily_rf = 2.0 / 252.0
    expected_sharpe_rf2 = round(((3.0 - daily_rf) / math.sqrt(2.5)) * math.sqrt(252), 4)
    sharpe_rf2 = calculate_sharpe_ratio(returns, risk_free_rate=2.0, annualization_factor=252, precision=4)
    assert sharpe_rf2 == expected_sharpe_rf2
    assert sharpe_rf2 == 30.0401

    # Test with custom annualization factor (e.g. 365 for crypto)
    expected_crypto_sharpe = round((3.0 / math.sqrt(2.5)) * math.sqrt(365), 4)
    sharpe_crypto = calculate_sharpe_ratio(returns, risk_free_rate=0.0, annualization_factor=365, precision=4)
    assert sharpe_crypto == expected_crypto_sharpe


# ----------------------------------------------------------------------
# 2. Sharpe Ratio Zero Standard Deviation Returns None
# ----------------------------------------------------------------------
def test_sharpe_ratio_zero_std_returns_none():
    """
    When all returns are identical (e.g. constant 1.5%), standard deviation is 0.
    Dividing by zero should safely return None, not infinity or error.
    """
    constant_returns = [1.5, 1.5, 1.5, 1.5]
    sharpe = calculate_sharpe_ratio(constant_returns, risk_free_rate=0.0, annualization_factor=252)
    assert sharpe is None


# ----------------------------------------------------------------------
# 3. Sharpe Ratio Insufficient Returns
# ----------------------------------------------------------------------
def test_sharpe_ratio_insufficient_returns():
    """Fewer than 2 valid returns should return None."""
    assert calculate_sharpe_ratio([]) is None
    assert calculate_sharpe_ratio([None]) is None
    assert calculate_sharpe_ratio([None, 2.0]) is None  # Only 1 valid return
    assert calculate_sharpe_ratio([1.0]) is None


# ----------------------------------------------------------------------
# 4. Maximum Drawdown with Known Sequence
# ----------------------------------------------------------------------
def test_maximum_drawdown_known_sequence():
    """
    Prices: [100, 120, 110, 90, 100]
    t=0: P=100, Peak=100, DD = 0.0%
    t=1: P=120, Peak=120, DD = 0.0%
    t=2: P=110, Peak=120, DD = ((110/120) - 1)*100 = -8.3333%
    t=3: P=90,  Peak=120, DD = ((90/120) - 1)*100 = -25.0%
    t=4: P=100, Peak=120, DD = ((100/120) - 1)*100 = -16.6667%
    Max Drawdown = -25.0%
    """
    prices = [100.0, 120.0, 110.0, 90.0, 100.0]
    timestamps = [
        "2026-09-01T00:00:00Z",
        "2026-09-02T00:00:00Z",
        "2026-09-03T00:00:00Z",
        "2026-09-04T00:00:00Z",
        "2026-09-05T00:00:00Z",
    ]

    series, max_dd, max_dd_ts = calculate_drawdown(prices, timestamps, precision=4)

    assert len(series) == 5
    assert series[0].running_peak == 100.0
    assert series[0].drawdown_pct == 0.0

    assert series[1].running_peak == 120.0
    assert series[1].drawdown_pct == 0.0

    assert series[2].running_peak == 120.0
    assert series[2].drawdown_pct == -8.3333

    assert series[3].running_peak == 120.0
    assert series[3].drawdown_pct == -25.0

    assert series[4].running_peak == 120.0
    assert series[4].drawdown_pct == -16.6667

    assert max_dd == -25.0
    assert max_dd_ts == "2026-09-04T00:00:00Z"


# ----------------------------------------------------------------------
# 5. Maximum Drawdown Increasing Prices
# ----------------------------------------------------------------------
def test_maximum_drawdown_increasing_prices():
    """In a strictly bull market with continuously new highs, drawdown is always 0.0%."""
    prices = [100.0, 105.0, 110.0, 120.0, 130.0]
    timestamps = [f"2026-09-0{i+1}T00:00:00Z" for i in range(5)]

    series, max_dd, max_dd_ts = calculate_drawdown(prices, timestamps)
    assert max_dd == 0.0
    assert all(pt.drawdown_pct == 0.0 for pt in series)


# ----------------------------------------------------------------------
# 6. Maximum Drawdown Single Price
# ----------------------------------------------------------------------
def test_maximum_drawdown_single_price():
    """A single price observation has 0.0% drawdown."""
    series, max_dd, max_dd_ts = calculate_drawdown([150.0], ["2026-09-01T00:00:00Z"])
    assert max_dd == 0.0
    assert max_dd_ts == "2026-09-01T00:00:00Z"
    assert len(series) == 1
    assert series[0].drawdown_pct == 0.0


# ----------------------------------------------------------------------
# 7. Zero Look-Ahead Bias Prevention
# ----------------------------------------------------------------------
def test_look_ahead_bias_prevention():
    """
    Changing a future price (e.g. Day 25) must NOT alter any earlier
    drawdown values (Days 1–24).
    """
    base_prices = [100.0 + (i * 0.5) for i in range(30)]
    timestamps = [f"2026-09-{i+1:02d}T00:00:00Z" for i in range(30)]

    orig_series, orig_max_dd, _ = calculate_drawdown(base_prices, timestamps)

    # Shock a future price at day 25
    shocked_prices = list(base_prices)
    shocked_prices[24] = 10.0  # Massive crash in future

    shocked_series, shocked_max_dd, _ = calculate_drawdown(shocked_prices, timestamps)

    # Earlier indices (0 to 23) must be strictly identical
    for t in range(24):
        assert orig_series[t].running_peak == shocked_series[t].running_peak, f"Peak leak at index {t}"
        assert orig_series[t].drawdown_pct == shocked_series[t].drawdown_pct, f"Drawdown leak at index {t}"

    # Day 24 must reflect the shock
    assert orig_series[24].drawdown_pct != shocked_series[24].drawdown_pct
    assert shocked_max_dd < orig_max_dd


# ----------------------------------------------------------------------
# 8. Invalid Parameters Service-Level Validation
# ----------------------------------------------------------------------
def test_invalid_parameters_service_level():
    """Service level must raise ValueError on negative rf or invalid annualization factor."""
    dummy_returns = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError):
        calculate_sharpe_ratio(dummy_returns, risk_free_rate=-1.0)

    with pytest.raises(ValueError):
        calculate_sharpe_ratio(dummy_returns, annualization_factor=0)

    with pytest.raises(ValueError):
        calculate_sharpe_ratio(dummy_returns, annualization_factor=-252)


# ----------------------------------------------------------------------
# 9. Invalid Parameters HTTP 400 Validation
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_parameters_http_400():
    """FastAPI route must reject bad query parameters with HTTP 400 and INVALID_PARAMETER error code."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Negative risk-free rate
        resp_neg_rf = await client.get("/market/nvidia/risk-analysis?risk_free_rate=-2.0")
        assert resp_neg_rf.status_code == 400
        assert resp_neg_rf.json().get("error") == "INVALID_PARAMETER"

        # Non-numeric risk-free rate
        resp_str_rf = await client.get("/market/nvidia/risk-analysis?risk_free_rate=abc")
        assert resp_str_rf.status_code == 400

        # Zero annualization factor
        resp_zero_af = await client.get("/market/nvidia/risk-analysis?annualization_factor=0")
        assert resp_zero_af.status_code == 400

        # Negative annualization factor
        resp_neg_af = await client.get("/market/nvidia/risk-analysis?annualization_factor=-252")
        assert resp_neg_af.status_code == 400

        # Float annualization factor
        resp_dec_af = await client.get("/market/nvidia/risk-analysis?annualization_factor=252.5")
        assert resp_dec_af.status_code == 400

        # String annualization factor
        resp_str_af = await client.get("/market/nvidia/risk-analysis?annualization_factor=xyz")
        assert resp_str_af.status_code == 400


# ----------------------------------------------------------------------
# 10. NVIDIA Live / Mock Endpoint Verification
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_nvidia_risk_analysis_endpoint():
    """Tests /market/nvidia/risk-analysis endpoint with mock clean data."""
    mock_clean_points = [
        CleanHistoricalPoint(
            timestamp=f"2026-08-{i+1:02d}T00:00:00Z",
            open=100.0 + i,
            high=105.0 + i,
            low=98.0 + i,
            close=102.0 + i,
            volume=50000000.0,
            asset="NVIDIA",
            symbol="NVDA",
            source="Twelve Data"
        )
        for i in range(30)
    ]
    # Introduce a dip in the middle to create a drawdown
    mock_clean_points[15].close = 90.0

    mock_clean_resp = CleanMarketDataResponse(
        asset="NVIDIA",
        symbol="NVDA",
        source="Twelve Data",
        data_status="clean_verified",
        count=30,
        quality_report=DataQualityReport(
            total_records=30,
            raw_records=30,
            duplicates_removed=0,
            invalid_records_dropped=0,
            missing_close_count=0,
            missing_volume_count=0,
            ohlc_anomalies_detected=0,
            quality_status="pristine"
        ),
        data=mock_clean_points
    )

    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_get_clean:
        mock_get_clean.return_value = mock_clean_resp

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/market/nvidia/risk-analysis?risk_free_rate=0.0&annualization_factor=252")
            assert resp.status_code == 200
            data = resp.json()

            assert data["asset"] == "NVIDIA"
            assert data["symbol"] == "NVDA"
            assert data["source"] == "Twelve Data"
            assert data["data_status"] == "calculated"

            summary = data["summary"]
            assert summary["risk_free_rate"] == 0.0
            assert summary["annualization_factor"] == 252
            assert summary["valid_return_count"] == 29
            assert summary["sharpe_ratio"] is not None
            assert summary["maximum_drawdown_pct"] <= 0.0
            assert summary["maximum_drawdown_timestamp"] is not None
            assert summary["latest_close"] == mock_clean_points[-1].close

            drawdown_series = data["drawdown_series"]
            assert len(drawdown_series) == 30
            assert all("drawdown_pct" in pt for pt in drawdown_series)

            # Validate against Pydantic schema
            validated = RiskAnalysisResponse(**data)
            assert validated.asset == "NVIDIA"


# ----------------------------------------------------------------------
# 11. Bitcoin Live / Mock Endpoint Verification
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_bitcoin_risk_analysis_endpoint():
    """Tests /market/bitcoin/risk-analysis endpoint with mock clean data."""
    mock_clean_points = [
        CleanHistoricalPoint(
            timestamp=f"2026-08-{i+1:02d}T00:00:00Z",
            open=60000.0 + (i * 100),
            high=61000.0 + (i * 100),
            low=59000.0 + (i * 100),
            close=60500.0 + (i * 100),
            volume=None,
            asset="Bitcoin",
            symbol="BTC/USD",
            source="Twelve Data"
        )
        for i in range(30)
    ]

    mock_clean_resp = CleanMarketDataResponse(
        asset="Bitcoin",
        symbol="BTC/USD",
        source="Twelve Data",
        data_status="clean_verified",
        count=30,
        quality_report=DataQualityReport(
            total_records=30,
            raw_records=30,
            duplicates_removed=0,
            invalid_records_dropped=0,
            missing_close_count=0,
            missing_volume_count=30,
            ohlc_anomalies_detected=0,
            quality_status="pristine"
        ),
        data=mock_clean_points
    )

    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_get_clean:
        mock_get_clean.return_value = mock_clean_resp

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/market/bitcoin/risk-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["asset"] == "Bitcoin"
            assert data["symbol"] == "BTC/USD"
            assert data["summary"]["sharpe_ratio"] is not None
            assert "maximum_drawdown_pct" in data["summary"]


# ----------------------------------------------------------------------
# 12. Gold Live / Mock Endpoint Verification
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_gold_risk_analysis_endpoint():
    """Tests /market/gold/risk-analysis endpoint with mock clean data."""
    mock_clean_points = [
        CleanHistoricalPoint(
            timestamp=f"2026-08-{i+1:02d}T00:00:00Z",
            open=2500.0 + (i * 5),
            high=2520.0 + (i * 5),
            low=2490.0 + (i * 5),
            close=2510.0 + (i * 5),
            volume=None,
            asset="Gold",
            symbol="XAU/USD",
            source="Twelve Data"
        )
        for i in range(30)
    ]

    mock_clean_resp = CleanMarketDataResponse(
        asset="Gold",
        symbol="XAU/USD",
        source="Twelve Data",
        data_status="clean_verified",
        count=30,
        quality_report=DataQualityReport(
            total_records=30,
            raw_records=30,
            duplicates_removed=0,
            invalid_records_dropped=0,
            missing_close_count=0,
            missing_volume_count=30,
            ohlc_anomalies_detected=0,
            quality_status="pristine"
        ),
        data=mock_clean_points
    )

    with patch("app.services.market_data.MarketDataService.get_clean_data", new_callable=AsyncMock) as mock_get_clean:
        mock_get_clean.return_value = mock_clean_resp

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/market/gold/risk-analysis")
            assert resp.status_code == 200
            data = resp.json()
            assert data["asset"] == "Gold"
            assert data["symbol"] == "XAU/USD"
            assert data["summary"]["sharpe_ratio"] is not None
            assert "maximum_drawdown_pct" in data["summary"]
