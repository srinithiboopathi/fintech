# API Reference

The **Quantexa** REST API provides endpoints for market data ingestion, data quality audits, technical indicator computation, and quantitative risk metrics.

Base URL: `http://127.0.0.1:8000`

---

## Endpoint Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | [`/health`](#1-system-health-check) | System status, provider configurations, and cache statistics |
| `GET` | [`/assets`](#2-list-supported-assets) | List of supported assets and metadata |
| `GET` | [`/market/{asset}/historical`](#3-normalized-historical-data) | Ingested raw historical daily prices |
| `GET` | [`/market/{asset}/latest`](#4-latest-market-price) | Latest available price quote |
| `GET` | [`/market/{asset}/data`](#5-clean-historical-data) | Validated, sorted, and cleaned historical dataset |
| `GET` | [`/market/{asset}/data/summary`](#6-data-quality-summary) | Executive data quality and validation audit |
| `GET` | [`/market/{asset}/indicators`](#7-technical-indicators-sma--ema) | Simple and Exponential Moving Averages |
| `GET` | [`/market/{asset}/risk-metrics`](#8-quantitative-risk-metrics) | Daily percentage returns and rolling volatility |
| `GET` | [`/market/{asset}/risk-analysis`](#9-quantitative-risk-analysis-sharpe-ratio--maximum-drawdown) | Annualized Sharpe ratio and continuous Maximum Drawdown |

---

## Supported Asset Identifiers

For all `{asset}` path parameters, the following names and symbols are accepted:

- **NVIDIA**: `nvidia`, `nvda`, `nvidia stock`
- **Bitcoin**: `bitcoin`, `btc/usd`, `btc`, `btcusd`, `btc-usd`
- **Gold**: `gold`, `xau/usd`, `xau`, `gld`, `xauusd`, `xau-usd`

---

## 1. System Health Check

### `GET /health`

Returns operational status, primary and fallback provider configurations, masked API keys, and cache hit/miss statistics.

#### Response: `200 OK`
```json
{
  "status": "healthy",
  "primary_provider": "twelve_data",
  "fallback_provider": "alpha_vantage",
  "twelve_data_configured": true,
  "twelve_data_masked_key": "**********287514",
  "alpha_vantage_configured": true,
  "alpha_vantage_masked_key": "************Z28G",
  "api_key_configured": true,
  "masked_key": "**********287514",
  "environment": "development",
  "timestamp": "2026-09-19T13:42:56Z",
  "cache_stats": {
    "total_cache_files": 9,
    "historical_entries": 3,
    "latest_entries": 3,
    "clean_entries": 3,
    "cache_dir": "c:\\Users\\asus\\OneDrive\\Desktop\\quantexa\\backend\\data\\cache"
  }
}
```

---

## 2. List Supported Assets

### `GET /assets`

Returns the universe of active assets supported for quantitative analysis.

#### Response: `200 OK`
```json
{
  "assets": [
    {
      "asset_id": "nvidia",
      "name": "NVIDIA",
      "symbol": "NVDA",
      "asset_class": "equity",
      "description": "NVIDIA Corporation (Equity / Stock)",
      "supported_routes": {
        "historical": "/market/nvidia/historical",
        "latest": "/market/nvidia/latest",
        "clean_data": "/market/nvidia/data",
        "summary": "/market/nvidia/data/summary",
        "indicators": "/market/nvidia/indicators",
        "risk_metrics": "/market/nvidia/risk-metrics"
      }
    },
    {
      "asset_id": "bitcoin",
      "name": "Bitcoin",
      "symbol": "BTC/USD",
      "asset_class": "cryptocurrency",
      "description": "Bitcoin USD (Cryptocurrency)",
      "supported_routes": {
        "historical": "/market/bitcoin/historical",
        "latest": "/market/bitcoin/latest",
        "clean_data": "/market/bitcoin/data",
        "summary": "/market/bitcoin/data/summary",
        "indicators": "/market/bitcoin/indicators",
        "risk_metrics": "/market/bitcoin/risk-metrics"
      }
    },
    {
      "asset_id": "gold",
      "name": "Gold",
      "symbol": "XAU/USD",
      "asset_class": "commodity",
      "description": "Gold Spot Bullion (XAU/USD) & SPDR Gold Shares (GLD)",
      "supported_routes": {
        "historical": "/market/gold/historical",
        "latest": "/market/gold/latest",
        "clean_data": "/market/gold/data",
        "summary": "/market/gold/data/summary",
        "indicators": "/market/gold/indicators",
        "risk_metrics": "/market/gold/risk-metrics"
      }
    }
  ],
  "count": 3
}
```

---

## 3. Normalized Historical Data

### `GET /market/{asset}/historical`

Retrieves normalized historical daily price bars ingested from Twelve Data (with Alpha Vantage fallback).

#### Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `outputsize` | `string` | `"compact"` | `"compact"` (latest ~30–100 bars) or `"full"` (extended history) |
| `refresh` | `boolean` | `false` | When `true`, bypasses local cache and fetches fresh provider data |

#### Response: `200 OK`
```json
{
  "asset": "nvidia",
  "symbol": "NVDA",
  "asset_class": "equity",
  "source": "twelve_data",
  "data_points": 30,
  "earliest_timestamp": "2026-02-02T00:00:00Z",
  "latest_timestamp": "2026-03-13T00:00:00Z",
  "data": [
    {
      "timestamp": "2026-03-13T00:00:00Z",
      "open": 121.20,
      "high": 123.50,
      "low": 120.10,
      "close": 122.75,
      "volume": 48291000.0,
      "asset": "nvidia",
      "symbol": "NVDA",
      "source": "twelve_data"
    }
  ]
}
```

---

## 4. Latest Market Price

### `GET /market/{asset}/latest`

Fetches the latest available price quote for the asset.

#### Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `refresh` | `boolean` | `false` | When `true`, forces a fresh quote request (bypassing the 60s cache) |

#### Response: `200 OK`
```json
{
  "asset": "nvidia",
  "symbol": "NVDA",
  "price": 122.75,
  "change": 1.55,
  "change_percent": 1.28,
  "timestamp": "2026-03-13T20:00:00Z",
  "source": "twelve_data",
  "data_nature": "latest_available"
}
```

---

## 5. Clean Historical Data

### `GET /market/{asset}/data`

Retrieves historical market data after running through the data cleaning and validation pipeline. Duplicate timestamps are removed, records are sorted chronologically ascending, and OHLC boundaries are strictly enforced.

#### Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `refresh` | `boolean` | `false` | Re-evaluates clean data from fresh provider input |

#### Response: `200 OK`
```json
{
  "asset": "bitcoin",
  "symbol": "BTC/USD",
  "source": "twelve_data",
  "total_records": 30,
  "records": [
    {
      "timestamp": "2026-02-12T00:00:00Z",
      "open": 68500.00,
      "high": 69400.00,
      "low": 67900.00,
      "close": 68950.00,
      "volume": null,
      "asset": "bitcoin",
      "symbol": "BTC/USD",
      "source": "twelve_data"
    }
  ]
}
```

---

## 6. Data Quality Summary

### `GET /market/{asset}/data/summary`

Returns executive metrics on data cleanliness, completeness, dropped invalid observations, and overall quality rating.

#### Query Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `refresh` | `boolean` | `false` | When `true`, forces re-computation of summary metrics |

#### Response: `200 OK`
```json
{
  "asset": "gold",
  "symbol": "XAU/USD",
  "source": "twelve_data",
  "total_records": 30,
  "earliest_timestamp": "2026-02-02T00:00:00Z",
  "latest_timestamp": "2026-03-13T00:00:00Z",
  "missing_close_count": 0,
  "missing_volume_count": 30,
  "duplicate_timestamps_dropped": 0,
  "invalid_records_dropped": 0,
  "latest_close": 2980.50,
  "quality_rating": "EXCELLENT"
}
```

---

## 7. Technical Indicators (SMA & EMA)

### `GET /market/{asset}/indicators`

Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA) over cleaned historical data.

#### Query Parameters

| Parameter | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `sma_period` | `string` | `"20"` | Positive integer $\ge 1$ | Lookback window for SMA |
| `ema_period` | `string` | `"20"` | Positive integer $\ge 1$ | Lookback window for EMA |
| `refresh` | `boolean` | `false` | `true` / `false` | Bypass cache |

#### Error Response: `400 Bad Request` (Invalid Period)
```json
{
  "detail": "Invalid indicator period: period must be a positive integer >= 1"
}
```

#### Response: `200 OK`
```json
{
  "asset": "nvidia",
  "symbol": "NVDA",
  "source": "twelve_data",
  "sma_period": 20,
  "ema_period": 20,
  "total_records": 30,
  "data": [
    {
      "timestamp": "2026-02-02T00:00:00Z",
      "close": 118.50,
      "sma": null,
      "ema": null
    },
    {
      "timestamp": "2026-02-27T00:00:00Z",
      "close": 122.10,
      "sma": 120.45,
      "ema": 120.45
    },
    {
      "timestamp": "2026-03-02T00:00:00Z",
      "close": 123.40,
      "sma": 120.78,
      "ema": 120.73
    }
  ]
}
```

---

## 8. Quantitative Risk Metrics

### `GET /market/{asset}/risk-metrics`

Calculates percentage daily returns and rolling sample volatility ($ddof=1$).

#### Query Parameters

| Parameter | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `volatility_period` | `string` | `"20"` | Positive integer $\ge 1$ | Rolling window for volatility |
| `refresh` | `boolean` | `false` | `true` / `false` | Bypass cache |

#### Error Response: `400 Bad Request` (Invalid Period)
```json
{
  "detail": "Invalid volatility period: period must be a positive integer >= 1"
}
```

#### Response: `200 OK`
```json
{
  "asset": "bitcoin",
  "symbol": "BTC/USD",
  "source": "twelve_data",
  "volatility_period": 20,
  "total_records": 30,
  "data": [
    {
      "timestamp": "2026-02-02T00:00:00Z",
      "close": 65000.0,
      "daily_return": null,
      "rolling_volatility": null
    },
    {
      "timestamp": "2026-02-03T00:00:00Z",
      "close": 66300.0,
      "daily_return": 0.020000,
      "rolling_volatility": null
    },
    {
      "timestamp": "2026-03-02T00:00:00Z",
      "close": 68900.0,
      "daily_return": 0.015000,
      "rolling_volatility": 0.024185
    }
  ]
}
```

---

## 9. Quantitative Risk Analysis (Sharpe Ratio & Maximum Drawdown)

### `GET /market/{asset}/risk-analysis`

Calculates annualized Sharpe Ratio and Maximum Drawdown analysis with continuous running peak and drawdown series.

#### Query Parameters

| Parameter | Type | Default | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `risk_free_rate` | `string` | `"0.0"` | Non-negative float $\ge 0.0$ | Annual risk-free rate percentage |
| `annualization_factor` | `string` | `"252"` | Positive integer $\ge 1$ | Annualization periods per year (e.g., 252 for stocks, 365 for crypto) |
| `refresh` | `boolean` | `false` | `true` / `false` | Bypass cache |

#### Error Response: `400 Bad Request` (Invalid Parameter)
```json
{
  "error": "INVALID_PARAMETER",
  "message": "Invalid risk analysis parameter: risk_free_rate must be a non-negative number and annualization_factor must be a positive integer greater than or equal to 1.",
  "status_code": 400,
  "details": {},
  "path": "/market/nvidia/risk-analysis"
}
```

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "data_status": "calculated",
  "summary": {
    "risk_free_rate": 0.0,
    "annualization_factor": 252,
    "valid_return_count": 29,
    "sharpe_ratio": 0.0351,
    "maximum_drawdown_pct": -8.4216,
    "maximum_drawdown_timestamp": "2026-09-14T00:00:00Z",
    "latest_close": 222.27
  },
  "drawdown_series": [
    {
      "timestamp": "2026-08-07T00:00:00Z",
      "close": 223.96,
      "running_peak": 223.96,
      "drawdown_pct": 0.0
    },
    {
      "timestamp": "2026-09-14T00:00:00Z",
      "close": 210.96,
      "running_peak": 230.36,
      "drawdown_pct": -8.4216
    },
    {
      "timestamp": "2026-09-18T00:00:00Z",
      "close": 222.27,
      "running_peak": 230.36,
      "drawdown_pct": -3.5119
    }
  ]
}
```

---

## Common Error Codes

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid Parameter | Provided `sma_period`, `ema_period`, or `volatility_period` is $< 1$, non-integer, or empty. |
| `404 Not Found` | Unsupported Asset | Requested asset identifier is not mapped to NVDA, BTC/USD, or XAU/USD. |
| `502 Bad Gateway` | Upstream API Error | Upstream market data provider failed or rate limit exceeded with no valid cache. |
| `504 Gateway Timeout` | Provider Timeout | Upstream provider failed to respond within connection timeout window. |
