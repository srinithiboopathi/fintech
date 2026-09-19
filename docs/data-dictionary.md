# QUANTLAB Data Dictionary

## 1. Asset Universe

| Asset Identifier | Full Name | Asset Class | Trading Days / Year | Primary Benchmark Role |
|---|---|---|---|---|
| `gold` | Physical Gold / Comex Futures | Commodity / Store of Value | 252 | Safe-haven benchmark |
| `bitcoin` | Bitcoin (BTC-USD) | Digital Asset / Crypto | 365 | High-volatility growth asset |
| `nvidia` | NVIDIA Corporation (NVDA) | Equities / Tech Semiconductor | 252 | Equities market momentum |

---

## 2. Normalized Time-Series Schema

The standardized dataset format used across all backend calculation engines:

| Field Name | Type | Unit / Format | Description |
|---|---|---|---|
| `date` | `string` (ISO-8601) | `YYYY-MM-DD` | Calendar trade date |
| `asset` | `string` | `gold` / `bitcoin` / `nvidia` | Standard asset identifier |
| `open` | `float` | USD ($) | Market opening price |
| `high` | `float` | USD ($) | Highest price during session |
| `low` | `float` | USD ($) | Lowest price during session |
| `close` | `float` | USD ($) | Closing / Settlement price |
| `volume` | `float` | Contracts / Shares / Units | Traded volume |

---

## 3. Quantitative & Statistical Metrics

| Metric Name | Mathematical Definition | Interpretation |
|---|---|---|
| **Simple Moving Average (SMA)** | $\text{SMA}_n = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}$ | Rolling trend baseline |
| **Exponential Moving Average (EMA)** | $\text{EMA}_t = \alpha P_t + (1-\alpha)\text{EMA}_{t-1}$ | Responsive trend line ($\alpha = \frac{2}{n+1}$) |
| **Daily Return** | $R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$ | Arithmetic daily percentage gain/loss |
| **Cumulative Return** | $CR_t = \prod_{i=1}^t (1 + R_i) - 1$ | Compounded total return from inception |
| **Annualized Volatility** | $\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{N}$ | Standard deviation of returns scaled to year ($N=252$ or $365$) |
| **Sharpe Ratio** | $\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}$ | Risk-adjusted return excess of risk-free rate |
| **Maximum Drawdown (MDD)** | $\text{MDD} = \min_{\tau \le t} \frac{P_t - \max_{s \le \tau} P_s}{\max_{s \le \tau} P_s}$ | Peak-to-trough maximum percentage decline |
| **Pearson Correlation** | $\rho_{X,Y} = \frac{\text{Cov}(X,Y)}{\sigma_X \sigma_Y}$ | Linear co-movement between asset returns |
