import pytest
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from app.config import settings, SUPPORTED_ASSETS
from app.models.schemas import HistoricalPoint, LatestMarketDataResponse, HistoricalDataResponse
from app.services.twelve_data import TwelveDataService, parse_twelve_data_timestamp_to_utc_iso
from app.services.cache_manager import CacheManager
from app.services.market_data import MarketDataService
from app.utils.exceptions import TwelveDataRateLimitError, TwelveDataAuthError

# ----------------------------------------------------------------------
# Unit Test 1: Timestamp parsing
# ----------------------------------------------------------------------
def test_twelve_data_timestamp_parsing():
    assert parse_twelve_data_timestamp_to_utc_iso("2026-09-18") == "2026-09-18T00:00:00Z"
    assert parse_twelve_data_timestamp_to_utc_iso("2026-09-19 14:30:00") == "2026-09-19T14:30:00Z"
    assert parse_twelve_data_timestamp_to_utc_iso("2026-09-19T14:30:00Z") == "2026-09-19T14:30:00Z"

# ----------------------------------------------------------------------
# Unit Test 2: Volume normalization (Strict null for crypto/gold, float for stocks)
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_twelve_data_stock_historical_volume():
    service = TwelveDataService()
    mock_payload = {
        "meta": {"symbol": "NVDA"},
        "values": [
            {
                "datetime": "2026-09-18",
                "open": "178.50",
                "high": "180.25",
                "low": "177.10",
                "close": "179.35",
                "volume": "189452300"
            }
        ],
        "status": "ok"
    }
    with patch.object(service, "_fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload
        points = await service.get_historical_time_series(SUPPORTED_ASSETS["nvidia"], outputsize=1)
        assert len(points) == 1
        assert points[0].symbol == "NVDA"
        assert points[0].close == 179.35
        assert points[0].volume == 189452300.0
        assert points[0].source == "Twelve Data"

@pytest.mark.asyncio
async def test_twelve_data_crypto_historical_null_volume():
    service = TwelveDataService()
    mock_payload = {
        "meta": {"symbol": "BTC/USD"},
        "values": [
            {
                "datetime": "2026-09-18",
                "open": "64500.00",
                "high": "65100.00",
                "low": "64200.00",
                "close": "64850.00",
                "volume": None
            }
        ],
        "status": "ok"
    }
    with patch.object(service, "_fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload
        points = await service.get_historical_time_series(SUPPORTED_ASSETS["bitcoin"], outputsize=1)
        assert len(points) == 1
        assert points[0].symbol == "BTC/USD"
        assert points[0].volume is None  # MUST be None, NOT 0.0

@pytest.mark.asyncio
async def test_twelve_data_gold_historical_null_volume():
    service = TwelveDataService()
    mock_payload = {
        "meta": {"symbol": "XAU/USD"},
        "values": [
            {
                "datetime": "2026-09-18",
                "open": "2580.00",
                "high": "2595.00",
                "low": "2575.00",
                "close": "2586.50"
                # volume is completely absent
            }
        ],
        "status": "ok"
    }
    with patch.object(service, "_fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload
        points = await service.get_historical_time_series(SUPPORTED_ASSETS["gold"], outputsize=1)
        assert len(points) == 1
        assert points[0].symbol == "XAU/USD"
        assert points[0].volume is None  # MUST be None, NOT 0.0

# ----------------------------------------------------------------------
# Unit Test 3: Rate limit exception detection
# ----------------------------------------------------------------------
def test_twelve_data_rate_limit_exception():
    service = TwelveDataService()
    error_payload = {
        "status": "error",
        "code": 429,
        "message": "You have run out of API credits for this minute. Please wait or upgrade."
    }
    with pytest.raises(TwelveDataRateLimitError) as exc_info:
        service._check_provider_payload_errors(error_payload, context="time_series")
    assert "rate limit" in str(exc_info.value).lower()
    assert exc_info.value.status_code == 429

# ----------------------------------------------------------------------
# Unit Test 4: Cache Manager functionality
# ----------------------------------------------------------------------
def test_cache_manager_save_and_get(tmp_path: Path):
    cache = CacheManager(cache_dir=tmp_path)
    test_symbol = "BTC/USD"
    payload = {
        "asset": "Bitcoin",
        "symbol": "BTC/USD",
        "source": "Twelve Data",
        "data_status": "latest_available",
        "count": 1,
        "data": [
            {
                "timestamp": "2026-09-18T00:00:00Z",
                "open": 64500.0,
                "high": 65100.0,
                "low": 64200.0,
                "close": 64850.0,
                "volume": None,
                "asset": "Bitcoin",
                "symbol": "BTC/USD",
                "source": "Twelve Data"
            }
        ]
    }
    # Initially none
    assert cache.get_historical(test_symbol) is None

    # Save
    cache.save_historical(test_symbol, payload)

    # Cache hit
    cached = cache.get_historical(test_symbol, max_age_hours=1)
    assert cached is not None
    assert cached["asset"] == "Bitcoin"
    assert cached["data"][0]["volume"] is None

    # Stale fallback works even if age limit is 0
    stale = cache.get_stale_historical(test_symbol)
    assert stale is not None
    assert stale["symbol"] == "BTC/USD"

# ----------------------------------------------------------------------
# Unit Test 5: Orchestration and Fallback to Alpha Vantage
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_market_data_fallback_to_alpha_vantage(tmp_path: Path):
    cache = CacheManager(cache_dir=tmp_path)
    service = MarketDataService()

    # Mock Twelve Data raising rate limit error
    with patch("app.services.market_data.cache_manager", cache):
        with patch("app.services.market_data.twelve_data_service.get_historical_time_series", new_callable=AsyncMock) as mock_td:
            mock_td.side_effect = TwelveDataRateLimitError("Rate limit exceeded")

            # Mock Alpha Vantage returning valid fallback points
            fallback_response = HistoricalDataResponse(
                asset="NVIDIA",
                symbol="NVDA",
                source="Alpha Vantage (Fallback)",
                data_status="latest_available",
                count=1,
                data=[
                    HistoricalPoint(
                        timestamp="2026-09-18T00:00:00Z",
                        open=178.5,
                        high=180.25,
                        low=177.1,
                        close=179.35,
                        volume=189000000.0,
                        asset="NVIDIA",
                        symbol="NVDA",
                        source="Alpha Vantage"
                    )
                ]
            )

            with patch.object(service, "_get_alpha_vantage_historical", new_callable=AsyncMock) as mock_av:
                mock_av.return_value = fallback_response

                result = await service.get_historical_data("nvidia", refresh=True)
                assert result is not None
                assert result.symbol == "NVDA"
                assert "Alpha Vantage" in result.source
                mock_td.assert_called_once()
                mock_av.assert_called_once()
