import pytest
from app.services.market_data import parse_to_utc_iso, MarketDataService
from app.utils.exceptions import (
    AlphaVantageAuthError,
    AlphaVantageRateLimitError,
    AlphaVantageDataNotFoundError,
    AlphaVantageProviderError,
    UnsupportedAssetError,
)

@pytest.fixture
def service():
    return MarketDataService()

def test_parse_to_utc_iso():
    assert parse_to_utc_iso("2026-09-18") == "2026-09-18T00:00:00Z"
    assert parse_to_utc_iso("2026-09-19 10:38:45") == "2026-09-19T10:38:45Z"
    assert parse_to_utc_iso("2026-09-19T12:00:00Z") == "2026-09-19T12:00:00Z"

def test_normalize_stock_historical(service):
    sample_payload = {
        "Time Series (Daily)": {
            "2026-09-18": {
                "1. open": "118.50",
                "2. high": "120.00",
                "3. low": "117.20",
                "4. close": "119.80",
                "5. volume": "45000000"
            },
            "2026-09-17": {
                "1. open": "116.00",
                "2. high": "118.00",
                "3. low": "115.50",
                "4. close": "117.90",
                "5. volume": "42000000"
            }
        }
    }
    points = service._normalize_stock_historical(sample_payload, "NVIDIA", "NVDA")
    assert len(points) == 2
    # Check chronological ordering (2026-09-17 first, then 2026-09-18)
    assert points[0].timestamp == "2026-09-17T00:00:00Z"
    assert points[0].close == 117.90
    assert points[0].volume == 42000000.0
    assert points[0].asset == "NVIDIA"
    assert points[0].symbol == "NVDA"
    assert points[0].source == "Alpha Vantage"

    assert points[1].timestamp == "2026-09-18T00:00:00Z"
    assert points[1].close == 119.80

def test_normalize_stock_latest(service):
    sample_payload = {
        "Global Quote": {
            "01. symbol": "NVDA",
            "02. open": "118.50",
            "03. high": "120.25",
            "04. low": "117.10",
            "05. price": "119.85",
            "06. volume": "48000000",
            "07. latest trading day": "2026-09-18",
            "08. previous close": "117.90",
            "09. change": "1.95",
            "10. change percent": "1.654%"
        }
    }
    quote = service._normalize_stock_latest(sample_payload, "NVIDIA", "NVDA")
    assert quote.asset == "NVIDIA"
    assert quote.symbol == "NVDA"
    assert quote.price == 119.85
    assert quote.data_status == "latest_available"
    assert quote.source == "Alpha Vantage"
    assert quote.volume == 48000000.0
    assert quote.previous_close == 117.90

def test_normalize_crypto_historical(service):
    sample_payload = {
        "Time Series (Digital Currency Daily)": {
            "2026-09-19": {
                "1. open": "64500.00",
                "2. high": "65200.00",
                "3. low": "64100.00",
                "4. close": "64950.00",
                "5. volume": "12000.5"
            }
        }
    }
    points = service._normalize_crypto_historical(sample_payload, "Bitcoin", "BTC")
    assert len(points) == 1
    assert points[0].close == 64950.00
    assert points[0].symbol == "BTC"
    assert points[0].asset == "Bitcoin"
    assert points[0].timestamp == "2026-09-19T00:00:00Z"

def test_normalize_crypto_latest(service):
    sample_payload = {
        "Realtime Currency Exchange Rate": {
            "1. From_Currency Code": "BTC",
            "2. From_Currency Name": "Bitcoin",
            "3. To_Currency Code": "USD",
            "5. Exchange Rate": "64890.50",
            "6. Last Refreshed": "2026-09-19 12:45:00",
            "8. Bid Price": "64890.00",
            "9. Ask Price": "64891.00"
        }
    }
    quote = service._normalize_crypto_latest(sample_payload, "Bitcoin", "BTC")
    assert quote.asset == "Bitcoin"
    assert quote.symbol == "BTC"
    assert quote.price == 64890.50
    assert quote.timestamp == "2026-09-19T12:45:00Z"
    assert quote.data_status == "latest_available"

def test_normalize_gold_historical(service):
    sample_payload = {
        "nominal": "XAUUSD",
        "data": [
            {"date": "2026-09-18", "price": "2650.75"},
            {"date": "2026-09-17", "price": "2640.20"}
        ]
    }
    points = service._normalize_gold_history(sample_payload, "Gold", "XAU")
    assert len(points) == 2
    assert points[0].timestamp == "2026-09-17T00:00:00Z"
    assert points[0].close == 2640.20
    assert points[1].timestamp == "2026-09-18T00:00:00Z"
    assert points[1].close == 2650.75

def test_normalize_gold_latest(service):
    sample_payload = {
        "nominal": "XAUUSD",
        "timestamp": "2026-09-19 10:38:45",
        "price": "2655.40"
    }
    quote = service._normalize_gold_latest(sample_payload, "Gold", "XAU")
    assert quote.asset == "Gold"
    assert quote.symbol == "XAU"
    assert quote.price == 2655.40
    assert quote.timestamp == "2026-09-19T10:38:45Z"
    assert quote.data_status == "latest_available"

def test_error_detection_rate_limit(service):
    payload = {
        "Information": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
    }
    with pytest.raises(AlphaVantageRateLimitError):
        service._check_provider_payload_errors(payload)

    note_payload = {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
    }
    with pytest.raises(AlphaVantageRateLimitError):
        service._check_provider_payload_errors(note_payload)

def test_error_detection_invalid_api_key(service):
    payload = {
        "Error Message": "the parameter apikey is invalid or missing. Please claim your free API key on https://www.alphavantage.co"
    }
    with pytest.raises(AlphaVantageAuthError):
        service._check_provider_payload_errors(payload)
