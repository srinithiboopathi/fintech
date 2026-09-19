# QUANTLAB Market Regime Analysis Methodology

## 1. Overview and Quantitative Purpose

The **Market Regime Analysis Engine** classifies historical market dynamics into quantitative trend regimes and volatility states. Market returns exhibit non-stationary distributions, clustering of volatility, and structural shifts between trending and mean-reverting environments.

> [!IMPORTANT]
> **Deterministic Quantitative Analysis (No Machine Learning / No Future Prediction)**:
> This module performs purely backward-looking, deterministic classification of historical time-series data. It does not predict future regimes or make probabilistic forecasts.

---

## 2. Classification Methodology

The engine calculates two orthogonal dimensions for each daily observation:

```
                      ┌───────────────────────────┐
                      │    Primary Trend Regime   │
                      │       (BULL / BEAR)       │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │ Secondary Volatility State│
                      │    (HIGH_VOL / LOW_VOL)   │
                      └───────────────────────────┘
```

### 2.1 Trend Classification (Primary Regime)
- **Default Parameter**: `trend_window = 50` days.
- **Indicator**: Simple Moving Average: $\text{SMA}_W(t) = \frac{1}{W} \sum_{i=0}^{W-1} P_{t-i}$ with `center=False`.
- **Classification Rules**:
  $$\text{Regime}_t = \begin{cases} \text{BULL} & \text{if } P_t > \text{SMA}_W(t) \\ \text{BEAR} & \text{if } P_t \le \text{SMA}_W(t) \\ \text{null} & \text{if } t < W - 1 \text{ (warm-up)} \end{cases}$$

### 2.2 Volatility State Classification (Secondary State)
- **Default Parameter**: `volatility_window = 20` days.
- **Indicator**: Rolling Annualized Volatility:
  $$\sigma_{\text{ann}}(t) = \text{std}(R_{t-W+1 \dots t}, \text{ddof}=1) \times \sqrt{\text{annualization\_factor}}$$
  where `annualization_factor = 365` for Bitcoin and `252` for Gold/NVIDIA.

---

## 3. Volatility Threshold Modes & Look-Ahead Bias Considerations

The engine supports two distinct threshold determination modes:

### 3.1 Historical Descriptive Threshold (`historical_descriptive` — Default)
- **Formula**: Constant threshold $\theta = \text{median}(\{\sigma_{\text{ann}}(t) \mid \sigma_{\text{ann}}(t) \text{ is valid}\})$.
- **Usage**: Retrospective historical benchmarking.
- **Limitation**: Not causal / point-in-time, because observations from future dates influence the full-sample median threshold.

### 3.2 Expanding Threshold (`expanding_threshold`)
- **Formula**: Time-varying causal threshold:
  $$\theta(t) = \text{median}(\{\sigma_{\text{ann}}(1), \sigma_{\text{ann}}(2), \dots, \sigma_{\text{ann}}(t)\})$$
- **Usage**: Strict point-in-time quantitative backtesting and simulation.
- **Property**: Future observations after date $t$ have zero impact on today's threshold or volatility state classification.

---

## 4. State Transitions and Descriptive Statistics

### 4.1 Transition Detection
State transitions in primary regime (`BULL` $\leftrightarrow$ `BEAR`) and volatility state (`HIGH_VOLATILITY` $\leftrightarrow$ `LOW_VOLATILITY`) are detected chronologically:
- `date`: Date of transition event.
- `transition_type`: `"regime"` or `"volatility"`.
- `from_state`: Prior state.
- `to_state`: New active state.

### 4.2 Descriptive Regime Statistics
For each state segment, the following empirical metrics are computed over all constituent trading days:
- `observation_count`: Total trading days in state.
- `percentage`: Share of total classified trading days.
- `start_date`, `end_date`: Observed bounds.
- `average_daily_return`: Arithmetic mean of daily returns.
- `cumulative_return`: Compounded return $\prod (1 + R_t) - 1$.
- `annualized_volatility`: Sample annualized standard deviation.
- `sharpe_ratio`: Zero-rf risk-adjusted return ratio.
- `maximum_drawdown`: Peak-to-trough drawdown on the compounded equity curve.

---

## 5. Warm-Up & Date Windowing Discipline

Indicators are always calculated on the complete historical time series prior to applying any user-specified `start_date` / `end_date` filters. This guarantees proper moving average and rolling volatility warm-up without synthetic forward-fills or truncated window distortions.
