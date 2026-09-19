# QuantLab API Specification

Base URLs:
- Root: `http://localhost:8000/`
- API v1 Prefix: `http://localhost:8000/api/v1`
- Universal API Prefix: `http://localhost:8000/api`
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Interactive ReDoc: `http://localhost:8000/redoc`

---

## 1. System Health

### `GET /health` / `GET /api/health`
Returns system status.
- **Response (200 OK):**
  ```json
  {
    "status": "ok"
  }
  ```

---

## 2. Market Data Endpoints

### `GET /api/market/assets`
Returns list of supported multi-asset contracts (Gold, Bitcoin, NVIDIA) with real-time statistics.

### `GET /api/market/{symbol}/history` or `GET /api/market/history/{symbol}`
Retrieves daily historical OHLCV bars.
- **Parameters:**
  - `start_date` (optional, format: `YYYY-MM-DD`)
  - `end_date` (optional, format: `YYYY-MM-DD`)

---

## 3. Quantitative Analytics Endpoints

### `GET /api/analytics/{symbol}/sma`
Calculates Simple Moving Average for a specified period.
- **Query Parameters:** `period=20` (integer, range: 2 to 500)

### `GET /api/analytics/{symbol}/ema`
Calculates Exponential Moving Average.
- **Query Parameters:** `period=20` (integer, range: 2 to 500)

### `GET /api/analytics/{symbol}/returns`
Computes daily percentage returns, cumulative returns series, and CAGR.

### `GET /api/analytics/{symbol}/volatility`
Calculates annualized historical volatility, downside volatility, and rolling volatility series.
- **Query Parameters:** `window=30`

### `GET /api/analytics/{symbol}/sharpe`
Calculates Sharpe Ratio, Sortino Ratio, Calmar Ratio, and rolling Sharpe series.
- **Query Parameters:**
  - `risk_free_rate=0.035` (default: 3.5%)
  - `window=60`

### `GET /api/analytics/{symbol}/drawdown`
Calculates underwater equity curve, peak-to-trough series, max drawdown percentage, and max drawdown duration in days.

### `GET /api/analytics/indicators/{symbol}`
Returns a unified payload with SMA (20, 50), EMA (9, 21), RSI (14), Bollinger Bands (20, 2σ), MACD (12, 26, 9), and ATR (14).

### `GET /api/analytics/risk/{symbol}`
Returns comprehensive institutional risk teardown: VaR 95%, VaR 99%, CVaR 95%, Sharpe, Sortino, Calmar, and Downside Volatility.

---

## 4. Correlation Lab

### `GET /api/correlation/matrix`
Returns aligned Pearson / Spearman correlation matrix across Gold, Bitcoin, and NVIDIA returns.
- **Query Parameters:** `method=pearson` (or `spearman`)

### `GET /api/correlation/rolling`
Returns rolling pairwise correlation time series between two selected assets.
- **Query Parameters:**
  - `asset_a=BTC-USD`
  - `asset_b=GC=F`
  - `window=30`

---

## 5. Strategy & Backtesting Endpoints

### `GET /api/strategies`
Returns the 4 institutional strategy definitions:
1. `sma_crossover` (Dual SMA Golden Cross)
2. `ema_trend` (Triple EMA Trend Ribbon)
3. `momentum` (Momentum Breakout System)
4. `mean_reversion` (Bollinger Bands Mean Reversion)

### `POST /api/backtest/run`
Executes an event-driven backtest simulation without look-ahead bias and compares performance against a passive Buy-and-Hold benchmark.
- **Request Body:**
  ```json
  {
    "symbol": "NVDA",
    "strategy_id": "sma_crossover",
    "initial_capital": 100000.0,
    "parameters": {
      "fast_period": 20,
      "slow_period": 50,
      "stop_loss_pct": 0.05,
      "take_profit_pct": 0.15
    },
    "position_sizing": "percent_equity",
    "position_size_value": 0.95,
    "commission_bps": 5.0,
    "slippage_pct": 0.0005,
    "start_date": "2021-01-04",
    "end_date": "2024-06-01"
  }
  ```
- **Response (200 OK):**
  Returns summary metrics (`total_return_pct`, `sharpe_ratio`, `max_drawdown_pct`, `win_rate_pct`, `total_trades`), full `equity_curve`, discrete `trades` ledger, and `benchmark` comparison (`total_return_pct`, `cagr_pct`, `sharpe_ratio`, `max_drawdown_pct`, `alpha_excess_return_pct`).

### `GET /api/backtest/history`
Returns recent backtest runs persisted in the database.

### `GET /api/backtest/{run_id}`
Retrieves a specific historical backtest run with associated trade logs.

---

## 6. Robustness & Regime Analysis

### `GET /api/robustness/monte-carlo/{symbol}`
Performs 300-1,000 path bootstrap resampling over historical return distribution to simulate forward equity probability envelopes and 5th/50th/95th percentile metrics.

### `GET /api/robustness/sensitivity/{symbol}`
Tests strategy across parameter grids and transaction cost schedules (0, 5, 15 bps).

### `GET /api/regimes/detect/{symbol}`
Classifies market time-series into 4 quantitative regimes:
- `Bull Trend`
- `Bear Trend`
- `High Volatility Choppy`
- `Low Volatility Consolidation`

---

## 7. Research Reports

### `GET /api/reports/generate/{symbol}`
Generates a complete quantitative research tear sheet containing price summary, returns, volatility, risk metrics, peer correlation profile, baseline backtest, and current market regime.
