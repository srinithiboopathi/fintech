# QUANTLAB Backtesting Methodology & Financial Integrity

## 1. Core Principles

To ensure rigorous quantitative analysis, the QUANTLAB backtesting engine operates under strict simulation integrity standards:

1. **No Look-Ahead Bias**:
   Signals generated at time $t$ evaluate indicators computed strictly on prices $\le t$. Order executions occur at $t+1$ open (or close of $t$ if conservative next-tick execution is modeled).

2. **Realistic Transaction Costs**:
   Every trade incurs:
   - **Commission**: Flat fee or basis points (bps) per transaction.
   - **Slippage / Spread**: Percentage degradation of execution price reflecting market liquidity.

3. **Cash & Portfolio Simulation**:
   Backtests maintain:
   - `cash_balance`
   - `holdings` (quantity of units owned)
   - `portfolio_value` = $\text{cash} + (\text{holdings} \times \text{current\_price})$
   - `realized_pnl` and `unrealized_pnl`

4. **Benchmark Comparison**:
   All strategies are benchmarked against the standard **Buy-and-Hold** strategy over the identical time horizon.

---

## 2. Strategy Universe

- **SMA Crossover**: Generates buy signals when short-period SMA crosses above long-period SMA; cash out when it crosses below.
- **EMA Trend**: Exponential trend-following filter capturing momentum inflection points.
- **Momentum (RSI / Rate of Change)**: Capitalizes on persistent directional velocity.
- **Mean Reversion (Bollinger Bands / Z-score)**: Captures price reversals when extreme statistical standard deviations occur.

---

## 3. Performance Metrics Formulae

- **CAGR (Compound Annual Growth Rate)**:
  $$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{1}{Y}} - 1$$
- **Win Rate**:
  $$\text{Win Rate} = \frac{\text{Profitable Trades}}{\text{Total Trades}}$$
- **Profit Factor**:
  $$\text{Profit Factor} = \frac{\sum \text{Gross Profits}}{\sum |\text{Gross Losses}|}$$
- **Calmar Ratio**:
  $$\text{Calmar Ratio} = \frac{\text{CAGR}}{|\text{Max Drawdown}|}$$
