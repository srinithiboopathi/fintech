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
| `GET` | [`/market/correlation`](#10-multi-asset-pearson-correlation-matrix) | Pairwise symmetric Pearson correlation matrix across multi-asset returns |
| `GET` | [`/market/correlation/rolling`](#11-rolling-pearson-correlation) | Configurable rolling Pearson correlation time series across asset pairs |
| `POST` | [`/market/{asset}/backtest`](#12-strategy-agnostic-portfolio-backtesting) | Generic historical portfolio simulation with Next-Observation execution |
| `POST` | [`/ai/chat`](#21-grounded-ai-financial-intelligence-chat) | Grounded AI chatbot answering quantitative queries with live platform context |
| `GET` | [`/ai/status`](#22-ai-assistant-provider-status) | Current AI service status, provider configuration, and masked API credentials |

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

## 10. Multi-Asset Pearson Correlation Matrix

### `GET /market/correlation`

Calculates a symmetric Pearson correlation matrix across multi-asset returns (`NVDA`, `BTC/USD`, `XAU/USD`) strictly using Step 3 cleaned historical market data.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `refresh` | `boolean` | No | `false` | Bypass local cache and force fresh data fetch and calculation |

#### Response: `200 OK`
```json
{
  "assets": [
    "NVIDIA",
    "Bitcoin",
    "Gold"
  ],
  "symbols": [
    "NVDA",
    "BTC/USD",
    "XAU/USD"
  ],
  "matrix": {
    "NVDA": {
      "NVDA": 1.0,
      "BTC/USD": 0.3007,
      "XAU/USD": 0.5311
    },
    "BTC/USD": {
      "NVDA": 0.3007,
      "BTC/USD": 1.0,
      "XAU/USD": 0.577
    },
    "XAU/USD": {
      "NVDA": 0.5311,
      "BTC/USD": 0.577,
      "XAU/USD": 1.0
    }
  },
  "observation_count": 19,
  "start_date": "2026-08-24",
  "end_date": "2026-09-18",
  "source": "Twelve Data",
  "data_status": "calculated",
  "methodology": "Pearson correlation on aligned daily percentage returns ((close_t / close_{t-1}) - 1)"
}
```

---

## 11. Rolling Pearson Correlation

### `GET /market/correlation/rolling`

Calculates rolling Pearson correlation time series across asset pairs over a configurable lookback window $W \ge 2$.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `window` | `integer` | No | `20` | Rolling correlation window in observations ($W \ge 2$) |
| `asset1` | `string` | No | `null` | Optional first asset identifier filter (e.g. `nvidia`, `bitcoin`, `gold`) |
| `asset2` | `string` | No | `null` | Optional second asset identifier filter |
| `refresh` | `boolean` | No | `false` | Bypass local cache and force fresh calculation |

#### Response: `200 OK`
```json
{
  "window": 20,
  "assets": [
    "NVIDIA",
    "Bitcoin",
    "Gold"
  ],
  "source": "Twelve Data",
  "data_status": "calculated",
  "pairs": [
    {
      "pair": "NVDA vs BTC/USD",
      "asset1": "NVDA",
      "asset2": "BTC/USD",
      "window": 20,
      "observation_count": 19,
      "valid_correlation_count": 0,
      "latest_correlation": null,
      "series": [
        {
          "timestamp": "2026-08-24",
          "correlation": null
        }
      ]
    },
    {
      "pair": "BTC/USD vs XAU/USD",
      "asset1": "BTC/USD",
      "asset2": "XAU/USD",
      "window": 20,
      "observation_count": 29,
      "valid_correlation_count": 10,
      "latest_correlation": 0.5191,
      "series": [
        {
          "timestamp": "2026-09-10",
          "correlation": 0.7118
        },
        {
          "timestamp": "2026-09-19",
          "correlation": 0.5191
        }
      ]
    }
  ]
}
```

---

## 12. Strategy-Agnostic Portfolio Backtesting

### `POST /market/{asset}/backtest`

Simulates historical portfolio performance using a generic sequence of trading signals (`BUY`, `SELL`, `HOLD`) and configurable parameters (capital, fee rate, allocation fraction).

**Next-Observation Execution Assumption**:
A signal generated at historical observation $t$ executes at observation $t+1$ at close price $P_{t+1}$, strictly eliminating look-ahead bias.

#### Path Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `asset` | `string` | Yes | Target asset identifier: `nvidia`, `bitcoin`, `gold` |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `refresh` | `boolean` | No | `false` | Bypass local cache and force fresh data calculation |

#### Request Body (`application/json`)

```json
{
  "initial_capital": 100000.0,
  "transaction_cost_rate": 0.001,
  "allocation_fraction": 1.0,
  "signals": [
    {
      "timestamp": "2026-08-07T00:00:00Z",
      "signal": "BUY"
    },
    {
      "timestamp": "2026-08-25T00:00:00Z",
      "signal": "SELL"
    }
  ]
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `initial_capital` | `float` | No | `100000.0` | Initial starting capital (must be $> 0$) |
| `transaction_cost_rate` | `float` | No | `0.001` | Transaction fee percentage rate per trade (must be $\ge 0$) |
| `allocation_fraction` | `float` | No | `1.0` | Fraction of cash deployed on BUY (must be in $(0.0, 1.0]$) |
| `signals` | `list` | Yes | - | Chronological array of `{ timestamp, signal }` points |

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "data_status": "calculated",
  "execution_model": "Next-Observation (Signal at t executes at t+1)",
  "performance": {
    "initial_capital": 100000.0,
    "final_portfolio_value": 101281.95,
    "total_return_pct": 1.28,
    "total_trades": 2,
    "winning_trades": 1,
    "losing_trades": 0,
    "win_rate_pct": 100.0,
    "total_fees_paid": 201.28,
    "maximum_drawdown_pct": -7.47,
    "maximum_drawdown_timestamp": "2026-08-24T00:00:00Z",
    "sharpe_ratio": 0.4755
  },
  "benchmark": {
    "benchmark_name": "Buy & Hold",
    "initial_value": 100000.0,
    "final_value": 99150.0,
    "total_return_pct": -0.85,
    "equity_curve": [...]
  },
  "trade_history": [
    {
      "trade_id": 1,
      "timestamp": "2026-08-10T00:00:00Z",
      "side": "BUY",
      "price": 104.97,
      "quantity": 951.70,
      "trade_value": 99900.10,
      "transaction_cost": 99.90,
      "resulting_cash": 0.0,
      "resulting_position": 951.70,
      "pnl": null,
      "pnl_percent": null
    }
  ],
  "equity_curve": [...]
}
```

---

## 13. Strategy Signals Generation

### `POST /market/{asset}/strategy/signals`

Generates deterministic, chronological trading signals (`BUY`, `SELL`, `HOLD`) for a specified asset using one of the four supported quantitative strategies:
1. `sma_crossover`: Dual Simple Moving Average Crossover (`short_period`, `long_period`)
2. `ema_trend`: Exponential Moving Average Trend Following (`ema_period`)
3. `momentum`: Lookback Rate-of-Change Momentum (`lookback`)
4. `mean_reversion`: Rolling Z-Score Mean Reversion (`lookback`, `entry_threshold`)

Strictly adheres to **Zero Look-Ahead Bias**: signals at observation $t$ use only observations $i \le t$.

#### Path Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `asset` | `string` | Yes | Target asset identifier: `nvidia`, `bitcoin`, `gold` |

#### Request Body (`application/json`)

```json
{
  "strategy": "mean_reversion",
  "parameters": {
    "lookback": 20,
    "entry_threshold": 1.0
  }
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `strategy` | `string` | Yes | - | Strategy name: `sma_crossover`, `ema_trend`, `momentum`, `mean_reversion` |
| `parameters` | `dict` | No | `{}` | Strategy-specific parameter overrides |

#### Supported Strategy Parameters

- **`sma_crossover`**:
  - `short_period` (int $\ge 1$, default 20)
  - `long_period` (int $\ge 2$, default 50, must satisfy `short_period < long_period`)
- **`ema_trend`**:
  - `ema_period` (int $\ge 1$, default 20)
- **`momentum`**:
  - `lookback` (int $\ge 1$, default 10)
- **`mean_reversion`**:
  - `lookback` (int $\ge 2$, default 20)
  - `entry_threshold` (float $> 0.0$, default 1.0)

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "strategy": "mean_reversion",
  "parameters": {
    "lookback": 20,
    "entry_threshold": 1.0
  },
  "source": "Twelve Data",
  "data_status": "calculated",
  "observation_count": 30,
  "start_date": "2026-08-07T00:00:00Z",
  "end_date": "2026-09-18T00:00:00Z",
  "signals": [
    {
      "timestamp": "2026-09-18T00:00:00Z",
      "close": 115.59,
      "signal": "HOLD",
      "indicators": {
        "z_score": 0.421,
        "rolling_mean": 114.20,
        "rolling_std": 3.30
      }
    }
  ]
}
```

---

## 14. Strategy End-to-End Backtest

### `POST /market/{asset}/strategy/backtest`

Runs end-to-end simulation by dispatching the specified strategy, extracting chronological `BUY`/`SELL`/`HOLD` signals, and causally executing them through the Step 8 `BacktestingEngine`.

**Causal Guarantee**:
Signals generated at observation $t$ execute at observation $t+1$ at close price $P_{t+1}$ with transaction costs applied and cash balances tracked.

#### Request Body (`application/json`)

```json
{
  "strategy": "ema_trend",
  "parameters": {
    "ema_period": 20
  },
  "initial_capital": 100000.0,
  "transaction_cost_rate": 0.001,
  "allocation": 1.0
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `strategy` | `string` | Yes | - | Strategy name (`sma_crossover`, `ema_trend`, `momentum`, `mean_reversion`) |
| `parameters` | `dict` | No | `{}` | Strategy parameters |
| `initial_capital` | `float` | No | `100000.0` | Initial capital ($> 0$) |
| `transaction_cost_rate` | `float` | No | `0.001` | Transaction fee rate ($\ge 0$) |
| `allocation` | `float` | No | `1.0` | Portfolio cash allocation fraction in $(0, 1]$ |

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "strategy": "ema_trend",
  "parameters": {
    "ema_period": 20
  },
  "source": "Twelve Data",
  "data_status": "calculated",
  "execution_model": "Next-Observation (Signal at t executes at t+1 at P_{t+1})",
  "initial_capital": 100000.0,
  "final_portfolio_value": 94476.56,
  "total_return": -5.52,
  "total_trades": 3,
  "number_of_trades": 3,
  "max_drawdown": -5.52,
  "maximum_drawdown": -5.52,
  "equity_curve": [...],
  "trade_history": [...],
  "benchmark_buy_and_hold": {
    "benchmark_name": "Buy & Hold",
    "initial_value": 100000.0,
    "final_value": 99150.0,
    "total_return_pct": -0.85,
    "equity_curve": [...]
  },
  "performance": {
    "initial_capital": 100000.0,
    "final_portfolio_value": 94476.56,
    "total_return_pct": -5.52,
    "total_trades": 3,
    "winning_trades": 0,
    "losing_trades": 2,
    "win_rate_pct": 0.0,
    "total_fees_paid": 293.44,
    "maximum_drawdown_pct": -5.52,
    "maximum_drawdown_timestamp": "2026-09-18T00:00:00Z",
    "sharpe_ratio": -1.24
  }
}
```

---

## 15. Strategy Comparison

### `POST /market/{asset}/strategy/compare`

Runs an objective, side-by-side comparison across trading strategies evaluated under **strictly identical market conditions**:
- Identical historical dataset and aligned time window
- Identical starting capital (`initial_capital`)
- Identical transaction fee percentage (`transaction_cost_rate`)
- Identical portfolio allocation fraction (`allocation`)
- Identical causal execution model ($t \to t+1$ at $P_{t+1}$)

**Quantitative Integrity**:
Results are strictly factual. Strategies are **never** ranked or labeled as "winner/best/loser".

#### Path Parameters

| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `asset` | `string` | Yes | Target asset identifier: `nvidia`, `bitcoin`, `gold` |

#### Request Body (`application/json`)

```json
{
  "initial_capital": 100000.0,
  "transaction_cost_rate": 0.001,
  "allocation": 1.0,
  "strategies": ["sma_crossover", "ema_trend", "momentum", "mean_reversion"]
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `initial_capital` | `float` | No | `100000.0` | Initial capital ($> 0$) |
| `transaction_cost_rate` | `float` | No | `0.001` | Transaction fee rate ($\ge 0$) |
| `allocation` | `float` | No | `1.0` | Cash allocation fraction in $(0, 1]$ |
| `strategies` | `list` | No | All 4 | Optional subset of strategies to compare |
| `strategy_configs` | `dict` | No | `{}` | Optional parameter overrides per strategy |

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "data_status": "calculated",
  "execution_model": "Next-Observation (Signal at t executes at t+1 at P_{t+1})",
  "observation_count": 30,
  "start_date": "2026-08-07T00:00:00Z",
  "end_date": "2026-09-18T00:00:00Z",
  "benchmark": {
    "benchmark_name": "Buy & Hold",
    "initial_value": 100000.0,
    "final_value": 99150.0,
    "total_return_pct": -0.85,
    "equity_curve": [...]
  },
  "strategies": [
    {
      "strategy": "sma_crossover",
      "parameters": {"short_period": 20, "long_period": 50},
      "initial_capital": 100000.0,
      "final_portfolio_value": 100000.0,
      "total_return": 0.0,
      "total_trades": 0,
      "number_of_trades": 0,
      "winning_trades": 0,
      "losing_trades": 0,
      "win_rate_pct": null,
      "maximum_drawdown": 0.0,
      "max_drawdown": 0.0,
      "sharpe_ratio": null,
      "total_fees_paid": 0.0,
      "benchmark_return": -0.85,
      "excess_return_vs_benchmark": 0.85
    },
    {
      "strategy": "mean_reversion",
      "parameters": {"lookback": 20, "entry_threshold": 1.0},
      "initial_capital": 100000.0,
      "final_portfolio_value": 104655.68,
      "total_return": 4.66,
      "total_trades": 1,
      "number_of_trades": 1,
      "winning_trades": 1,
      "losing_trades": 0,
      "win_rate_pct": 100.0,
      "maximum_drawdown": -0.1,
      "max_drawdown": -0.1,
      "sharpe_ratio": 1.15,
      "total_fees_paid": 194.8,
      "benchmark_return": -0.85,
      "excess_return_vs_benchmark": 5.51
    }
  ]
}
```

---

## 16. Parameter Robustness & Sensitivity Analysis

### `POST /market/{asset}/strategy/robustness`

Performs controlled, bounded parameter sensitivity testing across discrete parameter grids for a chosen strategy.

**Platform Protection**:
- Parameter combinations are capped at a maximum of **50 combinations** per request to prevent Denial of Service.
- Validates all values and enforces logical constraints (e.g. `short_period < long_period` for SMA).
- Every evaluated combination is returned factually without silently selecting the "optimal" or "best" setting.

#### Request Body (`application/json`)

```json
{
  "strategy": "ema_trend",
  "parameter_grid": {
    "ema_period": [10, 20, 30]
  },
  "initial_capital": 100000.0,
  "transaction_cost_rate": 0.001,
  "allocation": 1.0
}
```

#### Response: `200 OK`
```json
{
  "asset": "Bitcoin",
  "symbol": "BTC/USD",
  "strategy": "ema_trend",
  "source": "Twelve Data",
  "data_status": "calculated",
  "execution_model": "Next-Observation (Signal at t executes at t+1 at P_{t+1})",
  "observation_count": 30,
  "start_date": "2026-08-21T00:00:00Z",
  "end_date": "2026-09-19T00:00:00Z",
  "benchmark": {
    "benchmark_name": "Buy & Hold",
    "initial_value": 100000.0,
    "final_value": 103670.0,
    "total_return_pct": 3.67,
    "equity_curve": [...]
  },
  "total_combinations_tested": 3,
  "results": [
    {
      "strategy": "ema_trend",
      "parameters": {"ema_period": 10},
      "initial_capital": 100000.0,
      "final_portfolio_value": 98400.47,
      "total_return": -1.6,
      "total_trades": 7,
      "number_of_trades": 7,
      "maximum_drawdown": -2.54,
      "max_drawdown": -2.54,
      "sharpe_ratio": -0.62,
      "total_fees_paid": 595.2,
      "benchmark_return": 3.67,
      "excess_return_vs_benchmark": -5.27
    },
    {
      "strategy": "ema_trend",
      "parameters": {"ema_period": 20},
      "initial_capital": 100000.0,
      "final_portfolio_value": 100440.6,
      "total_return": 0.44,
      "total_trades": 3,
      "number_of_trades": 3,
      "maximum_drawdown": -0.1,
      "max_drawdown": -0.1,
      "sharpe_ratio": 0.22,
      "total_fees_paid": 298.5,
      "benchmark_return": 3.67,
      "excess_return_vs_benchmark": -3.23
    }
  ]
}
```

---

## 17. Market Regime Analysis

### `GET /market/{asset}/regimes`

Classifies historical daily observations into deterministic trend, volatility, and combined market regimes with strict zero look-ahead protection.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `trend_period` | `integer` | No | `50` | SMA lookback period for trend classification ($1 \le n \le 500$) |
| `volatility_window` | `integer` | No | `20` | Rolling returns window for volatility calculation ($2 \le n \le 500$) |
| `volatility_threshold` | `float` | No | `None` | Optional fixed daily percentage volatility threshold. If omitted, causal expanding median is used |
| `trend_threshold` | `float` | No | `0.0` | Optional neutral band fraction around SMA for sideways trend ($0.0 \le t \le 1.0$) |
| `refresh` | `boolean` | No | `false` | Bypass local cache and force fresh data calculation |

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "data_status": "calculated",
  "parameters": {
    "trend_period": 50,
    "volatility_window": 20,
    "volatility_threshold": 2.15,
    "trend_threshold": 0.0
  },
  "observation_count": 30,
  "start_date": "2026-08-21T00:00:00Z",
  "end_date": "2026-09-19T00:00:00Z",
  "data": [
    {
      "timestamp": "2026-09-19T00:00:00Z",
      "close": 118.5,
      "sma": 112.4,
      "rolling_volatility": 1.85,
      "trend_state": "BULLISH",
      "volatility_state": "LOW_VOLATILITY",
      "combined_regime": "BULLISH_LOW_VOL"
    }
  ]
}
```

---

## 18. Market Regimes Distribution Summary

### `GET /market/{asset}/regimes/summary`

Returns an executive distribution summary of detected market regimes, including observation counts, percentage distribution across regimes, and historical start/end dates.

#### Query Parameters

Same query parameters as `/regimes` (`trend_period`, `volatility_window`, `volatility_threshold`, `trend_threshold`, `refresh`).

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "data_status": "calculated",
  "parameters": {
    "trend_period": 10,
    "volatility_window": 5,
    "volatility_threshold": 2.15,
    "trend_threshold": 0.0
  },
  "total_observations": 30,
  "observation_count": 30,
  "start_date": "2026-08-21T00:00:00Z",
  "end_date": "2026-09-19T00:00:00Z",
  "regimes": [
    {
      "regime": "BULLISH_HIGH_VOL",
      "observation_count": 9,
      "percentage": 30.0,
      "percentage_of_observations": 30.0,
      "start_date": "2026-08-28T00:00:00Z",
      "end_date": "2026-09-12T00:00:00Z"
    },
    {
      "regime": "BEARISH_LOW_VOL",
      "observation_count": 8,
      "percentage": 26.67,
      "percentage_of_observations": 26.67,
      "start_date": "2026-08-25T00:00:00Z",
      "end_date": "2026-09-18T00:00:00Z"
    },
    {
      "regime": "UNKNOWN",
      "observation_count": 9,
      "percentage": 30.0,
      "percentage_of_observations": 30.0,
      "start_date": "2026-08-21T00:00:00Z",
      "end_date": "2026-08-29T00:00:00Z"
    }
  ]
}
```

---

## 19. Strategy Performance by Market Regime

### `GET /market/{asset}/regimes/performance`

Evaluates the factual performance and risk metrics (observations, trades, compound return, maximum drawdown) of each quantitative strategy across detected market regimes. Factual metrics only; no subjective ranking or "winner/loser" labeling.

#### Query Parameters

Same query parameters as `/regimes` (`trend_period`, `volatility_window`, `volatility_threshold`, `trend_threshold`, `refresh`).

#### Response: `200 OK`
```json
{
  "asset": "NVIDIA",
  "symbol": "NVDA",
  "source": "Twelve Data",
  "parameters": {
    "trend_period": 10,
    "volatility_window": 5,
    "volatility_threshold": 2.15,
    "trend_threshold": 0.0
  },
  "performances": [
    {
      "strategy": "sma_crossover",
      "regime": "BULLISH_HIGH_VOL",
      "observations": 9,
      "trades": 1,
      "total_return": 3.45,
      "maximum_drawdown": 1.2
    },
    {
      "strategy": "ema_trend",
      "regime": "BEARISH_LOW_VOL",
      "observations": 8,
      "trades": 2,
      "total_return": -0.85,
      "maximum_drawdown": 2.1
    }
  ]
}
```

---

## 20. Quantexa Web Application Viewer & Static Assets

### `GET /viewer`

Serves the **Quantexa** financial intelligence dashboard single-page web application (`frontend/index.html`).

#### Static Asset Mounts
- `GET /css/{path}`: Serves stylesheet assets from `frontend/css/` (e.g. `/css/styles.css`).
- `GET /js/{path}`: Serves modular JavaScript components from `frontend/js/` (`/js/api.js`, `/js/charts.js`, `/js/app.js`).

#### Response: `200 OK`
Content-Type: `text/html; charset=utf-8`

---

## 21. Grounded AI Financial Intelligence Chat

### `POST /ai/chat`

Processes natural-language financial queries, routes to existing quantitative services for factual data retrieval, and generates numerically grounded responses via server-side LLMs (Gemini / OpenAI) or built-in factual analytical synthesis.

#### Request Body (`application/json`)
```json
{
  "message": "What is NVDA's Sharpe ratio?",
  "asset": "NVDA",
  "conversation_id": "c7a8b9d0-1234-5678-9abc-def012345678"
}
```

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `message` | `string` | **Yes** | Natural-language financial or quantitative question (min length: 1, max length: 1000). |
| `asset` | `string` | No | Optional asset hint (`NVDA`, `BTC/USD`, `XAU/USD`). If omitted, detected automatically from message text. |
| `conversation_id` | `string` | No | Bounded conversation session ID for multi-turn conversational memory (retains up to 6 turns). |

#### Response: `200 OK`
```json
{
  "conversation_id": "c7a8b9d0-1234-5678-9abc-def012345678",
  "answer": "According to Quantexa's risk analysis model, NVIDIA (NVDA) has an annualized Sharpe ratio of 1.8421 (evaluated against a 2.0% risk-free rate) with a maximum drawdown of -12.45% occurring on 2024-08-05. Note that historical risk metrics are backward-looking and do not guarantee future returns.",
  "relevant_assets": ["NVDA"],
  "relevant_contexts": ["risk", "market_data"],
  "timestamp": "2026-09-19T18:00:00Z",
  "model": "quantexa-grounded-analytics",
  "data_references": [
    {
      "source": "Risk Analysis",
      "asset": "NVDA",
      "details": "Sharpe: 1.8421 | Max Drawdown: -12.45% (2024-08-05)",
      "observation_count": 252,
      "timestamp": "2026-09-19T00:00:00Z"
    }
  ]
}
```

---

## 22. AI Assistant Provider Status

### `GET /ai/status`

Returns the operational state of the server-side AI provider integration, configured model family, masked API key status, and conversation memory metrics.

#### Response: `200 OK`
```json
{
  "configured": true,
  "provider": "gemini",
  "model": "gemini-1.5-pro",
  "masked_api_key": "************A1b2",
  "active_conversations": 3,
  "max_history_turns": 6,
  "timestamp": "2026-09-19T18:00:00Z"
}
```

---

## Common Error Codes

| Status Code | Reason | Cause |
| :--- | :--- | :--- |
| `400 Bad Request` | Invalid Parameter | Provided parameter (`initial_capital`, `transaction_cost_rate`, `allocation`, `parameter_grid`, etc.) is invalid, out of bounds, or exceeds bounded limit (50 combinations). |
| `404 Not Found` | Unsupported Asset | Requested asset identifier is not mapped to NVDA, BTC/USD, or XAU/USD. |
| `502 Bad Gateway` | Upstream API Error | Upstream market data provider failed or rate limit exceeded with no valid cache. |
| `504 Gateway Timeout` | Provider Timeout | Upstream provider failed to respond within connection timeout window. |


