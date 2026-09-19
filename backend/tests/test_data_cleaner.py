import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
import pandas as pd

from app.main import app
from app.services.data_cleaner import data_cleaning_service, normalize_timestamp_to_utc_iso
from app.services.cache_manager import CacheManager
from app.models.schemas import HistoricalPoint, CleanHistoricalPoint

@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path):
    cm = CacheManager(cache_dir=tmp_path)
    with patch("app.services.market_data.cache_manager", cm):
        with patch("app.routes.market.cache_manager", cm):
            yield cm

# ----------------------------------------------------------------------
# 1. Timestamp Normalization Tests
# ----------------------------------------------------------------------
def test_normalize_timestamp_to_utc():
    assert normalize_timestamp_to_utc_iso("2026-09-18") == "2026-09-18T00:00:00Z"
    assert normalize_timestamp_to_utc_iso("2026-09-18 16:00:00") == "2026-09-18T16:00:00Z"
    assert normalize_timestamp_to_utc_iso("2026-09-18T16:00:00Z") == "2026-09-18T16:00:00Z"
    assert normalize_timestamp_to_utc_iso(None) is None
    assert normalize_timestamp_to_utc_iso("") is None
    assert normalize_timestamp_to_utc_iso("invalid_date") is None

# ----------------------------------------------------------------------
# 2. Duplicate Removal and Chronological Sorting
# ----------------------------------------------------------------------
def test_cleaner_duplicate_removal_and_sorting():
    raw_data = [
        {"timestamp": "2026-09-18", "open": 180.0, "high": 185.0, "low": 178.0, "close": 182.0, "volume": 1000.0},
        {"timestamp": "2026-09-16", "open": 175.0, "high": 177.0, "low": 173.0, "close": 176.0, "volume": 1200.0},
        # Duplicate timestamp of 2026-09-18
        {"timestamp": "2026-09-18", "open": 181.0, "high": 186.0, "low": 179.0, "close": 183.0, "volume": 900.0},
        {"timestamp": "2026-09-17", "open": 176.0, "high": 181.0, "low": 175.0, "close": 179.0, "volume": 1100.0},
    ]
    points, report = data_cleaning_service.clean_historical_records(
        raw_records=raw_data,
        asset_name="NVIDIA",
        symbol="NVDA",
        source="Twelve Data"
    )
    assert len(points) == 3
    assert report.duplicates_removed == 1
    assert report.total_records == 3
    # Check chronological ordering (oldest first)
    assert points[0].timestamp == "2026-09-16T00:00:00Z"
    assert points[1].timestamp == "2026-09-17T00:00:00Z"
    assert points[2].timestamp == "2026-09-18T00:00:00Z"
    # First occurrence preserved (open was 180.0, not 181.0)
    assert points[2].open == 180.0

# ----------------------------------------------------------------------
# 3. Missing, Non-Numeric, and Negative Price Detection
# ----------------------------------------------------------------------
def test_cleaner_detects_and_drops_invalid_prices():
    raw_data = [
        {"timestamp": "2026-09-15", "open": 100.0, "high": 105.0, "low": 98.0, "close": 102.0},
        # Missing close
        {"timestamp": "2026-09-16", "open": 100.0, "high": 105.0, "low": 98.0, "close": None},
        # Non-numeric close
        {"timestamp": "2026-09-17", "open": 100.0, "high": 105.0, "low": 98.0, "close": "corrupt_price"},
        # Negative close
        {"timestamp": "2026-09-18", "open": 100.0, "high": 105.0, "low": 98.0, "close": -50.0},
        # Zero price
        {"timestamp": "2026-09-19", "open": 0.0, "high": 105.0, "low": 98.0, "close": 100.0},
    ]
    points, report = data_cleaning_service.clean_historical_records(
        raw_records=raw_data,
        asset_name="NVIDIA",
        symbol="NVDA",
        source="Twelve Data"
    )
    assert len(points) == 1
    assert points[0].timestamp == "2026-09-15T00:00:00Z"
    assert report.invalid_records_dropped == 4
    assert report.missing_close_count == 1

# ----------------------------------------------------------------------
# 4. OHLC Relationship Bounds Validation
# ----------------------------------------------------------------------
def test_cleaner_validates_ohlc_relationships():
    raw_data = [
        # Anomaly 1: high is lower than open
        {"timestamp": "2026-09-15", "open": 105.0, "high": 102.0, "low": 98.0, "close": 100.0},
        # Anomaly 2: low is higher than close
        {"timestamp": "2026-09-16", "open": 100.0, "high": 105.0, "low": 103.0, "close": 98.0},
        # Anomaly 3: high is lower than low
        {"timestamp": "2026-09-17", "open": 100.0, "high": 90.0, "low": 110.0, "close": 95.0},
    ]
    points, report = data_cleaning_service.clean_historical_records(
        raw_records=raw_data,
        asset_name="NVIDIA",
        symbol="NVDA",
        source="Twelve Data"
    )
    assert len(points) == 3
    assert report.ohlc_anomalies_detected > 0
    for p in points:
        assert p.high >= p.low
        assert p.high >= p.open
        assert p.high >= p.close
        assert p.low <= p.open
        assert p.low <= p.close

# ----------------------------------------------------------------------
# 5. Strict Null Volume Preservation for Crypto and Gold
# ----------------------------------------------------------------------
def test_cleaner_preserves_null_volume():
    # Bitcoin crypto test: volume is None
    btc_raw = [
        {"timestamp": "2026-09-18", "open": 64000.0, "high": 65000.0, "low": 63800.0, "close": 64800.0, "volume": None},
        {"timestamp": "2026-09-19", "open": 64800.0, "high": 65500.0, "low": 64500.0, "close": 65200.0}  # absent volume
    ]
    btc_points, btc_report = data_cleaning_service.clean_historical_records(
        raw_records=btc_raw,
        asset_name="Bitcoin",
        symbol="BTC/USD",
        source="Twelve Data"
    )
    assert len(btc_points) == 2
    assert btc_points[0].volume is None  # STRICTLY None, NOT 0.0
    assert btc_points[1].volume is None  # STRICTLY None, NOT 0.0
    assert btc_report.missing_volume_count == 2

    # Stock test: volume is present float
    nvda_raw = [
        {"timestamp": "2026-09-18", "open": 180.0, "high": 185.0, "low": 178.0, "close": 182.0, "volume": 189000000.0}
    ]
    nvda_points, nvda_report = data_cleaning_service.clean_historical_records(
        raw_records=nvda_raw,
        asset_name="NVIDIA",
        symbol="NVDA",
        source="Twelve Data"
    )
    assert nvda_points[0].volume == 189000000.0
    assert nvda_report.missing_volume_count == 0

# ----------------------------------------------------------------------
# 6. Pandas DataFrame Conversion (Step 4 Readiness)
# ----------------------------------------------------------------------
def test_cleaner_to_dataframe():
    raw_data = [
        {"timestamp": "2026-09-17", "open": 170.0, "high": 175.0, "low": 169.0, "close": 174.0, "volume": 1000.0},
        {"timestamp": "2026-09-18", "open": 174.0, "high": 178.0, "low": 172.0, "close": 176.0, "volume": 1200.0}
    ]
    points, _ = data_cleaning_service.clean_historical_records(raw_data, "NVIDIA", "NVDA", "Twelve Data")
    df = data_cleaning_service.to_dataframe(points)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None  # UTC
    assert df["close"].iloc[0] == 174.0
    assert df["close"].iloc[1] == 176.0
    assert df["close"].dtype == "float64"

# ----------------------------------------------------------------------
# 7. Endpoint Tests: GET /market/{asset}/data and /market/{asset}/data/summary
# ----------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_clean_data_endpoint():
    mock_raw_points = [
        HistoricalPoint(
            timestamp="2026-09-18T00:00:00Z",
            open=178.5,
            high=180.25,
            low=177.1,
            close=179.35,
            volume=189000000.0,
            asset="NVIDIA",
            symbol="NVDA",
            source="Twelve Data"
        )
    ]
    with patch("app.services.market_data.MarketDataService.get_historical_data", new_callable=AsyncMock) as mock_hist:
        from app.models.schemas import HistoricalDataResponse
        mock_hist.return_value = HistoricalDataResponse(
            asset="NVIDIA",
            symbol="NVDA",
            source="Twelve Data",
            count=1,
            data=mock_raw_points
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/market/nvidia/data")

        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["symbol"] == "NVDA"
        assert data["data_status"] == "clean_verified"
        assert data["count"] == 1
        assert "quality_report" in data
        assert data["quality_report"]["quality_status"] == "pristine"
        assert data["data"][0]["close"] == 179.35

@pytest.mark.asyncio
async def test_get_clean_data_summary_endpoint():
    mock_raw_points = [
        HistoricalPoint(
            timestamp="2026-09-18T00:00:00Z",
            open=64500.0,
            high=65100.0,
            low=64200.0,
            close=64850.0,
            volume=None,
            asset="Bitcoin",
            symbol="BTC/USD",
            source="Twelve Data"
        )
    ]
    with patch("app.services.market_data.MarketDataService.get_historical_data", new_callable=AsyncMock) as mock_hist:
        from app.models.schemas import HistoricalDataResponse
        mock_hist.return_value = HistoricalDataResponse(
            asset="Bitcoin",
            symbol="BTC/USD",
            source="Twelve Data",
            count=1,
            data=mock_raw_points
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/market/bitcoin/data/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["symbol"] == "BTC/USD"
        assert data["total_records"] == 1
        assert data["duplicate_count"] == 0
        assert data["latest_close"] == 64850.0
        assert data["missing_value_count"]["volume"] == 1  # 1 null volume counted
        assert data["data_quality"] in ("pristine", "good")
