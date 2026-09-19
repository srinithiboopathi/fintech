# QUANTLAB Strategy Robustness & Sensitivity Methodology

## 1. Overview and Quantitative Purpose

The **Strategy Robustness Lab** in QUANTLAB provides a deterministic framework for evaluating how algorithmic trading strategies perform under varying parameterizations, transaction cost assumptions, and historical time horizons. 

Traditional backtesting often suffers from *overfitting* (data snooping / curve fitting), where a single parameter combination is cherry-picked because it happened to perform well on a specific sample. The Robustness Lab exposes the sensitivity surface of a strategy across parameter neighborhoods to assess stability.

> [!IMPORTANT]
> **No Strategy Ranking / No Optimization Claim**:
> The Robustness Lab does **NOT** rank strategies, score configurations, or declare a "best" parameter set. It provides objective, unranked empirical ranges (min/max/averages) across the parameter grid. Quantitative researchers must inspect parameter neighborhoods rather than isolated peak performance points.

---

## 2. Multi-Dimensional Sensitivity Variables

### 2.1 Strategy Hyperparameter Grids
Each quantitative strategy supports systematic exploration across its defined parameter spaces:

1. **SMA Crossover (`sma_crossover`)**:
   - `fast_period`: Fast Simple Moving Average lookback ($n_{\text{fast}} \ge 2$).
   - `slow_period`: Slow Simple Moving Average lookback ($n_{\text{slow}} \ge 2$).
   - **Constraint**: $n_{\text{fast}} < n_{\text{slow}}$. Any combinations violating this constraint are pruned prior to execution.

2. **EMA Trend (`ema_trend`)**:
   - `short_period`: Short Exponential Moving Average span ($n_{\text{short}} \ge 2$).
   - `long_period`: Long Exponential Moving Average span ($n_{\text{long}} \ge 2$).
   - **Constraint**: $n_{\text{short}} < n_{\text{long}}$.

3. **Momentum (`momentum`)**:
   - `lookback`: Return lookback window in trading days ($L \ge 1$).

4. **Mean Reversion (`mean_reversion`)**:
   - `window`: Moving average benchmark window ($W \ge 2$).
   - `threshold`: Percentage price deviation threshold ($\theta > 0$).

### 2.2 Transaction Cost Variations
Backtest outcomes are evaluated across varying friction levels to quantify turnover vulnerability:
- Examples: `[0.0, 0.001, 0.002]` (representing 0 bps, 10 bps, and 20 bps round-trip fees).

### 2.3 Backtest Period Variations
Sensitivity across market cycles can be assessed by providing explicit sub-period windows:
- Example: `[{"start_date": "2020-01-01", "end_date": "2022-12-31"}, {"start_date": "2023-01-01", "end_date": "2024-12-31"}]`.

---

## 3. Cartesian Grid Construction and Safety Limits

The total number of backtest configurations $N$ is the Cartesian product:
$$N = |\text{Valid Parameter Tuples}| \times |\text{Transaction Costs}| \times |\text{Period Windows}|$$

### Safety Limit Enactment
To prevent combinatorial explosion and excessive server compute overhead:
- **Default Maximum Limit**: `MAX_CONFIGURATIONS = 100` (configurable up to 500).
- If $N > \text{max\_configurations}$, the engine rejects the request with an explicit `400 Bad Request` validation error detailing the count and guidance to reduce step resolution. **The grid is never silently truncated.**

---

## 4. Execution Engine Integration

The Robustness Lab directly invokes the Phase 7 `BacktestEngine.run()` for each individual configuration. No backtesting or accounting logic is duplicated.

For each configuration, the following metrics are recorded:
- `parameters`: Exact settings used.
- `transaction_cost`: Transaction fee applied.
- `start_date`, `end_date`: Evaluated date window.
- `initial_capital`, `final_portfolio_value`: Equity progression.
- `total_return`: Cumulative percentage return.
- `annualized_return`: Compound Annual Growth Rate (CAGR).
- `annualized_volatility`: Sample annualized standard deviation.
- `sharpe_ratio`: Zero-rf risk-adjusted return ratio.
- `maximum_drawdown`: Peak-to-trough equity drop.
- `number_of_trades`: Total executed trades.
- `win_rate`: Fraction of profitable trades.

---

## 5. Aggregate Descriptive Metrics

The aggregate summary computes bounding ranges across all tested combinations without ranking:
- `return_range`: `{"min": float, "max": float}`
- `sharpe_range`: `{"min": float, "max": float}`
- `drawdown_range`: `{"min": float, "max": float}`
- `trades_range`: `{"min": int, "max": int}`
- `win_rate_range`: `{"min": float, "max": float}`

---

## 6. Interpretation and Limitations

1. **Parameter Fragility (Cliff Risk)**: If a strategy performs well at $(20, 50)$ but suffers severe degradation at $(19, 50)$ or $(21, 50)$, it is fragile and likely overfit.
2. **Cost Drag**: High-turnover strategies (e.g. short momentum) typically show steep decay across cost steps.
3. **Historical Non-Stationarity**: Robustness across past subsets does not guarantee future stability.
