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

## 4. Correlation & Asset Comparison Endpoints (Phase 5)

The Correlation and Asset Comparison Engine computes cross-asset Pearson correlation matrices, pairwise metrics, rolling correlation curves, and comparative risk/return performance on strictly aligned historical market dates.

---

### `GET /api/v1/correlation/matrix`
Calculates symmetric Pearson correlation matrix and pairwise observation counts across selected assets on overlapping return dates.

**Query Parameters**:
- `assets` (string, optional): Comma-separated asset list (e.g. `Gold,Bitcoin,NVIDIA`). Defaults to all assets.
- `start_date` (string `YYYY-MM-DD`, optional): Earliest date filter.
- `end_date` (string `YYYY-MM-DD`, optional): Latest date filter.

**Example Request**:
`GET /api/v1/correlation/matrix?assets=Gold,Bitcoin,NVIDIA`

**Response `200 OK`**:
```json
{
  "assets": ["Gold", "Bitcoin", "NVIDIA"],
  "matrix": {
    "Gold": {
      "Gold": 1.0,
      "Bitcoin": -0.0076,
      "NVIDIA": 0.0026
    },
    "Bitcoin": {
      "Gold": -0.0076,
      "Bitcoin": 1.0,
      "NVIDIA": 0.0326
    },
    "NVIDIA": {
      "Gold": 0.0026,
      "Bitcoin": 0.0326,
      "NVIDIA": 1.0
    }
  },
  "observation_counts": {
    "Gold": { "Gold": 6357, "Bitcoin": 251, "NVIDIA": 6352 },
    "Bitcoin": { "Gold": 251, "Bitcoin": 364, "NVIDIA": 251 },
    "NVIDIA": { "Gold": 6352, "Bitcoin": 251, "NVIDIA": 6777 }
  },
  "start_date": "1999-01-22",
  "end_date": "2025-12-31"
}
```

---

### `GET /api/v1/correlation/pair`
Calculates pairwise Pearson correlation coefficient, active overlapping trading days, and date coverage between two assets.

**Query Parameters**:
- `asset_a` (string, required): First asset identifier (e.g. `Gold`).
- `asset_b` (string, required): Second asset identifier (e.g. `Bitcoin`).
- `start_date` (string `YYYY-MM-DD`, optional): Date filter start.
- `end_date` (string `YYYY-MM-DD`, optional): Date filter end.

**Example Request**:
`GET /api/v1/correlation/pair?asset_a=Gold&asset_b=Bitcoin`

**Response `200 OK`**:
```json
{
  "asset_a": "Gold",
  "asset_b": "Bitcoin",
  "correlation": -0.0076,
  "observations": 251,
  "start_date": "2017-01-03",
  "end_date": "2017-12-29"
}
```

---

### `GET /api/v1/correlation/rolling`
Generates time-series of rolling Pearson correlation over a configurable window ($w \ge 2$) on aligned calendar dates.

**Query Parameters**:
- `asset_a` (string, required): First asset identifier (e.g. `Gold`).
- `asset_b` (string, required): Second asset identifier (e.g. `NVIDIA`).
- `window` (integer, default: `30`, min: `2`, max: `500`): Lookback window in days.
- `start_date` (string `YYYY-MM-DD`, optional): Date filter start.
- `end_date` (string `YYYY-MM-DD`, optional): Date filter end.

**Example Request**:
`GET /api/v1/correlation/rolling?asset_a=Gold&asset_b=NVIDIA&window=60`

**Response `200 OK`**:
```json
{
  "asset_a": "Gold",
  "asset_b": "NVIDIA",
  "window": 60,
  "count": 6352,
  "data": [
    {
      "date": "2025-12-31",
      "correlation": 0.045
    }
  ]
}
```

---

### `GET /api/v1/correlation/comparison`
Returns comparative risk, return, Sharpe, drawdown, and CAGR metrics across multiple assets with joint aligned record counts.

**Query Parameters**:
- `assets` (string, optional): Comma-separated asset list (e.g. `Gold,Bitcoin,NVIDIA`).
- `start_date` (string `YYYY-MM-DD`, optional): Date filter start.
- `end_date` (string `YYYY-MM-DD`, optional): Date filter end.

**Example Request**:
`GET /api/v1/correlation/comparison?assets=Gold,Bitcoin,NVIDIA`

**Response `200 OK`**:
```json
{
  "assets": [
    {
      "asset": "Gold",
      "start_date": "2000-08-30",
      "end_date": "2025-12-31",
      "records": 6358,
      "total_return": 14.8346,
      "annualized_return": 0.1152,
      "annualized_volatility": 0.1739,
      "sharpe_ratio": 0.7168,
      "maximum_drawdown": -0.4436
    },
    {
      "asset": "Bitcoin",
      "start_date": "2017-01-01",
      "end_date": "2017-12-31",
      "records": 365,
      "total_return": 13.1802,
      "annualized_return": 13.1802,
      "annualized_volatility": 0.7486,
      "sharpe_ratio": 3.737,
      "maximum_drawdown": -0.3952
    },
    {
      "asset": "NVIDIA",
      "start_date": "1999-01-22",
      "end_date": "2025-12-31",
      "records": 6778,
      "total_return": 454.492,
      "annualized_return": 0.2523,
      "annualized_volatility": 0.5962,
      "sharpe_ratio": 0.8277,
      "maximum_drawdown": -0.8972
    }
  ],
  "start_date": "1999-01-22",
  "end_date": "2025-12-31",
  "aligned_records": 250
}
```

---

---

## 5. Strategy Engine Endpoints (Phase 6)

The Strategy Engine provides deterministic, parameterized quantitative trading signal generators over historical market datasets (`Gold`, `Bitcoin`, `NVIDIA`). All calculations are strictly backward-looking, preserving full warm-up history before filtering.

### Standardized Signal Semantics
- **`BUY`**: Discrete crossing/entry event into a long/bullish regime.
- **`SELL`**: Discrete crossing/exit event into a short/bearish regime.
- **`HOLD`**: Inactive transition, warm-up phase, or sustained continuation of existing regime.

---

### `GET /api/v1/strategies/{asset}/sma-crossover`
Calculates Simple Moving Average (SMA) Crossover trading signals.

**Path Parameters**:
- `asset` (string): Canonical asset name or alias (e.g. `Gold`, `Bitcoin`, `NVIDIA`).

**Query Parameters**:
- `fast_period` (integer, default: `20`, constraint: `ge=2`): Lookback period for fast SMA.
- `slow_period` (integer, default: `50`, constraint: `ge=2`, `slow_period > fast_period`): Lookback period for slow SMA.
- `start_date` (string `YYYY-MM-DD`, optional): Start date filter.
- `end_date` (string `YYYY-MM-DD`, optional): End date filter.

**Example Request**:
`GET /api/v1/strategies/Gold/sma-crossover?fast_period=20&slow_period=50&start_date=2024-01-01`

**Response `200 OK`**:
```json
{
  "asset": "Gold",
  "strategy": "sma_crossover",
  "parameters": {
    "fast_period": 20,
    "slow_period": 50
  },
  "start_date": "2024-01-01",
  "end_date": null,
  "count": 501,
  "summary": {
    "buy": 4,
    "sell": 3,
    "hold": 494,
    "total": 501
  },
  "data": [
    {
      "date": "2024-01-02",
      "asset": "Gold",
      "close": 2064.20,
      "strategy": "sma_crossover",
      "signal": "HOLD",
      "fast_sma": 2045.15,
      "slow_sma": 2010.80,
      "short_ema": null,
      "long_ema": null,
      "momentum": null,
      "moving_average": null,
      "deviation": null
    }
  ]
}
```

---

### `GET /api/v1/strategies/{asset}/ema-trend`
Calculates Exponential Moving Average (EMA) Trend trading signals.

**Query Parameters**:
- `short_period` (integer, default: `20`, constraint: `ge=2`): Span for short EMA.
- `long_period` (integer, default: `50`, constraint: `ge=2`, `long_period > short_period`): Span for long EMA.
- `start_date` (string `YYYY-MM-DD`, optional): Start date filter.
- `end_date` (string `YYYY-MM-DD`, optional): End date filter.

**Example Request**:
`GET /api/v1/strategies/Bitcoin/ema-trend?short_period=20&long_period=50`

---

### `GET /api/v1/strategies/{asset}/momentum`
Calculates $N$-period continuous momentum and zero-line crossing trading signals.

**Query Parameters**:
- `lookback` (integer, default: `20`, constraint: `ge=1`): Momentum lookback window.
- `start_date` (string `YYYY-MM-DD`, optional): Start date filter.
- `end_date` (string `YYYY-MM-DD`, optional): End date filter.

**Example Request**:
`GET /api/v1/strategies/NVIDIA/momentum?lookback=20`

---

### `GET /api/v1/strategies/{asset}/mean-reversion`
Calculates rolling mean reversion deviation percentages and threshold entry/exit signals.

**Query Parameters**:
- `window` (integer, default: `20`, constraint: `ge=2`): Rolling moving average lookback window.
- `threshold` (float, default: `0.02`, constraint: `gt=0.0`): Percentage deviation trigger threshold ($\theta = 0.02 \implies \pm 2\%$).
- `start_date` (string `YYYY-MM-DD`, optional): Start date filter.
- `end_date` (string `YYYY-MM-DD`, optional): End date filter.

**Example Request**:
`GET /api/v1/strategies/Gold/mean-reversion?window=20&threshold=0.02`

---

### `GET /api/v1/strategies/{asset}/signals`
Unified dispatch endpoint supporting all quantitative trading strategies.

**Query Parameters**:
- `strategy` (string, required): Strategy identifier (`sma_crossover`, `ema_trend`, `momentum`, `mean_reversion`).
- `fast_period`, `slow_period`, `short_period`, `long_period`, `lookback`, `window`, `threshold`: Strategy hyperparameters.
- `start_date`, `end_date`: Date filters.

**Example Request**:
`GET /api/v1/strategies/NVIDIA/signals?strategy=sma_crossover&fast_period=20&slow_period=50`

---

## 6. Upcoming Endpoints (Scheduled by Phase)

| Endpoint | Method | Phase | Description |
|---|---|---|---|
| `/api/v1/backtest/run` | POST | Phase 7/8 | Run portfolio backtest with transaction costs |
| `/api/v1/robustness/monte-carlo` | POST | Phase 11 | Parameter sensitivity & Monte Carlo simulations |
| `/api/v1/regime/detect` | POST | Phase 12 | Classify market volatility and trend regimes |
| `/api/v1/report/generate` | POST | Phase 13 | Generate downloadable research teardown report |

