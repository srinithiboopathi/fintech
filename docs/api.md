# QUANTLAB API Specification

This document defines the REST API surface for QUANTLAB.

## Base URL
- Development: `http://localhost:8000/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Redoc Reference: `http://localhost:8000/redoc`

---

## 1. System & Health

### `GET /health` / `GET /api/v1/health`
Checks server operational readiness.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "app_name": "QUANTLAB API",
  "environment": "development"
}
```

---

## 2. Market Data Endpoints (Phase 3)

The Market Data API exposes standardized, cleaned historical time-series datasets (`datasets/processed/`) across multiple asset classes:
- **Gold**: Commodity / Store of Value (6,358 daily records, 2000-08-30 to 2025-12-31)
- **Bitcoin**: Digital Asset / Cryptocurrency (365 daily records, 2017-01-01 to 2017-12-31)
- **NVIDIA**: Equities / Tech Semiconductor (6,778 daily records, 1999-01-22 to 2025-12-31)

### `GET /api/v1/market/assets`
Returns all available assets supported by QUANTLAB with category metadata.

**Response `200 OK`**:
```json
{
  "assets": [
    {
      "symbol": "Gold",
      "name": "Gold",
      "category": "Commodity"
    },
    {
      "symbol": "Bitcoin",
      "name": "Bitcoin",
      "category": "Cryptocurrency"
    },
    {
      "symbol": "NVIDIA",
      "name": "NVIDIA",
      "category": "Equities"
    }
  ]
}
```

---

### `GET /api/v1/market/date-range`
Returns the available historical date boundaries and record counts for all supported assets.

**Response `200 OK`**:
```json
{
  "assets": {
    "Gold": {
      "start_date": "2000-08-30",
      "end_date": "2025-12-31",
      "records": 6358
    },
    "Bitcoin": {
      "start_date": "2017-01-01",
      "end_date": "2017-12-31",
      "records": 365
    },
    "NVIDIA": {
      "start_date": "1999-01-22",
      "end_date": "2025-12-31",
      "records": 6778
    }
  }
}
```

---

### `GET /api/v1/market/assets/{asset}`
Returns structural metadata for a specific asset. Input identifier is case-insensitive (e.g., `Gold`, `gold`, `btc`, `nvda`).

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Response `200 OK`**:
```json
{
  "asset": "NVIDIA",
  "start_date": "1999-01-22",
  "end_date": "2025-12-31",
  "records": 6778,
  "frequency": "daily"
}
```

**Errors**:
- `404 Not Found`: Unknown asset symbol (e.g. `Ethereum`).

---

### `GET /api/v1/market/{asset}/history`
Retrieves daily OHLCV historical time-series bars for a single asset with optional date filtering and truncation limits.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `start_date` (string `YYYY-MM-DD`, optional): Earliest date to include (inclusive).
- `end_date` (string `YYYY-MM-DD`, optional): Latest date to include (inclusive).
- `limit` (integer, default: `1000`, min: `1`, max: `10000`): Maximum records to return.

**Example Request**:
`GET /api/v1/market/NVIDIA/history?start_date=2024-01-01&end_date=2024-12-31&limit=500`

**Response `200 OK`**:
```json
{
  "asset": "NVIDIA",
  "frequency": "daily",
  "count": 252,
  "data": [
    {
      "date": "2024-01-02",
      "asset": "NVIDIA",
      "open": 49.26,
      "high": 49.30,
      "low": 47.56,
      "close": 48.17,
      "volume": 411556000.0
    }
  ]
}
```

**Errors**:
- `400 Bad Request`: `start_date` > `end_date` or invalid date format.
- `404 Not Found`: Unknown asset symbol.
- `422 Unprocessable Entity`: `limit` out of range (e.g. `< 1` or `> 10000`).

---

### `GET /api/v1/market/history`
Retrieves filtered daily OHLCV time-series records across multiple assets from the unified `market_data.csv` dataset.

**Query Parameters**:
- `assets` (string, optional): Comma-separated list of assets (e.g. `Gold,Bitcoin,NVIDIA`).
- `start_date` (string `YYYY-MM-DD`, optional): Earliest date to include (inclusive).
- `end_date` (string `YYYY-MM-DD`, optional): Latest date to include (inclusive).
- `limit` (integer, default: `2000`, min: `1`, max: `20000`): Maximum records to return.

**Example Request**:
`GET /api/v1/market/history?assets=Gold,Bitcoin&start_date=2017-01-01&end_date=2017-01-07&limit=20`

**Response `200 OK`**:
```json
{
  "frequency": "daily",
  "count": 12,
  "data": [
    {
      "date": "2017-01-01",
      "asset": "Bitcoin",
      "open": 966.34,
      "high": 1005.00,
      "low": 960.53,
      "close": 997.75,
      "volume": 6850.5
    },
    {
      "date": "2017-01-03",
      "asset": "Gold",
      "open": 1156.40,
      "high": 1163.60,
      "low": 1146.50,
      "close": 1160.40,
      "volume": 204900.0
    }
  ]
}
```

**Errors**:
- `400 Bad Request`: `start_date` > `end_date` or invalid date format.
- `422 Unprocessable Entity`: `limit` out of range.

---

## 3. Quantitative Analysis Endpoints (Phase 4)

The Quantitative Engine computes technical trend indicators, returns, volatility metrics, risk-adjusted performance (Sharpe ratio), drawdown curves, and rolling metrics strictly from verified historical datasets.

---

### `GET /api/v1/quant/{asset}/indicators`
Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA) time-series for the specified asset.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `sma_period` (integer, default: `20`, min: `1`, max: `1000`): Lookback period for SMA.
- `ema_period` (integer, default: `20`, min: `1`, max: `1000`): Lookback period for EMA.
- `start_date` (string `YYYY-MM-DD`, optional): Analysis window start date.
- `end_date` (string `YYYY-MM-DD`, optional): Analysis window end date.

**Example Request**:
`GET /api/v1/quant/NVIDIA/indicators?sma_period=20&ema_period=50&start_date=2024-01-01&end_date=2024-01-10`

**Response `200 OK`**:
```json
{
  "asset": "NVIDIA",
  "frequency": "daily",
  "sma_period": 20,
  "ema_period": 50,
  "count": 6,
  "data": [
    {
      "date": "2024-01-02",
      "close": 48.14,
      "sma": 48.52,
      "ema": 47.91
    }
  ]
}
```

---

### `GET /api/v1/quant/{asset}/returns`
Calculates arithmetic daily percentage returns and compounded cumulative return growth series.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `start_date` (string `YYYY-MM-DD`, optional): Filter start date.
- `end_date` (string `YYYY-MM-DD`, optional): Filter end date.

**Response `200 OK`**:
```json
{
  "asset": "Bitcoin",
  "frequency": "daily",
  "count": 365,
  "data": [
    {
      "date": "2017-01-01",
      "close": 997.75,
      "daily_return": null,
      "cumulative_return": 0.0
    },
    {
      "date": "2017-01-02",
      "close": 1012.54,
      "daily_return": 0.0148,
      "cumulative_return": 0.0148
    }
  ]
}
```

---

### `GET /api/v1/quant/{asset}/volatility`
Calculates rolling daily volatility and rolling annualized volatility over a configurable window ($w \ge 2$). Annualization applies $N=365$ for Bitcoin and $N=252$ for Gold/NVIDIA.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `window` (integer, default: `20`, min: `2`, max: `500`): Rolling lookback window in days.
- `start_date` (string `YYYY-MM-DD`, optional): Filter start date.
- `end_date` (string `YYYY-MM-DD`, optional): Filter end date.

**Response `200 OK`**:
```json
{
  "asset": "Gold",
  "window": 20,
  "annualization_factor": 252,
  "count": 6358,
  "data": [
    {
      "date": "2025-12-31",
      "rolling_volatility": 0.0094,
      "annualized_volatility": 0.1492
    }
  ]
}
```

---

### `GET /api/v1/quant/{asset}/risk-metrics`
Returns annualized volatility, annualized Sharpe ratio (with configurable risk-free rate), and Maximum Drawdown (MDD).

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `risk_free_rate` (float, default: `0.0`): Annualized risk-free interest rate (e.g. `0.02` for 2%).
- `start_date` (string `YYYY-MM-DD`, optional): Analysis start date.
- `end_date` (string `YYYY-MM-DD`, optional): Analysis end date.

**Response `200 OK`**:
```json
{
  "asset": "NVIDIA",
  "start_date": "1999-01-22",
  "end_date": "2025-12-31",
  "records": 6778,
  "risk_free_rate": 0.0,
  "annualization_factor": 252,
  "annualized_volatility": 0.5962,
  "sharpe_ratio": 0.8277,
  "maximum_drawdown": -0.8972
}
```

---

### `GET /api/v1/quant/{asset}/rolling-performance`
Computes synchronized rolling returns, rolling volatility, rolling Sharpe ratio, and drawdown curve over a configurable window.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `window` (integer, default: `20`, min: `2`, max: `500`): Lookback window in days.
- `risk_free_rate` (float, default: `0.0`): Annualized risk-free rate.
- `start_date` (string `YYYY-MM-DD`, optional): Filter start date.
- `end_date` (string `YYYY-MM-DD`, optional): Filter end date.

**Response `200 OK`**:
```json
{
  "asset": "Gold",
  "window": 60,
  "count": 6358,
  "data": [
    {
      "date": "2025-12-31",
      "rolling_return": 0.125,
      "rolling_volatility": 0.162,
      "rolling_sharpe": 1.45,
      "drawdown": -0.042
    }
  ]
}
```

---

### `GET /api/v1/quant/{asset}/summary`
Generates a comprehensive statistical profile including cumulative return, annualized risk metrics, and return distribution metrics.

**Path Parameters**:
- `asset` (string, required): Asset identifier (`Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `risk_free_rate` (float, default: `0.0`): Annualized risk-free rate.
- `start_date` (string `YYYY-MM-DD`, optional): Analysis start date.
- `end_date` (string `YYYY-MM-DD`, optional): Analysis end date.

**Response `200 OK`**:
```json
{
  "asset": "Gold",
  "start_date": "2000-08-30",
  "end_date": "2025-12-31",
  "records": 6358,
  "latest_close": 4337.10,
  "cumulative_return": 14.8346,
  "annualized_volatility": 0.1739,
  "sharpe_ratio": 0.7168,
  "maximum_drawdown": -0.4436,
  "return_statistics": {
    "mean": 0.00048,
    "std": 0.01095,
    "min": -0.0935,
    "max": 0.1024,
    "positive_days": 3380,
    "negative_days": 2940
  }
}
```

---

## 4. Upcoming Endpoints (Scheduled by Phase)

| Endpoint | Method | Phase | Description |
|---|---|---|---|
| `/api/v1/quant/correlation` | POST | Phase 6 | Compute correlation matrices and rolling correlation |
| `/api/v1/strategy/signals` | POST | Phase 7 | Generate trading signals for configured strategy |
| `/api/v1/backtest/run` | POST | Phase 8 | Run portfolio backtest with transaction costs |
| `/api/v1/robustness/monte-carlo` | POST | Phase 11 | Parameter sensitivity & Monte Carlo simulations |
| `/api/v1/regime/detect` | POST | Phase 12 | Classify market volatility and trend regimes |
| `/api/v1/report/generate` | POST | Phase 13 | Generate downloadable research teardown report |
