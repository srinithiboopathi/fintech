# Quantitative Methodology

This document details the mathematical models, formulas, statistical assumptions, and numerical implementations active in the **Quantexa** analytics platform.

> [!NOTE]
> This document describes the currently implemented quantitative algorithms (Steps 1–8). Future algorithmic models (such as specific systematic strategy rules) are reserved for subsequent steps.

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

## 7. Multi-Asset Pearson Correlation & Rolling Correlation

The platform provides institutional-grade pairwise and multi-asset correlation analysis based exclusively on **daily percentage returns**, completely eliminating the severe statistical pitfalls of correlating non-stationary raw price levels.

### 1. Daily Return Transformation:
For each asset $k$, daily price discovery is mapped to discrete percentage returns:
$$R_{k,t} = \frac{P_{k,t} - P_{k,t-1}}{P_{k,t-1}}$$

### 2. Strict Date Alignment (No Forward-Filling):
Because equity markets (`NVDA`) trade on business days while cryptocurrency markets (`BTC/USD`) trade continuously, timestamp alignment is strictly enforced:
- **Inner Join**: Return series are aligned strictly on exact overlapping UTC dates ($t \in \mathcal{D}_{NVDA} \cap \mathcal{D}_{BTC} \cap \mathcal{D}_{XAU}$).
- **Zero Forward-Filling**: Missing return observations are never artificially interpolated, forward-filled, or zero-filled.
- **Reporting**: The exact number of overlapping observations and the start/end dates are explicitly reported.

### 3. Pearson Product-Moment Correlation:
The empirical sample correlation between asset returns $X$ and $Y$ over $n$ overlapping days is computed as:
$$r_{xy} = \frac{\sum_{i=1}^n (X_i - \bar{X})(Y_i - \bar{Y})}{\sqrt{\sum_{i=1}^n (X_i - \bar{X})^2 \cdot \sum_{i=1}^n (Y_i - \bar{Y})^2}}$$

Where $\bar{X} = \frac{1}{n} \sum_{i=1}^n X_i$ and $\bar{Y} = \frac{1}{n} \sum_{i=1}^n Y_i$.

#### Operational Characteristics & Matrix Invariants:
- **Symmetry**: $r_{xy} \equiv r_{yx}$ for all asset pairs.
- **Unit Diagonal**: $r_{xx} = 1.0$ for any non-zero variance series.
- **Bounded Range**: $r \in [-1.0, 1.0]$.
- **Zero Variance Safety**: Evaluates strictly to `None` if sample variance is zero or $n < 2$.

### 4. Rolling Correlation Analysis:
Tracks dynamic co-movement over a configurable rolling lookback window of $W$ observations ($W \ge 2$):
- **Warmup Period**: For any observation $t < W - 1$, fewer than $W$ observations exist. The rolling correlation evaluates strictly to `None`.
- **Causal Calculation**: At step $t \ge W - 1$, correlation is calculated strictly on return slices $[t - W + 1 : t + 1]$. Future returns ($i > t$) are mathematically inaccessible.
- **Multi-Asset Pairing**: Pairwise rolling series are computed independently for `NVDA vs BTC/USD`, `NVDA vs XAU/USD`, and `BTC/USD vs XAU/USD`.

---

## 6. Strategy-Agnostic Backtesting Engine

The **Quantexa** backtesting engine is a modular, event-driven, strategy-agnostic simulation service designed to model realistic trading performance over historical market data.

### 1. Strategy-Agnostic Signal Model
The engine operates independently of specific trading rules or indicators. It ingests an aligned sequence of generic trading directives:
- **`BUY`**: Enter a long position using available cash scaled by `allocation_fraction`.
- **`SELL`**: Fully liquidate existing asset holdings into cash.
- **`HOLD`**: Maintain existing portfolio state without executing trades.

### 2. Next-Observation Execution Assumption (Zero Look-Ahead Bias)
In live trading, a signal calculated using the closing price at observation $t$ cannot be executed at $t$ because the market has already closed. 
Therefore, the engine enforces a strict causal execution contract:
$$\text{Signal generated at time } t \implies \text{Executed at time } t + 1 \text{ at Close Price } P_{t+1}$$
This structural constraint guarantees zero look-ahead bias. Past trade executions and equity snapshots remain strictly invariant to future price perturbations.

### 3. Position Sizing & Cash Invariants
- **Target Cash Allocation**:
  $$\text{Cash Committed} = \text{Cash}_t \times \text{allocation\_fraction}$$
  Where $\text{allocation\_fraction} \in (0.0, 1.0]$ (default: $1.0 = 100\%$).
- **Fee-Aware Sizing**:
  To prevent overspending and guarantee $\text{Cash} \ge 0$, transaction costs are incorporated directly into position sizing:
  $$\text{Quantity} = \frac{\text{Cash Committed}}{P_{t+1} \times (1 + \text{fee\_rate})}$$
- **Capital Conservation**: No borrowing, margin, or short selling is permitted. If available cash is zero or insufficient, subsequent `BUY` signals are ignored without creating negative cash.

### 4. Transaction Cost Model
Transaction costs are applied symmetrically across all `BUY` and `SELL` executions:
$$\text{Transaction Fee} = \text{Trade Value} \times \text{transaction\_cost\_rate}$$
Where $\text{Trade Value} = \text{Quantity} \times P_{\text{exec}}$, and $\text{transaction\_cost\_rate} \ge 0$ (default: $0.001 = 0.1\%$).
- **On `BUY`**: Cash deducted = $\text{Trade Value} + \text{Fee} = \text{Cash Committed}$.
- **On `SELL`**: Cash credited = $\text{Trade Value} - \text{Fee}$.

### 5. Portfolio Accounting & Valuation
At every historical observation $t$, the portfolio is marked to market:
$$\text{Market Value}_t = \text{Position Quantity}_t \times P_t$$
$$\text{Portfolio Value}_t = \text{Cash}_t + \text{Market Value}_t$$
$$\text{Daily Return}_t = \frac{\text{Portfolio Value}_t - \text{Portfolio Value}_{t-1}}{\text{Portfolio Value}_{t-1}} \times 100$$
At inception ($t = 0$), $\text{Portfolio Value}_0 = \text{Initial Capital}$, $\text{Cash}_0 = \text{Initial Capital}$, and $\text{Position}_0 = 0$.

### 6. Trade Audit History & Realized PnL
Every executed transaction logs an immutable audit trail:
- Timestamp, side (`BUY` / `SELL`), execution price, quantity, gross trade value, fee paid, resulting cash, and resulting position.
- On `SELL` executions, realized dollar profit/loss ($\text{PnL} = \text{Proceeds} - \text{Cost Basis}$) and return percentage ($\text{PnL\%}$) are recorded to track winning vs losing trades.

### 7. Buy-and-Hold Benchmark
For performance evaluation, each backtest simulates an identical baseline Buy-and-Hold benchmark:
- Buys the underlying asset at the first execution opportunity ($P_1$) using initial capital and applying identical transaction fees.
- Holds until the final observation $N-1$, providing a true passive baseline to measure strategy alpha.

---

## Four Quantitative Trading Strategies

Quantexa implements four canonical quantitative trading strategies conforming to a modular strategy interface. All strategies generate discrete, generic signals (`BUY`, `SELL`, `HOLD`) and are decoupled from portfolio accounting, which is handled exclusively by the Step 8 `BacktestingEngine`.

### 1. SMA Crossover Strategy
- **Parameters**: `short_period` ($\ge 1$, default: 20), `long_period` ($\ge 2$, default: 50, where `short_period < long_period`).
- **Signal Logic**:
  - **`BUY`**: Emitted if and only if the short SMA crosses strictly from $\le$ long SMA to $>$ long SMA:
    $$\text{SMA}_{\text{short}, t-1} \le \text{SMA}_{\text{long}, t-1} \quad \text{and} \quad \text{SMA}_{\text{short}, t} > \text{SMA}_{\text{long}, t}$$
  - **`SELL`**: Emitted if and only if the short SMA crosses strictly from $\ge$ long SMA to $<$ long SMA:
    $$\text{SMA}_{\text{short}, t-1} \ge \text{SMA}_{\text{long}, t-1} \quad \text{and} \quad \text{SMA}_{\text{short}, t} < \text{SMA}_{\text{long}, t}$$
  - **`HOLD`**: In all other conditions, including when short SMA remains above or below long SMA without crossing.

### 2. EMA Trend Strategy
- **Parameter**: `ema_period` ($\ge 1$, default: 20).
- **Signal Logic**:
  - **`BUY`**: When close price exceeds the current EMA ($\text{Close}_t > \text{EMA}_t$).
  - **`SELL`**: When close price falls below the current EMA ($\text{Close}_t < \text{EMA}_t$).
  - **`HOLD`**: When close price equals the current EMA ($\text{Close}_t = \text{EMA}_t$) or prior to EMA warmup.

### 3. Momentum Strategy
- **Parameter**: `lookback` ($\ge 1$, default: 10).
- **Metric**:
  $$\text{Momentum}_t = \frac{\text{Close}_t}{\text{Close}_{t - \text{lookback}}} - 1$$
- **Signal Logic**:
  - **`BUY`**: $\text{Momentum}_t > 0$ (positive price velocity).
  - **`SELL`**: $\text{Momentum}_t < 0$ (negative price velocity).
  - **`HOLD`**: $\text{Momentum}_t = 0$ or observations before the lookback window.

### 4. Mean Reversion Strategy
- **Parameters**: `lookback` ($\ge 2$, default: 20), `entry_threshold` ($> 0.0$, default: 1.0).
- **Metric**:
  $$z_t = \frac{\text{Close}_t - \mu_{t, \text{lookback}}}{s_{t, \text{lookback}}}$$
  Where $\mu_t$ is rolling arithmetic mean and $s_t$ is rolling sample standard deviation ($ddof = 1$). If $s_t = 0.0$, $z_t = 0.0$ safely.
- **Signal Logic**:
  - **`BUY`**: $z_t \le -\text{entry\_threshold}$ (oversold deviation from rolling mean).
  - **`SELL`**: $z_t \ge \text{entry\_threshold}$ (overbought deviation from rolling mean).
  - **`HOLD`**: $-\text{entry\_threshold} < z_t < \text{entry\_threshold}$ or insufficient warmup window.

---

## Summary of Quantitative Invariants

| Invariant | Implementation Mechanism |
| :--- | :--- |
| **No Look-Ahead Bias** | Signal at $t$ executes at $t+1$ at $P_{t+1}$; running peak and rolling slices depend strictly on past data ($i \le t$). |
| **Capital Conservation** | Fee-inclusive position sizing guarantees $\text{Cash} \ge 0$ at all times; no leverage or shorting. |
| **Symmetric Transaction Costs** | Configurable fee percentage applied on both entry (`BUY`) and exit (`SELL`). |
| **Discrete Signal Interface** | Strategies emit only `BUY`, `SELL`, `HOLD`; portfolio accounting is delegated to BacktestingEngine. |
| **Missing Value Safety** | Explicit `None` propagation; never interpolated or zero-filled. |
| **Bessel's Correction** | Sample variance denominator is $m - 1$, preventing sample bias. |
| **Zero Variance Protection** | Safely evaluates to `None` or `0.0` if $\sigma = 0.0$ or denominator evaluates to zero. |
| **Stationary Returns Only** | Correlation is calculated on daily return series, never on non-stationary raw prices. |
| **Strict Date Alignment** | Overlapping inner-join on UTC dates; zero forward-filling across market closures. |
| **Multi-Asset Compatibility** | Uniform mathematical definitions applied across Equities, Cryptocurrencies, and Commodities. |


