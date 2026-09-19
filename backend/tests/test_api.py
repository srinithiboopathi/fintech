import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.cache_manager import CacheManager

@pytest.fixture(autouse=True)
def isolate_cache(tmp_path):
    with patch("app.services.market_data.cache_manager", CacheManager(cache_dir=tmp_path)):
        with patch("app.routes.market.cache_manager", CacheManager(cache_dir=tmp_path)):
            yield

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "api_key_configured" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_assets_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/assets")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    symbols = [a["symbol"] for a in data["assets"]]
    assert "NVDA" in symbols
    assert "BTC/USD" in symbols
    assert "XAU/USD" in symbols

@pytest.mark.asyncio
async def test_unsupported_asset_historical():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/market/dogecoin/historical")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "UNSUPPORTED_ASSET"
    assert "dogecoin" in data["message"]

@pytest.mark.asyncio
async def test_unsupported_asset_latest():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/market/unknown_ticker/latest")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "UNSUPPORTED_ASSET"

@pytest.mark.asyncio
async def test_nvidia_historical_endpoint_mocked():
    mock_payload = {
        "Time Series (Daily)": {
            "2026-09-18": {
                "1. open": "118.50",
                "2. high": "120.00",
                "3. low": "117.20",
                "4. close": "119.80",
                "5. volume": "45000000"
            }
        }
    }
    with patch("app.services.market_data.settings.PRIMARY_PROVIDER", "alpha_vantage"):
        with patch("app.services.market_data.MarketDataService._fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_payload
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/market/nvidia/historical?refresh=true")
            assert response.status_code == 200
            data = response.json()
            assert data["asset"] == "NVIDIA"
            assert data["symbol"] == "NVDA"
            assert data["count"] == 1
            assert data["data"][0]["close"] == 119.80
            assert "Alpha Vantage" in data["data"][0]["source"]

@pytest.mark.asyncio
async def test_bitcoin_latest_endpoint_mocked():
    mock_payload = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "BTC",
            "2. From_Currency Name": "Bitcoin",
            "3. To_Currency Code": "USD",
            "5. Exchange Rate": "65120.50",
            "6. Last Refreshed": "2026-09-19 14:00:00",
            "8. Bid Price": "65120.00",
            "9. Ask Price": "65121.00"
        }
    }
    with patch("app.services.market_data.settings.PRIMARY_PROVIDER", "alpha_vantage"):
        with patch("app.services.market_data.MarketDataService._fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_payload
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/market/bitcoin/latest?refresh=true")
            assert response.status_code == 200
            data = response.json()
            assert data["asset"] == "Bitcoin"
            assert data["symbol"] == "BTC/USD"
            assert data["price"] == 65120.50
            assert data["data_status"] == "latest_available"

@pytest.mark.asyncio
async def test_gold_latest_endpoint_mocked():
    mock_payload = {
        "nominal": "XAUUSD",
        "timestamp": "2026-09-19 12:30:00",
        "price": "2658.90"
    }
    with patch("app.services.market_data.settings.PRIMARY_PROVIDER", "alpha_vantage"):
        with patch("app.services.market_data.MarketDataService._fetch_from_provider", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_payload
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/market/gold/latest?refresh=true")
            assert response.status_code == 200
            data = response.json()
            assert data["asset"] == "Gold"
            assert data["symbol"] == "XAU/USD"
            assert data["price"] == 2658.90
            assert data["data_status"] == "latest_available"
