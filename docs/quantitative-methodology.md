# Quantitative Methodology

This document details the mathematical models, formulas, statistical assumptions, and numerical implementations active in the **Quantexa** analytics platform.

> [!NOTE]
> This document describes the currently implemented quantitative algorithms (Steps 1–6). Future analytical models (such as portfolio correlation and backtesting) are reserved for subsequent steps.

---

## Data Input Pipeline & Temporal Hygiene

All quantitative models ingest data exclusively from the **Step 3 Data Storage & Cleaning Layer** (`app/services/data_cleaner.py`).

### Methodological Guarantees:
1. **Chronological Invariant**: All input arrays are strictly sorted in ascending chronological order:
   $$t_0 < t_1 < t_2 < \dots < t_N$$
2. **Look-Ahead Bias Elimination**:
   Calculations are strictly causal (forward-only). For any point at index $t$, the computed metrics depend solely on observations at indices $i \le t$. Future observations ($i > t$) are inaccessible at time $t$.
3. **Price Cleanliness**:
   All non-numeric values, zero prices, negative prices, and duplicate timestamps are purged before metric evaluation.

---

## 1. Simple Moving Average (SMA)

The Simple Moving Average is an unweighted arithmetic mean of closing prices over a rolling lookback window of length $n$.

### Mathematical Formulation

$$\text{SMA}_t(n) = \frac{1}{n} \sum_{k=0}^{n-1} P_{t-k}$$

Where:
- $P_t$: Closing price at time step $t$.
- $n$: Window period (a strictly positive integer, $n \ge 1$).

### Operational Characteristics & Boundary Rules:
- **Warmup Period**: For any index $t < n - 1$, fewer than $n$ observations exist. The function yields strictly `None` (or `null` in JSON) rather than distorting early values with partial sums.
- **Identity Case ($n = 1$)**: When $n = 1$, $\text{SMA}_t(1) = P_t$ for all $t$.
- **Window Exceeds Sample Size ($n > N$)**: If the period $n$ exceeds the total number of available records, all outputs evaluate to `None`.
- **Numerical Precision**: Values are rounded to 4 decimal places for API serialization.

---

## 2. Exponential Moving Average (EMA)

The Exponential Moving Average applies exponentially decreasing weights to past closing prices, placing greater statistical significance on recent price discovery while retaining infinite memory of prior prices.

### Mathematical Formulation

#### 1. Smoothing Factor (Multiplier):
$$\alpha = \frac{2}{n + 1}$$

Where $n$ is the moving average lookback period ($n \ge 1$).

#### 2. Seed Initialization:
To eliminate seed distortion without creating look-ahead bias, standard institutional practice is followed. The initial EMA seed is computed as the Simple Moving Average of the first $n$ closing prices:
$$\text{EMA}_{n-1} = \frac{1}{n} \sum_{k=0}^{n-1} P_k$$

All preceding indices ($t \in [0, n-2]$) evaluate strictly to `None`.

#### 3. Recursive Computation (for $t \ge n$):
$$\text{EMA}_t = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_{t-1}$$

### Operational Characteristics & Boundary Rules:
- **Warmup Period**: Pre-seed indices $t < n - 1$ return `None`.
- **Identity Case ($n = 1$)**: Multiplier $\alpha = \frac{2}{1 + 1} = 1.0$. The formula reduces to $\text{EMA}_t(1) = P_t$.
- **Numerical Stability**: Single-pass $O(N)$ recurrence ensures minimal floating-point accumulator drift.

---

## 3. Daily Percentage Returns

Daily returns measure the relative rate of price change between consecutive market close prices.

### Mathematical Formulation

$$R_t = \left( \frac{P_t - P_{t-1}}{P_{t-1}} \right) \times 100\% = \left( \frac{P_t}{P_{t-1}} - 1 \right) \times 100\%$$

Where:
- $P_t$: Clean closing price on day $t$.
- $P_{t-1}$: Clean closing price on the preceding trading day $t-1$.
- $R_t$: Return expressed in percentage points (e.g., $+2.50\%$ return is represented as `2.5`).

### Operational Characteristics & Boundary Rules:
- **Initial Observation ($t = 0$)**: Because no preceding observation exists for the very first bar in the dataset, $R_0 \equiv \text{None}$.
- **Zero / Negative Protection**: The data cleaning layer purges zero and negative prices, preventing division by zero or invalid sign inversion.
- **Precision**: Output is rounded to 4 decimal places.

---

## 4. Rolling Volatility

Volatility represents the dispersion of daily returns around their empirical mean over a rolling lookback window of length $n$.

### Mathematical Formulation

The platform calculates the **sample standard deviation** with Bessel's correction ($ddof = 1$):

$$\sigma_t(n) = \sqrt{\frac{1}{n - 1} \sum_{i=0}^{n-1} \left( R_{t-i} - \bar{R}_t \right)^2}$$

Where:
- $R_{t-i}$: Daily return at time $t-i$.
- $\bar{R}_t$: Empirical sample mean of returns within the rolling window:
  $$\bar{R}_t = \frac{1}{n} \sum_{i=0}^{n-1} R_{t-i}$$
- $n$: Window size in observations ($n \ge 2$).

### Operational Characteristics & Boundary Rules:
- **Bessel's Correction ($ddof = 1$)**: Dividing by $n - 1$ produces an unbiased estimator of population variance from a sample of returns.
- **Undefined at $n = 1$**: Sample variance with $n=1$ requires dividing by $n - 1 = 0$. Hence, for $n = 1$, the rolling volatility strictly returns `None`.
- **Warmup & Incomplete Windows**: If fewer than $n$ valid (non-null) return observations exist leading up to index $t$, $\sigma_t(n) \equiv \text{None}$. Because $R_0 = \text{None}$, the earliest index capable of yielding rolling volatility for period $n$ is index $t = n$.
- **Non-Annualized**: In accordance with the Step 5 requirement, values represent daily percentage volatility ($\sigma_{\text{daily}}$) without assuming an arbitrary annualization factor (e.g., $\sqrt{252}$ or $\sqrt{365}$).

---

## 5. Annualized Sharpe Ratio

The Sharpe Ratio measures the risk-adjusted excess performance of an asset relative to an annualized risk-free benchmark rate.

### Mathematical Formulation

$$\text{Sharpe} = \left( \frac{\bar{R} - \frac{R_f}{N}}{\sigma} \right) \times \sqrt{N}$$

Where:
- $\bar{R}$: Empirical sample mean of daily percentage returns: $\bar{R} = \frac{1}{m} \sum_{i=1}^m R_i$.
- $R_f$: Annual risk-free benchmark rate (e.g., $0.0\%$ or $2.0\%$).
- $N$: Annualization factor representing trading days per year ($N=252$ for equities, $N=365$ for crypto).
- $\frac{R_f}{N}$: De-annualized daily risk-free rate.
- $\sigma$: Unbiased sample standard deviation of daily returns with Bessel's correction ($ddof=1$):
  $$\sigma = \sqrt{\frac{1}{m - 1} \sum_{i=1}^m (R_i - \bar{R})^2}$$
- $m$: Total count of valid (non-null) daily return observations.

### Operational Characteristics & Boundary Rules:
- **Sample Size Constraint**: If $m < 2$, sample variance is undefined. The Sharpe ratio strictly returns `None`.
- **Zero Variance Edge Case**: If $\sigma = 0.0$ (e.g., perfectly flat returns), division by zero is prevented and the calculation safely returns `None`.
- **Annualization Consistency**: Multiplied by $\sqrt{N}$ in institutional standard accordance.

---

## 6. Maximum Drawdown (MDD)

Maximum Drawdown quantifies the largest historical peak-to-trough percentage decline observed in an asset's price trajectory prior to reaching a new high.

### Mathematical Formulation

#### 1. Running Peak Series (Causal):
$$\text{Peak}_t = \max_{0 \le i \le t} (P_i)$$

Where $P_i$ is the clean closing price on day $i$. Crucially, $\text{Peak}_t$ accesses observations only up to index $t$, ensuring zero look-ahead bias.

#### 2. Percentage Drawdown Series:
$$\text{Drawdown}_t = \left( \frac{P_t}{\text{Peak}_t} - 1 \right) \times 100\%$$

#### 3. Maximum Drawdown & Timestamp:
$$\text{MDD} = \min_{0 \le t \le N} (\text{Drawdown}_t)$$
$$t_{\text{MDD}} = \arg\min_{0 \le t \le N} (\text{Drawdown}_t)$$

### Operational Characteristics & Boundary Rules:
- **Non-Positive Value**: Drawdown is bounded in $(-\infty, 0.0\%]$. A value of $0.0\%$ indicates that the asset is currently at an all-time peak for the analyzed window.
- **Trough Date Identification**: The platform explicitly returns the ISO-8601 UTC timestamp of the exact observation where the maximum trough occurred.
- **Single Observation Case**: If $N = 1$, $\text{MDD} = 0.0\%$.

---

## Summary of Quantitative Invariants

| Invariant | Implementation Mechanism |
| :--- | :--- |
| **No Look-Ahead Bias** | Running peak $\text{Peak}_t = \max_{i \le t}(P_i)$ depends strictly on past/current prices. |
| **Missing Value Safety** | Explicit `None` propagation; never interpolated or zero-filled. |
| **Bessel's Correction** | Variance denominator is $m - 1$, preventing sample bias. |
| **Zero Variance Protection** | Safely evaluates to `None` if $\sigma = 0.0$, preventing division by zero. |
| **Multi-Asset Compatibility** | Uniform mathematical definitions applied across Equities, Cryptocurrencies, and Commodities. |
