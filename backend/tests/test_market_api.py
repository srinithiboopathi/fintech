"""
Comprehensive Integration & Unit Tests for Market Data APIs (Phase 3).
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.market_service import market_service

client = TestClient(app)


class TestHealthEndpoints:
    def test_root_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_api_v1_health(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == "QUANTLAB API"


class TestMarketAssetsEndpoint:
    def test_get_assets_list(self):
        response = client.get("/api/v1/market/assets")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert len(data["assets"]) == 3
        
        symbols = [a["symbol"] for a in data["assets"]]
        assert "Gold" in symbols
        assert "Bitcoin" in symbols
        assert "NVIDIA" in symbols

        names = [a["name"] for a in data["assets"]]
        assert "Gold" in names
        assert "Bitcoin" in names
        assert "NVIDIA" in names


class TestAssetMetadataEndpoint:
    def test_get_gold_metadata(self):
        response = client.get("/api/v1/market/assets/Gold")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["records"] == 6358
        assert data["start_date"] == "2000-08-30"
        assert data["end_date"] == "2025-12-31"
        assert data["frequency"] == "daily"

    def test_get_bitcoin_metadata(self):
        response = client.get("/api/v1/market/assets/Bitcoin")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert data["records"] == 365
        assert data["start_date"] == "2017-01-01"
        assert data["end_date"] == "2017-12-31"
        assert data["frequency"] == "daily"

    def test_get_nvidia_metadata(self):
        response = client.get("/api/v1/market/assets/NVIDIA")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert data["records"] == 6778
        assert data["start_date"] == "1999-01-22"
        assert data["end_date"] == "2025-12-31"
        assert data["frequency"] == "daily"

    def test_case_insensitive_asset_metadata(self):
        for variant in ["gold", "GOLD", "btc", "bitcoin", "nvda", "nvidia"]:
            response = client.get(f"/api/v1/market/assets/{variant}")
            assert response.status_code == 200
            assert response.json()["records"] > 0

    def test_unknown_asset_metadata_returns_404(self):
        response = client.get("/api/v1/market/assets/Ethereum")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDateRangeEndpoint:
    def test_get_date_ranges_all_assets(self):
        response = client.get("/api/v1/market/date-range")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "Gold" in data["assets"]
        assert "Bitcoin" in data["assets"]
        assert "NVIDIA" in data["assets"]

        assert data["assets"]["Gold"]["start_date"] == "2000-08-30"
        assert data["assets"]["Gold"]["end_date"] == "2025-12-31"
        assert data["assets"]["Gold"]["records"] == 6358

        assert data["assets"]["Bitcoin"]["start_date"] == "2017-01-01"
        assert data["assets"]["Bitcoin"]["end_date"] == "2017-12-31"
        assert data["assets"]["Bitcoin"]["records"] == 365

        assert data["assets"]["NVIDIA"]["start_date"] == "1999-01-22"
        assert data["assets"]["NVIDIA"]["end_date"] == "2025-12-31"
        assert data["assets"]["NVIDIA"]["records"] == 6778


class TestAssetHistoricalDataEndpoint:
    def test_gold_history_default(self):
        response = client.get("/api/v1/market/Gold/history")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Gold"
        assert data["frequency"] == "daily"
        assert len(data["data"]) == 1000  # default limit
        assert data["count"] == 1000

        # Check first point schema
        point = data["data"][0]
        assert "date" in point
        assert "open" in point
        assert "high" in point
        assert "low" in point
        assert "close" in point
        assert "volume" in point
        assert point["asset"] == "Gold"
        assert point["open"] > 0
        assert point["high"] >= point["low"]

    def test_bitcoin_history_full(self):
        response = client.get("/api/v1/market/Bitcoin/history?limit=1000")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "Bitcoin"
        assert len(data["data"]) == 365  # All 365 days of 2017
        assert data["count"] == 365
        assert data["data"][0]["date"] == "2017-01-01"
        assert data["data"][-1]["date"] == "2017-12-31"

    def test_nvidia_history_limit(self):
        response = client.get("/api/v1/market/NVIDIA/history?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["asset"] == "NVIDIA"
        assert len(data["data"]) == 50
        assert data["count"] == 50

    def test_history_start_date_filter(self):
        response = client.get("/api/v1/market/NVIDIA/history?start_date=2024-01-01&limit=5000")
        assert response.status_code == 200
        data = response.json()
        assert all(p["date"] >= "2024-01-01" for p in data["data"])

    def test_history_end_date_filter(self):
        response = client.get("/api/v1/market/Gold/history?end_date=2005-01-01&limit=5000")
        assert response.status_code == 200
        data = response.json()
        assert all(p["date"] <= "2005-01-01" for p in data["data"])

    def test_history_date_range_inclusive(self):
        response = client.get("/api/v1/market/Bitcoin/history?start_date=2017-06-01&end_date=2017-06-30&limit=100")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 30  # 30 days in June
        assert data["data"][0]["date"] == "2017-06-01"
        assert data["data"][-1]["date"] == "2017-06-30"

    def test_history_unknown_asset_returns_404(self):
        response = client.get("/api/v1/market/UNKNOWN/history")
        assert response.status_code == 404

    def test_history_invalid_date_format_returns_400(self):
        response = client.get("/api/v1/market/Gold/history?start_date=not-a-date")
        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]

    def test_history_invalid_calendar_date_returns_400(self):
        response = client.get("/api/v1/market/Gold/history?start_date=2024-02-31")
        assert response.status_code == 400

    def test_history_start_after_end_returns_400(self):
        response = client.get("/api/v1/market/Gold/history?start_date=2024-01-01&end_date=2023-01-01")
        assert response.status_code == 400
        assert "start_date" in response.json()["detail"]
        assert "end_date" in response.json()["detail"]


class TestMultiAssetHistoryEndpoint:
    def test_multi_asset_history_default(self):
        response = client.get("/api/v1/market/history?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert data["frequency"] == "daily"
        assert len(data["data"]) == 100
        assert data["count"] == 100

    def test_multi_asset_history_specific_assets(self):
        response = client.get("/api/v1/market/history?assets=Gold,Bitcoin&start_date=2017-01-01&end_date=2017-01-10&limit=100")
        assert response.status_code == 200
        data = response.json()
        assets_found = set(p["asset"] for p in data["data"])
        assert assets_found.issubset({"Gold", "Bitcoin"})
        assert "NVIDIA" not in assets_found

    def test_multi_asset_invalid_date_range_returns_400(self):
        response = client.get("/api/v1/market/history?start_date=2025-01-01&end_date=2020-01-01")
        assert response.status_code == 400

    def test_limit_validation_out_of_bounds(self):
        # Limit > maximum allowed (20000) returns 422
        response = client.get("/api/v1/market/history?limit=999999")
        assert response.status_code == 422

        # Limit < 1 returns 422
        response = client.get("/api/v1/market/history?limit=0")
        assert response.status_code == 422


class TestDataIntegrityAndErrorHandling:
    def test_missing_processed_file_handling(self, tmp_path):
        from backend.app.services.market_service import MarketDataService
        empty_service = MarketDataService(processed_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            empty_service._get_dataset("Gold")

        with pytest.raises(FileNotFoundError):
            empty_service._get_combined_dataset()

    def test_processed_and_raw_files_unmodified(self):
        import pandas as pd
        from pathlib import Path
        
        root = Path(__file__).resolve().parents[2]
        proc_dir = root / "datasets" / "processed"
        raw_dir = root / "datasets" / "raw"

        # Check raw files exist
        assert (raw_dir / "gold" / "Gold_Spot_historical_data.csv").exists()
        assert (raw_dir / "bitcoin" / "BTC-2017min.csv").exists()
        assert (raw_dir / "nvidia" / "NVIDIA_historical_data.csv").exists()

        # Check processed row counts match Phase 2 baseline
        gold_df = pd.read_csv(proc_dir / "gold_daily.csv")
        btc_df = pd.read_csv(proc_dir / "bitcoin_daily.csv")
        nvda_df = pd.read_csv(proc_dir / "nvidia_daily.csv")
        market_df = pd.read_csv(proc_dir / "market_data.csv")

        assert len(gold_df) == 6358
        assert len(btc_df) == 365
        assert len(nvda_df) == 6778
        assert len(market_df) == 13501
