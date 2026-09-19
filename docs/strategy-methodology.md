# QUANTLAB Quantitative Strategy Methodology

This document details the mathematical models, crossing algorithms, signal semantics, warm-up handling, and look-ahead bias guards implemented in **Phase 6: Strategy Engine** of the QUANTLAB quantitative intelligence platform.

---

## 1. Architectural Role & Boundary

The **Strategy Engine** is designed as a pure, deterministic, and modular quantitative signal generator.

```
+-----------------------------------------------------------------------------------+
|                            PHASE 6: STRATEGY ENGINE                               |
|                                                                                   |
|  +---------------------+   +---------------------+   +-------------------------+  |
|  |    SMA Crossover    |   |      EMA Trend      |   |   Momentum & Mean Rev   |  |
|  |  (Crossing Events)  |   |  (Crossing Events)  |   |    (Regime / Bounds)    |  |
|  +----------+----------+   +----------+----------+   +------------+------------+  |
|             |                         |                           |               |
|             v                         v                           v               |
|  +-----------------------------------------------------------------------------+  |
|  |                Standardized Strategy Signals (BUY, HOLD, SELL)              |  |
|  +-------------------------------------+---------------------------------------+  |
+----------------------------------------|------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        PHASE 7+: BACKTESTING & EXECUTION                          |
|                                                                                   |
|  - Position Sizing & Leverage               - Slippage & Commissions              |
|  - Trade Execution & Fills                  - Portfolio Mark-to-Market Simulation |
|  - Maximum Drawdown & Stop-Loss             - Benchmark Alpha & Equity Curve      |
+-----------------------------------------------------------------------------------+
```

> [!IMPORTANT]
> **Strategy Signal vs. Trade Execution Distinction**
> - **Strategy Signal (Phase 6)**: An analytical indicator event indicating a change in quantitative regime or crossing threshold at time $t$. It is strictly deterministic and asset-agnostic.
> - **Trade Execution (Phase 7)**: The portfolio execution logic that translates signals into order executions, position rebalances, cash adjustments, margin constraints, and transaction fee deductions.

---

## 2. Standardized Signal Model

All strategies output a standardized schema to ensure complete interoperability with future backtesting modules:

| Field | Type | Description |
| :--- | :--- | :--- |
| `date` | `str` | ISO 8601 observation date (`YYYY-MM-DD`). |
| `asset` | `str` | Canonical asset name (`Gold`, `Bitcoin`, `NVIDIA`). |
| `close` | `float` | Asset closing price on date $t$. |
| `strategy` | `str` | Applied strategy identifier (`sma_crossover`, `ema_trend`, `momentum`, `mean_reversion`). |
| `signal` | `SignalType` | Standardized signal: `BUY`, `HOLD`, `SELL`. |
| `fast_sma` | `float \| None` | Fast SMA value (for `sma_crossover`). |
| `slow_sma` | `float \| None` | Slow SMA value (for `sma_crossover`). |
| `short_ema` | `float \| None` | Short EMA value (for `ema_trend`). |
| `long_ema` | `float \| None` | Long EMA value (for `ema_trend`). |
| `momentum` | `float \| None` | Continuous percentage price change (for `momentum`). |
| `moving_average` | `float \| None` | Central moving average baseline (for `mean_reversion`). |
| `deviation` | `float \| None` | Percentage price deviation from central mean (for `mean_reversion`). |

---

## 3. Quantitative Trading Strategies

### 3.1. SMA Crossover Strategy (`sma_crossover`)

The Simple Moving Average (SMA) Crossover strategy captures medium-to-long term trend transitions by tracking when a faster moving average intersects a slower baseline moving average.

#### Mathematical Formulation
$$\text{SMA}_{\text{fast}}(t) = \frac{1}{n_{\text{fast}}} \sum_{i=0}^{n_{\text{fast}}-1} P_{t-i}$$
$$\text{SMA}_{\text{slow}}(t) = \frac{1}{n_{\text{slow}}} \sum_{i=0}^{n_{\text{slow}}-1} P_{t-i}$$

#### Signal Logic (Crossing Event)
- **`BUY`**: The fast SMA crosses from below or equal to the slow SMA to strictly above it:
  $$\text{SMA}_{\text{fast}}(t-1) \le \text{SMA}_{\text{slow}}(t-1) \quad \land \quad \text{SMA}_{\text{fast}}(t) > \text{SMA}_{\text{slow}}(t)$$
- **`SELL`**: The fast SMA crosses from above or equal to the slow SMA to strictly below it:
  $$\text{SMA}_{\text{fast}}(t-1) \ge \text{SMA}_{\text{slow}}(t-1) \quad \land \quad \text{SMA}_{\text{fast}}(t) < \text{SMA}_{\text{slow}}(t)$$
- **`HOLD`**: Otherwise.

> [!NOTE]
> Signals represent **discrete crossing events**. Once a `BUY` signal is generated, all subsequent bars where the fast SMA remains above the slow SMA emit `HOLD` to avoid generating redundant transaction commands.

- **Default Hyperparameters**: $n_{\text{fast}} = 20$, $n_{\text{slow}} = 50$.
- **Validation Constraints**: $n_{\text{fast}} \ge 2$, $n_{\text{slow}} \ge 2$, $n_{\text{fast}} < n_{\text{slow}}$.

---

### 3.2. EMA Trend Strategy (`ema_trend`)

The Exponential Moving Average (EMA) Trend strategy weights recent observations exponentially higher than older prices, reducing lag compared to arithmetic moving averages.

#### Mathematical Formulation
$$\alpha = \frac{2}{n + 1}$$
$$\text{EMA}_n(t) = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_n(t-1), \quad \text{where } \text{EMA}_n(0) = P_0$$

#### Signal Logic (Crossing Event)
- **`BUY`**: Short EMA crosses from below or equal to the long EMA to strictly above:
  $$\text{EMA}_{\text{short}}(t-1) \le \text{EMA}_{\text{long}}(t-1) \quad \land \quad \text{EMA}_{\text{short}}(t) > \text{EMA}_{\text{long}}(t)$$
- **`SELL`**: Short EMA crosses from above or equal to the long EMA to strictly below:
  $$\text{EMA}_{\text{short}}(t-1) \ge \text{EMA}_{\text{long}}(t-1) \quad \land \quad \text{EMA}_{\text{short}}(t) < \text{EMA}_{\text{long}}(t)$$
- **`HOLD`**: Otherwise.

- **Default Hyperparameters**: $n_{\text{short}} = 20$, $n_{\text{long}} = 50$.
- **Validation Constraints**: $n_{\text{short}} \ge 2$, $n_{\text{long}} \ge 2$, $n_{\text{short}} < n_{\text{long}}$.

---

### 3.3. Momentum Strategy (`momentum`)

The Momentum strategy measures the velocity of price change over a specified historical lookback period.

#### Mathematical Formulation
$$\text{Momentum}(t) = \frac{P_t}{P_{t - \text{lookback}}} - 1.0$$

#### Signal Logic (Zero-Line Crossing Event)
- **`BUY`**: Momentum emerges from non-positive into positive territory (bullish momentum acceleration):
  $$\text{Momentum}(t-1) \le 0.0 \quad \land \quad \text{Momentum}(t) > 0.0$$
- **`SELL`**: Momentum deteriorates from non-negative into negative territory (bearish momentum acceleration):
  $$\text{Momentum}(t-1) \ge 0.0 \quad \land \quad \text{Momentum}(t) < 0.0$$
- **`HOLD`**: Otherwise.

> [!TIP]
> The continuous `momentum` field retains the continuous rate-of-change value for regime identification, while the `signal` field records the discrete entry/exit events.

- **Default Hyperparameters**: $\text{lookback} = 20$.
- **Validation Constraints**: $\text{lookback} \ge 1$.

---

### 3.4. Mean Reversion Strategy (`mean_reversion`)

The Mean Reversion strategy operates under the hypothesis that prices that deviate excessively from their moving average baseline will tend to revert back to that central average.

#### Mathematical Formulation
$$\text{MA}_w(t) = \frac{1}{w} \sum_{i=0}^{w-1} P_{t-i}$$
$$\delta(t) = \frac{P_t - \text{MA}_w(t)}{\text{MA}_w(t)}$$

#### Signal Logic (Threshold Deviation Bounds)
- **`BUY`**: Price is depressed below the moving average by at least the specified threshold percentage (oversold condition):
  $$\delta(t) \le -\theta$$
- **`SELL`**: Price is elevated above the moving average by at least the specified threshold percentage (overbought condition):
  $$\delta(t) \ge +\theta$$
- **`HOLD`**: Price remains within the threshold band:
  $$-\theta < \delta(t) < +\theta$$

- **Default Hyperparameters**: $w = 20$, $\theta = 0.02$ (2.0% deviation).
- **Validation Constraints**: $w \ge 2$, $\theta > 0.0$.

---

## 4. Warm-Up Period Handling & Date Range Slicing

When an API client or backtester requests a filtered date range (e.g. `start_date="2024-01-01"`, `end_date="2024-12-31"`):
1. **Full Historical Calculation**: Moving averages, EMAs, deviations, and momentum are first calculated across the complete chronological historical dataset starting from $t_0$.
2. **Post-Calculation Slicing**: The resulting DataFrame is sliced down to the requested `start_date` and `end_date`.

This architecture completely eliminates warm-up artifacts for requested sub-ranges:

```
Full History:  [---------------- Warmup ----------------][=========== Requested Date Range ===========]
Indicator Calc: [======= Full Chronological Math =======][=========== Fully Warmed-Up Series ==========]
Output Sliced:                                          [=========== Accurate Output Signals =========]
```

---

## 5. Look-Ahead Bias Prevention

To ensure institutional mathematical rigor:
1. All moving averages and momentum calculations use backward-looking rolling windows with `center=False`.
2. No future price data at $t+k$ ($k > 0$) is accessible when generating the signal at time $t$.
3. Crossover checks strictly evaluate states at $t-1$ and $t$.
4. Automated property-based tests perturb future prices with extreme values ($50\times$, negative drops) and confirm that past signals through $t$ remain mathematically invariant.
