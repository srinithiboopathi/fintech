# QUANTLAB Data Dictionary & Kaggle Ingestion Specification

## 1. Asset Universe & Source Dataset Mapping

| Asset Identifier | Asset Class | Raw Kaggle Source File | Raw Frequency | Raw Rows | Processed Rows | Output File |
|---|---|---|---|---|---|---|
| **Gold** | Commodity (Futures GC=F) | `datasets/raw/gold/Gold_Spot_historical_data.csv` | Daily | 6,358 | 6,358 | `datasets/processed/gold_daily.csv` |
| **Bitcoin** | Digital Asset (BTC/USD) | `datasets/raw/bitcoin/BTC-2017min.csv` | 1-Minute Intraday | 525,599 | 365 | `datasets/processed/bitcoin_daily.csv` |
| **NVIDIA** | Equities (NVDA Semiconductor) | `datasets/raw/nvidia/NVIDIA_historical_data.csv` | Daily | 6,778 | 6,778 | `datasets/processed/nvidia_daily.csv` |

---

## 2. Actual Discovered Raw Dataset Schemas

### A. Gold (`Gold_Spot_historical_data.csv`)
- **Raw Columns**: `['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'name']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS-05:00` (ISO 8601 with timezone offset)
- **Date Range**: `2000-08-30` to `2025-12-31`
- **Mapping**:
  - `Date` $\rightarrow$ `date` (`YYYY-MM-DD`)
  - `'Gold'` $\rightarrow$ `asset`
  - `Open` $\rightarrow$ `open`
  - `High` $\rightarrow$ `high` (Envelope aligned with `max(High, Open, Close)`)
  - `Low` $\rightarrow$ `low` (Envelope aligned with `min(Low, Open, Close)`)
  - `Close` $\rightarrow$ `close`
  - `Volume` $\rightarrow$ `volume`

### B. Bitcoin (`BTC-2017min.csv`)
- **Raw Columns**: `['unix', 'date', 'symbol', 'open', 'high', 'low', 'close', 'Volume BTC', 'Volume USD']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS` (1-minute intervals, stored in descending chronological order)
- **Date Range**: `2017-01-01 00:01:00` to `2017-12-31 23:59:00` (Full 2017 calendar year)
- **Daily Aggregation Logic**:
  - Sorted ascending chronologically before grouping by calendar day (`YYYY-MM-DD`).
  - `open` = First 1-minute open of the day (`00:01` observation)
  - `high` = Maximum 1-minute high across all observations in the day
  - `low` = Minimum 1-minute low across all observations in the day
  - `close` = Last 1-minute close of the day (`23:59` observation)
  - `volume` = Sum of `Volume BTC` traded in the day

### C. NVIDIA (`NVIDIA_historical_data.csv`)
- **Raw Columns**: `['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'name']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS-05:00` (ISO 8601 with timezone offset)
- **Date Range**: `1999-01-22` to `2025-12-31`
- **Mapping**:
  - `Date` $\rightarrow$ `date` (`YYYY-MM-DD`)
  - `'NVIDIA'` $\rightarrow$ `asset`
  - `Open` $\rightarrow$ `open`
  - `High` $\rightarrow$ `high`
  - `Low` $\rightarrow$ `low`
  - `Close` $\rightarrow$ `close`
  - `Volume` $\rightarrow$ `volume`

---

## 3. Normalized Time-Series Schema

The standardized dataset format used across all backend calculation engines (`gold_daily.csv`, `bitcoin_daily.csv`, `nvidia_daily.csv`, and unified `market_data.csv`):

| Field Name | Type | Unit / Format | Description |
|---|---|---|---|
| `date` | `string` | `YYYY-MM-DD` | Normalized calendar trade date (ISO-8601 string) |
| `asset` | `string` | `Gold` / `Bitcoin` / `NVIDIA` | Standard asset identifier name |
| `open` | `float` | USD ($) | Market opening price for the day |
| `high` | `float` | USD ($) | Highest price during the session ($\ge \max(\text{open}, \text{close})$) |
| `low` | `float` | USD ($) | Lowest price during the session ($\le \min(\text{open}, \text{close})$) |
| `close` | `float` | USD ($) | Closing settlement price for the day |
| `volume` | `float` | Traded units | Total traded volume (contracts for Gold, BTC for Bitcoin, shares for NVDA) |

---

## 4. Quantitative & Statistical Metrics Reference

| Metric Name | API Field | Type | Unit / Format | Mathematical Definition | Annualization Factor | Interpretation |
|---|---|---|---|---|---|---|
| **Simple Moving Average** | `sma` | `float` / `null` | USD ($) | $\text{SMA}_n = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}$ | N/A | Trend baseline over lookback period $n$ |
| **Exponential Moving Average** | `ema` | `float` / `null` | USD ($) | $\text{EMA}_t = \alpha P_t + (1-\alpha)\text{EMA}_{t-1}$ | N/A | Exponentially smoothed trend line ($\alpha = \frac{2}{n+1}$) |
| **Daily Return** | `daily_return` | `float` / `null` | Ratio (e.g. `0.02` = +2%) | $R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$ | N/A | Single session arithmetic percentage return |
| **Cumulative Return** | `cumulative_return` | `float` / `null` | Ratio (e.g. `1.50` = +150%) | $\text{CR}_t = \prod_{i=1}^t (1 + R_i) - 1$ | N/A | Compounded wealth growth of \$1 initial capital |
| **Rolling Volatility** | `rolling_volatility` | `float` / `null` | Daily ratio | $\sigma_{\text{daily}} = \sqrt{\frac{\sum (R_t - \bar{R})^2}{w - 1}}$ | N/A | Historical rolling sample standard deviation ($w \ge 2$) |
| **Annualized Volatility** | `annualized_volatility` | `float` / `null` | Annual ratio | $\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{N}$ | Gold/NVDA: 252, BTC: 365 | Volatility scaled to annual trading sessions |
| **Sharpe Ratio** | `sharpe_ratio` | `float` / `null` | Dimensionless ratio | $\text{Sharpe} = \frac{\bar{R}_e}{\sigma_{R_e}} \times \sqrt{N}$ | Gold/NVDA: 252, BTC: 365 | Risk-adjusted excess return per unit volatility |
| **Maximum Drawdown** | `maximum_drawdown` | `float` / `null` | Ratio $\le 0.0$ (e.g. `-0.25`) | $\text{MDD} = \min_{t} (\frac{P_t}{\text{Peak}_t} - 1)$ | N/A | Maximum observed peak-to-trough equity decline |
| **Rolling Return** | `rolling_return` | `float` / `null` | Ratio | $\text{RR}_{w,t} = \frac{P_t}{P_{t-w}} - 1$ | N/A | $w$-period arithmetic price momentum |
| **Running Peak** | `peak` | `float` | USD ($) | $\text{Peak}_t = \max_{0 \le \tau \le t} P_\tau$ | N/A | High-water mark of price / wealth series |
| **Pearson Correlation** | `correlation` | `float` / `null` | Dimensionless $[-1.0, 1.0]$ | $r = \frac{\text{Cov}(R_A, R_B)}{\sigma_A \sigma_B}$ | N/A | Linear co-movement between aligned daily asset returns |
| **Rolling Correlation** | `rolling_correlation` | `float` / `null` | Dimensionless $[-1.0, 1.0]$ | $r_t = \frac{\text{Cov}_w(R_A, R_B)}{\sigma_{A,w} \sigma_{B,w}}$ | N/A | Time-varying linear dependency over lookback window $w$ |
| **Compound Annual Growth Rate** | `annualized_return` | `float` / `null` | Annual ratio | $\text{CAGR} = (1 + \text{CR})^{365.25 / \text{Days}} - 1$ | N/A | Geometric annualized return growth |
| **Overlapping Observations** | `observations` / `aligned_records` | `integer` | Count | Count of joint active trading dates | N/A | Sample size used for statistical validity |
