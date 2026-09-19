# QUANTLAB Backtesting & Portfolio Simulation Methodology

This document details the portfolio accounting model, trade execution mechanics, position sizing, transaction fees, performance attribution, and Buy-and-Hold benchmark comparison implemented in **Phase 7: Backtesting Engine** of the QUANTLAB quantitative intelligence platform.

---

## 1. Architectural Overview & Simulation Principles

The QUANTLAB backtesting engine translates analytical signals (`BUY`, `HOLD`, `SELL`) into a realistic portfolio trajectory with strict cash balance constraints, discrete trade life-cycles, and daily mark-to-market valuations.

```
+-----------------------------------------------------------------------------------------+
|                                  STRATEGY ENGINE (Phase 6)                              |
|   Generates deterministic signals at day t close: BUY, HOLD, SELL                       |
+--------------------------------------------+--------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                                BACKTESTING ENGINE (Phase 7)                             |
|                                                                                         |
|  1. Order Dispatch (t -> t+1 OPEN):                                                     |
|     - BUY on Day t Close  ==> Executes at Day t+1 OPEN at P_open,t+1                    |
|     - SELL on Day t Close ==> Executes at Day t+1 OPEN at P_open,t+1                    |
|                                                                                         |
|  2. Realistic Cash & Position Accounting:                                               |
|     - Cash subtracted upon entry: Notional + Fee                                        |
|     - Cash added upon exit: Notional - Fee                                              |
|     - Zero negative cash balances (no overdraft)                                        |
|                                                                                         |
|  3. Daily Mark-to-Market Valuation (Day t Close):                                       |
|     - Portfolio Value_t = Cash_t + (Quantity_t * Close_Price_t)                         |
|     - Daily Return_t = (Portfolio Value_t / Portfolio Value_{t-1}) - 1                  |
|     - Drawdown_t = (Portfolio Value_t / Running Peak_t) - 1                             |
|                                                                                         |
|  4. Buy-and-Hold Benchmark:                                                             |
|     - 100% Capital invested at initial OPEN with transaction fee                        |
|     - Daily mark-to-market over identical calendar period                               |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Trade Execution Timing & Look-Ahead Bias Prevention

To strictly prevent look-ahead bias:
1. **Signal Availability**: A strategy signal computed on day $t$ requires the closing price $P_{\text{close}, t}$, meaning it is only known after market close on day $t$.
2. **Execution Timing**: The order executes at the **OPEN** of the next available trading session ($t+1$) at $P_{\text{open}, t+1}$.
3. **End-of-Series Boundary**: If a signal is emitted on the final day of a backtest period, it is not executed because no subsequent open price exists within the simulation.

```
Day t:      [ Open ] ---- [ Intraday ] ---- [ Close / Signal Generated (BUY) ]
                                                            |
                                                            v
Day t+1:    [ Open / Trade Executed ($P_{open, t+1}$) ] ---- [ Close / Marked to Market ]
```

---

## 3. Position Sizing & Transaction Cost Accounting

### 3.1. Position Sizing
Let $C_t$ be available cash, $s \in (0.0, 1.0]$ be the configured `position_size` parameter, and $c \ge 0$ be the proportional `transaction_cost` rate (e.g. $0.001 = 0.1\%$).

Upon entering a `LONG` position:
- **Target Capital Allocation**:
  $$\text{Target Cash} = C_t \times s$$
- **Effective Unit Cost**:
  $$\text{Unit Cost} = P_{\text{open}, t+1} \times (1 + c)$$
- **Quantity Purchased**:
  $$Q = \frac{\text{Target Cash}}{\text{Unit Cost}}$$
- **Gross Entry Notional**:
  $$\text{Notional}_{\text{entry}} = Q \times P_{\text{open}, t+1}$$
- **Entry Transaction Cost**:
  $$\text{Cost}_{\text{entry}} = \text{Notional}_{\text{entry}} \times c$$
- **Cash Remaining**:
  $$C_{t+1} = C_t - (\text{Notional}_{\text{entry}} + \text{Cost}_{\text{entry}})$$

### 3.2. Trade Exit & Realized P&L
When exiting a `LONG` position at $P_{\text{open}, t+1}$:
- **Gross Exit Notional**:
  $$\text{Notional}_{\text{exit}} = Q \times P_{\text{open}, t+1}$$
- **Exit Transaction Cost**:
  $$\text{Cost}_{\text{exit}} = \text{Notional}_{\text{exit}} \times c$$
- **Net Cash Received**:
  $$\text{Cash Received} = \text{Notional}_{\text{exit}} - \text{Cost}_{\text{exit}}$$
- **Updated Cash Balance**:
  $$C_{t+1} = C_t + \text{Cash Received}$$
- **Gross P&L**:
  $$\text{Gross P&L} = \text{Notional}_{\text{exit}} - \text{Notional}_{\text{entry}}$$
- **Net P&L**:
  $$\text{Net P&L} = \text{Gross P&L} - (\text{Cost}_{\text{entry}} + \text{Cost}_{\text{exit}})$$
- **Percentage Net Return**:
  $$\text{Return Pct} = \frac{\text{Net P&L}}{\text{Notional}_{\text{entry}} + \text{Cost}_{\text{entry}}}$$

---

## 4. End-of-Backtest Position Handling

If a position is still `LONG` when the backtest reaches its final date:
1. No synthetic exit trade is fabricated.
2. The trade is marked as an `open_position`.
3. Unrealized P&L is calculated using the final session's closing price $P_{\text{close}, N}$:
   $$\text{Unrealized P&L} = (Q \times P_{\text{close}, N}) - \text{Notional}_{\text{entry}}$$
4. The final portfolio equity value and equity curve naturally reflect the marked position.

---

## 5. Performance Attribution Metrics

The backtesting engine calculates statistical, risk-adjusted, and trade performance metrics:

| Metric | Formula | Description |
| :--- | :--- | :--- |
| **Total Return** | $\frac{V_{\text{final}} - V_{\text{initial}}}{V_{\text{initial}}}$ | Cumulative return across entire backtest |
| **CAGR** | $(1 + \text{Total Return})^{\frac{365.25}{\text{Days}}} - 1$ | Compound Annual Growth Rate |
| **Annualized Volatility** | $\sigma_{\text{daily}} \times \sqrt{N}$ | Standard deviation of daily portfolio returns ($N=252$ for Gold/NVDA, $365$ for BTC) |
| **Sharpe Ratio** | $\frac{\bar{R}_{\text{daily}} - R_{f,\text{daily}}}{\sigma_{\text{daily}}} \times \sqrt{N}$ | Risk-adjusted excess return per unit volatility |
| **Maximum Drawdown** | $\min_t \left(\frac{V_t}{\max_{\tau \le t} V_\tau} - 1\right)$ | Maximum observed peak-to-trough decline ($\le 0.0$) |
| **Win Rate** | $\frac{\text{Winning Trades}}{\text{Total Completed Trades}}$ | Proportion of completed trades with $\text{Net P&L} > 0$ |
| **Gross Profit** | $\sum \text{Net P&L}_{\text{winning}}$ | Total gains generated by profitable trades |
| **Gross Loss** | $\sum |\text{Net P&L}_{\text{losing}}|$ | Total losses generated by unprofitable trades |
| **Net Profit** | $\sum \text{Net P&L}_{\text{all}}$ | Aggregate dollar profit after all transaction fees |
| **Average Trade Return** | $\frac{1}{M}\sum_{i=1}^M \text{Return Pct}_i$ | Arithmetic mean of percentage returns per trade |

---

## 6. Buy-and-Hold Benchmark & Comparative Analysis

Each backtest automatically computes a passive Buy-and-Hold benchmark under the same initial capital, date range, asset, and transaction fee assumptions:
- **Benchmark Initialization**: Invests 100% of capital at the first session's opening price, paying entry fee $c$.
- **Benchmark Valuation**: Daily mark-to-market at closing settlement prices.
- **Comparison Differentials**:
  - `return_difference` = $\text{Total Return}_{\text{strat}} - \text{Total Return}_{\text{bench}}$
  - `annualized_return_difference` = $\text{CAGR}_{\text{strat}} - \text{CAGR}_{\text{bench}}$
  - `volatility_difference` = $\text{Vol}_{\text{strat}} - \text{Vol}_{\text{bench}}$
  - `sharpe_difference` = $\text{Sharpe}_{\text{strat}} - \text{Sharpe}_{\text{bench}}$
  - `mdd_difference` = $\text{MDD}_{\text{strat}} - \text{MDD}_{\text{bench}}$
