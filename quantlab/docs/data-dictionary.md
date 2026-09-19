# QuantLab Data Dictionary

This document specifies the schema, definitions, measurement units, and mathematical definitions for all market time-series data and quantitative metrics used across QuantLab.

---

## 1. Market Time-Series Schema

| Field Name | Type | Unit / Format | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | ISO-8601 String | `YYYY-MM-DD` | Trading session date in UTC. |
| `open` | Float64 | USD ($) | Opening transaction price of the trading bar. |
| `high` | Float64 | USD ($) | Highest recorded transaction price during the bar. |
| `low` | Float64 | USD ($) | Lowest recorded transaction price during the bar. |
| `close` | Float64 | USD ($) | Official closing settlement price of the bar. |
| `adj_close` | Float64 | USD ($) | Close adjusted for stock splits and dividend distributions. |
| `volume` | Int64 / Float64 | Units / Contracts | Cumulative trading volume during the trading bar. |
| `daily_return` | Float64 | Ratio (e.g. 0.02 = +2%) | Single-period arithmetic return: $(P_t - P_{t-1}) / P_{t-1}$. |
| `log_return` | Float64 | Ratio | Continuously compounded return: $\ln(P_t / P_{t-1})$. |

---

## 2. Technical Indicators Schema

| Indicator Key | Formula / Parameters | Description |
| :--- | :--- | :--- |
| `sma_fast` / `sma_slow` | $\frac{1}{N}\sum_{i=0}^{N-1} P_{t-i}$ | Simple Moving Average over $N$ periods (default: 20, 50). |
| `ema_fast` / `ema_slow` | $P_t \cdot \alpha + EMA_{t-1}(1-\alpha)$ | Exponential Moving Average ($\alpha = 2/(N+1)$). |
| `rsi` | $100 - \frac{100}{1 + RS}$ | Relative Strength Index (14-period default). |
| `macd` | $EMA_{12}(P) - EMA_{26}(P)$ | Moving Average Convergence Divergence line. |
| `macd_signal` | $EMA_9(MACD)$ | 9-period EMA signal line of the MACD. |
| `macd_hist` | $MACD - Signal$ | Histogram delta between MACD and signal line. |
| `bb_upper` / `bb_lower`| $SMA_{20} \pm 2\sigma$ | Bollinger Bands (20-day baseline with 2 standard deviations). |
| `atr` | $\text{WilderSmooth}(TR, 14)$ | Average True Range measuring market volatility. |

---

## 3. Portfolio & Risk Metrics Schema

| Metric | Formula | Description |
| :--- | :--- | :--- |
| `cagr` | $(V_T / V_0)^{252/N} - 1$ | Compounded Annual Growth Rate. |
| `sharpe_ratio` | $\frac{\mu_p - R_f}{\sigma_p} \times \sqrt{252}$ | Risk-adjusted return over risk-free rate ($R_f = 3.5\%$). |
| `sortino_ratio`| $\frac{\mu_p - R_f}{\sigma_{downside}} \times \sqrt{252}$ | Downside risk-adjusted return (penalizes only negative variance). |
| `max_drawdown` | $\min_t \left( \frac{V_t - HWM_t}{HWM_t} \right)$ | Largest peak-to-trough decline in portfolio equity. |
| `calmar_ratio` | $CAGR / \|MaxDD\|$ | Ratio of annual return to maximum historical drawdown. |
| `win_rate` | $\text{Wins} / \text{Total Trades}$ | Proportion of closed trades yielding positive net PnL. |
| `profit_factor`| $\sum \text{Gross Profits} / \sum \|\text{Gross Losses}\|$ | Ratio of aggregate gains to aggregate losses. |
| `var_95` | $\text{Percentile}_{5\%}(\text{Daily Returns})$ | 1-day Value at Risk at 95% confidence level. |
| `cvar_95` | $E[R \mid R \le \text{VaR}_{95}]$ | Expected Shortfall / Conditional VaR in 5% tail events. |
| `beta` | $\text{Cov}(R_p, R_b) / \text{Var}(R_b)$ | Portfolio sensitivity to benchmark returns. |
| `alpha` | $R_p - (R_f + \beta(R_b - R_f))$ | Jensen's Alpha annualized excess return. |
