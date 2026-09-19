# QUANTLAB Quantitative & Financial Analytics Methodology

This document provides mathematical formulations, conventions, parameter assumptions, and look-ahead bias prevention specifications used in QUANTLAB Phase 4.

---

## 1. Mathematical Specifications

### 1.1 Simple Moving Average (SMA)
Calculates the unweighted arithmetic mean of closing prices over the prior $n$ trading sessions:

$$\text{SMA}_n(t) = \frac{1}{n} \sum_{i=0}^{n-1} P_{t-i}$$

- **Warm-up / Missing Data**: For $t < n-1$, $\text{SMA}_n(t) = \text{null}$.
- **Look-Ahead Bias Protection**: Strictly backward-looking with `center=False`. No forward-filling.

---

### 1.2 Exponential Moving Average (EMA)
Calculates an exponentially weighted moving average that gives higher weight to recent prices while retaining historical memory:

$$\alpha = \frac{2}{n + 1}$$

$$\text{EMA}_t = \alpha P_t + (1 - \alpha) \text{EMA}_{t-1}, \quad \text{with } \text{EMA}_0 = P_0$$

- **Determinism**: Calculated recursively using standard exponential smoothing (`adjust=False`).
- **Look-Ahead Bias Protection**: Only relies on $P_t$ and historical $\text{EMA}_{t-1}$.

---

### 1.3 Daily Arithmetic Returns
Daily percentage change computed on market closing settlement prices:

$$R_t = \frac{P_t}{P_{t-1}} - 1 = \frac{P_t - P_{t-1}}{P_{t-1}}$$

- **Baseline Observation**: At $t=0$, $R_0 = \text{null}$ (no prior price exists).
- **Asset Isolation**: Returns are computed independently per asset series. Cross-asset return computation is strictly forbidden.

---

### 1.4 Compounded Cumulative Returns
Measures the compounded total wealth progression of an initial \$1.00 unit capital:

$$\text{CR}_t = \prod_{i=1}^t (1 + R_i) - 1$$

- **Baseline Growth**: $\text{CR}_0 = 0.0$ (representing 0% growth at the inception date).

---

### 1.5 Historical & Annualized Volatility
Sample standard deviation ($\text{ddof}=1$) of daily return series:

$$\sigma_{\text{daily}} = \sqrt{\frac{1}{N - 1} \sum_{t=1}^N (R_t - \bar{R})^2}$$

#### Annualization Factor Convention:
- **Traditional Assets (Gold, NVIDIA)**: $N_{\text{ann}} = 252$ trading days.
- **Continuous 24/7 Digital Assets (Bitcoin)**: $N_{\text{ann}} = 365$ calendar days.

$$\sigma_{\text{annualized}} = \sigma_{\text{daily}} \times \sqrt{N_{\text{ann}}}$$

- **Rolling Volatility**: Evaluated over lookback window $w \ge 2$, requiring at least $w$ observations before outputting values.

---

### 1.6 Sharpe Ratio (Risk-Adjusted Performance)
Measures risk-adjusted excess return per unit of total risk:

$$r_{f,\text{daily}} = \frac{r_{f,\text{annual}}}{N_{\text{ann}}}$$

$$R_{e,t} = R_t - r_{f,\text{daily}}$$

$$\text{Sharpe} = \frac{\bar{R}_e}{\sigma_{R_e}} \times \sqrt{N_{\text{ann}}}$$

- **Zero-Volatility Protection**: If $\sigma_{R_e} \le 10^{-12}$ or data length $< 2$, returns $\text{null}$ without division-by-zero or infinity.
- **Default Risk-Free Rate**: $r_{f,\text{annual}} = 0.0$ (configurable via query parameter).

---

### 1.7 Maximum Drawdown (MDD) & Drawdown Series
Measures the maximum observed peak-to-trough decline before a new high is attained:

$$\text{Running Peak}_t = \max_{0 \le \tau \le t} (P_\tau)$$

$$\text{Drawdown}_t = \frac{P_t}{\text{Running Peak}_t} - 1.0$$

$$\text{Max Drawdown (MDD)} = \min_{0 \le t \le T} (\text{Drawdown}_t)$$

- **Output Range**: Drawdown values are non-positive ($\le 0.0$), returned as negative percentages (e.g. $-0.25$ for a $-25\%$ decline).

---

### 1.8 Rolling Performance Metrics
Computes moving-window performance analytics across configurable time horizons ($w \in [20, 30, 60, 90, \dots]$):
- **Rolling Return**: $\frac{P_t}{P_{t-w}} - 1.0$
- **Rolling Annualized Volatility**: $\text{std}(R_{t-w+1 \dots t}) \times \sqrt{N_{\text{ann}}}$
- **Rolling Sharpe Ratio**: $\frac{\bar{R}_{e, w}}{\sigma_{R_{e, w}}} \times \sqrt{N_{\text{ann}}}$
- **Running Drawdown**: $\frac{P_t}{\text{Peak}_t} - 1.0$

---

## 2. Look-Ahead Bias Prevention

To ensure strict quantitative research integrity:
1. **No Centered Windows**: All moving averages and rolling aggregations enforce `center=False`.
2. **No Future Data Leakage**: Slicing or filtering by dates evaluates indicators on full historical context before window truncation, or strictly uses past data.
3. **Automated Look-Ahead Bias Tests**: Automated unit tests perturb future data points $t+1 \dots T$ and verify that indicator values at time $t$ remain mathematically invariant.

---

## 3. Data Integrity & Missing Data Rules

- **Zero Synthetic Data**: Calculations run purely on cleaned historical observations in `datasets/processed/`.
- **Independent Asset Horizons**: Bitcoin (2017), Gold (2000–2025), and NVIDIA (1999–2025) are evaluated on their real data boundaries without cross-contamination.
