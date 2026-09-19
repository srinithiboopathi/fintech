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

## 3. Upcoming Endpoints (Scheduled by Phase)

| Endpoint | Method | Phase | Description |
|---|---|---|---|
| `/api/v1/quant/indicators` | POST | Phase 4 | Calculate SMA, EMA, Volatility, Sharpe, Drawdown |
| `/api/v1/quant/correlation` | POST | Phase 6 | Compute correlation matrices and rolling correlation |
| `/api/v1/strategy/signals` | POST | Phase 7 | Generate trading signals for configured strategy |
| `/api/v1/backtest/run` | POST | Phase 8 | Run portfolio backtest with transaction costs |
| `/api/v1/robustness/monte-carlo` | POST | Phase 11 | Parameter sensitivity & Monte Carlo simulations |
| `/api/v1/regime/detect` | POST | Phase 12 | Classify market volatility and trend regimes |
| `/api/v1/report/generate` | POST | Phase 13 | Generate downloadable research teardown report |
