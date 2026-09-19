# QuantLab Backtesting Methodology & Engine Mechanics

## 1. Simulation Principles

QuantLab operates on an event-driven and vectorized framework designed with strict financial engineering safeguards:

1. **Zero Look-Ahead Bias**: Signals generated at bar $t$ strictly use historical data up to and including bar $t$. Order execution occurs at bar close or bar $t+1$ with zero future leakage.
2. **Deterministic & Reproducible**: All indicators, strategy signals, and equity curves evaluate identically on consecutive runs with identical parameters.
3. **Explicit Transaction Friction**: Every trade simulates broker commission (configurable basis points) and market slippage percentage.
4. **Survivorship & Continuity**: Multi-asset continuous daily feeds for Gold (`GC=F`), Bitcoin (`BTC-USD`), and NVIDIA (`NVDA`) maintain real data integrity without fabricated prices.

---

## 2. Order Execution & Slippage Model

Given a target trade quantity $Q$ and current market price $P_t$:

$$\text{Execution Price} = P_t \times (1 \pm \text{slippage\_pct})$$

where slippage increases the purchase price for `BUY` orders ($+$) and decreases the realized price for `SELL` orders ($-$).

Broker commission is deducted directly from portfolio cash:

$$\text{Commission} = \text{Execution Price} \times Q \times \frac{\text{commission\_bps}}{10,000}$$

---

## 3. Position Sizing Models

QuantLab supports 4 distinct allocation algorithms:

1. **Percentage of Equity (`percent_equity`)**: A target fraction $w \in (0, 1]$ of total net portfolio equity is committed per position:
   $$Q = \frac{\text{Portfolio Equity} \times w}{P_t}$$
2. **Fixed Dollar Allocation (`fixed_amount`)**: A constant currency amount is allocated:
   $$Q = \frac{\text{Fixed Amount}}{P_t}$$
3. **Volatility Parity (Inverse Volatility)**: Allocations are weighted inversely proportional to 30-day realized asset volatility $\sigma_i$.
4. **Fractional Kelly Criterion**: Position size scaled to optimize long-term geometric compounding while constraining ruin risk.

---

## 4. Benchmark Comparison (Strategy vs. Buy & Hold)

Every backtest automatically generates an aligned passive **Buy & Hold Benchmark** over the identical date range and initial capital.

Key comparative metrics calculated:
- **Final Portfolio Equity & Total Return (%)**
- **Compound Annual Growth Rate (CAGR %)**
- **Annualized Volatility (%)**
- **Sharpe Ratio & Sortino Ratio**
- **Maximum Drawdown (%) & Recovery Duration**
- **Alpha Excess Return (%)**: $\text{Strategy Return} - \text{Buy\&Hold Return}$

---

## 5. Built-in Quantitative Strategies

### 1. Dual SMA Golden Cross (`sma_crossover`)
- **Long Entry**: Fast SMA crosses above Slow SMA.
- **Exit**: Fast SMA crosses below Slow SMA, or dynamic Stop-Loss / Take-Profit threshold reached.

### 2. Triple EMA Trend Ribbon (`ema_trend`)
- Uses triple exponential moving averages (Fast 9, Mid 21, Slow 55).
- **Long Entry**: Fast EMA > Mid EMA > Slow EMA (bullish alignment).
- **Exit**: Fast EMA < Mid EMA or Stop-Loss.

### 3. Momentum Breakout (`momentum`)
- **Long Entry**: Price breaks out above the highest high of the previous $N$ bars (Donchian channel) with $\text{RSI}(14) > 50$.
- **Exit**: Price closes below the lowest low of the lookback period.

### 4. Mean Reversion (`mean_reversion`)
- **Long Entry**: Price touches/dips below the 2.0σ Lower Bollinger Band and $\text{RSI}(14) < 35$ (oversold).
- **Exit**: Price reverts to the 20-day SMA middle band or $\text{RSI}(14) > 70$.
