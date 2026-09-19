# QUANTLAB Data Dictionary & Kaggle Ingestion Specification

## 1. Asset Universe & Source Dataset Mapping

| Asset Identifier | Asset Class | Raw Kaggle Source File | Raw Frequency | Raw Rows | Processed Rows | Output File |
|---|---|---|---|---|---|---|
| **Gold** | Commodity (Futures GC=F) | `datasets/raw/gold/Gold_Spot_historical_data.csv` | Daily | 6,358 | 6,358 | `datasets/processed/gold_daily.csv` |
| **Bitcoin** | Digital Asset (BTC/USD) | `datasets/raw/bitcoin/BTC-2017min.csv` | 1-Minute Intraday | 525,599 | 365 | `datasets/processed/bitcoin_daily.csv` |
| **NVIDIA** | Equities (NVDA Semiconductor) | `datasets/raw/nvidia/NVIDIA_historical_data.csv` | Daily | 6,778 | 6,778 | `datasets/processed/nvidia_daily.csv` |

---

## 2. Actual Discovered Raw Dataset Schemas

### A. Gold (`Gold_Spot_historical_data.csv`)
- **Raw Columns**: `['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'name']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS-05:00` (ISO 8601 with timezone offset)
- **Date Range**: `2000-08-30` to `2025-12-31`
- **Mapping**:
  - `Date` $\rightarrow$ `date` (`YYYY-MM-DD`)
  - `'Gold'` $\rightarrow$ `asset`
  - `Open` $\rightarrow$ `open`
  - `High` $\rightarrow$ `high` (Envelope aligned with `max(High, Open, Close)`)
  - `Low` $\rightarrow$ `low` (Envelope aligned with `min(Low, Open, Close)`)
  - `Close` $\rightarrow$ `close`
  - `Volume` $\rightarrow$ `volume`

### B. Bitcoin (`BTC-2017min.csv`)
- **Raw Columns**: `['unix', 'date', 'symbol', 'open', 'high', 'low', 'close', 'Volume BTC', 'Volume USD']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS` (1-minute intervals, stored in descending chronological order)
- **Date Range**: `2017-01-01 00:01:00` to `2017-12-31 23:59:00` (Full 2017 calendar year)
- **Daily Aggregation Logic**:
  - Sorted ascending chronologically before grouping by calendar day (`YYYY-MM-DD`).
  - `open` = First 1-minute open of the day (`00:01` observation)
  - `high` = Maximum 1-minute high across all observations in the day
  - `low` = Minimum 1-minute low across all observations in the day
  - `close` = Last 1-minute close of the day (`23:59` observation)
  - `volume` = Sum of `Volume BTC` traded in the day

### C. NVIDIA (`NVIDIA_historical_data.csv`)
- **Raw Columns**: `['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'ticker', 'name']`
- **Date Format**: `YYYY-MM-DD HH:MM:SS-05:00` (ISO 8601 with timezone offset)
- **Date Range**: `1999-01-22` to `2025-12-31`
- **Mapping**:
  - `Date` $\rightarrow$ `date` (`YYYY-MM-DD`)
  - `'NVIDIA'` $\rightarrow$ `asset`
  - `Open` $\rightarrow$ `open`
  - `High` $\rightarrow$ `high`
  - `Low` $\rightarrow$ `low`
  - `Close` $\rightarrow$ `close`
  - `Volume` $\rightarrow$ `volume`

---

## 3. Normalized Time-Series Schema

The standardized dataset format used across all backend calculation engines (`gold_daily.csv`, `bitcoin_daily.csv`, `nvidia_daily.csv`, and unified `market_data.csv`):

| Field Name | Type | Unit / Format | Description |
|---|---|---|---|
| `date` | `string` | `YYYY-MM-DD` | Normalized calendar trade date (ISO-8601 string) |
| `asset` | `string` | `Gold` / `Bitcoin` / `NVIDIA` | Standard asset identifier name |
| `open` | `float` | USD ($) | Market opening price for the day |
| `high` | `float` | USD ($) | Highest price during the session ($\ge \max(\text{open}, \text{close})$) |
| `low` | `float` | USD ($) | Lowest price during the session ($\le \min(\text{open}, \text{close})$) |
| `close` | `float` | USD ($) | Closing settlement price for the day |
| `volume` | `float` | Traded units | Total traded volume (contracts for Gold, BTC for Bitcoin, shares for NVDA) |

---

## 4. Quantitative & Statistical Metrics Reference

| Metric Name | API Field | Type | Unit / Format | Mathematical Definition | Annualization Factor | Interpretation |
|---|---|---|---|---|---|---|
| **Simple Moving Average** | `sma` | `float` / `null` | USD ($) | $\text{SMA}_n = \frac{1}{n}\sum_{i=0}^{n-1} P_{t-i}$ | N/A | Trend baseline over lookback period $n$ |
| **Exponential Moving Average** | `ema` | `float` / `null` | USD ($) | $\text{EMA}_t = \alpha P_t + (1-\alpha)\text{EMA}_{t-1}$ | N/A | Exponentially smoothed trend line ($\alpha = \frac{2}{n+1}$) |
| **Daily Return** | `daily_return` | `float` / `null` | Ratio (e.g. `0.02` = +2%) | $R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$ | N/A | Single session arithmetic percentage return |
| **Cumulative Return** | `cumulative_return` | `float` / `null` | Ratio (e.g. `1.50` = +150%) | $\text{CR}_t = \prod_{i=1}^t (1 + R_i) - 1$ | N/A | Compounded wealth growth of \$1 initial capital |
| **Rolling Volatility** | `rolling_volatility` | `float` / `null` | Daily ratio | $\sigma_{\text{daily}} = \sqrt{\frac{\sum (R_t - \bar{R})^2}{w - 1}}$ | N/A | Historical rolling sample standard deviation ($w \ge 2$) |
| **Annualized Volatility** | `annualized_volatility` | `float` / `null` | Annual ratio | $\sigma_{\text{ann}} = \sigma_{\text{daily}} \times \sqrt{N}$ | Gold/NVDA: 252, BTC: 365 | Volatility scaled to annual trading sessions |
| **Sharpe Ratio** | `sharpe_ratio` | `float` / `null` | Dimensionless ratio | $\text{Sharpe} = \frac{\bar{R}_e}{\sigma_{R_e}} \times \sqrt{N}$ | Gold/NVDA: 252, BTC: 365 | Risk-adjusted excess return per unit volatility |
| **Maximum Drawdown** | `maximum_drawdown` | `float` / `null` | Ratio $\le 0.0$ (e.g. `-0.25`) | $\text{MDD} = \min_{t} (\frac{P_t}{\text{Peak}_t} - 1)$ | N/A | Maximum observed peak-to-trough equity decline |
| **Rolling Return** | `rolling_return` | `float` / `null` | Ratio | $\text{RR}_{w,t} = \frac{P_t}{P_{t-w}} - 1$ | N/A | $w$-period arithmetic price momentum |
| **Running Peak** | `peak` | `float` | USD ($) | $\text{Peak}_t = \max_{0 \le \tau \le t} P_\tau$ | N/A | High-water mark of price / wealth series |
| **Pearson Correlation** | `correlation` | `float` / `null` | Dimensionless $[-1.0, 1.0]$ | $r = \frac{\text{Cov}(R_A, R_B)}{\sigma_A \sigma_B}$ | N/A | Linear co-movement between aligned daily asset returns |
| **Rolling Correlation** | `rolling_correlation` | `float` / `null` | Dimensionless $[-1.0, 1.0]$ | $r_t = \frac{\text{Cov}_w(R_A, R_B)}{\sigma_{A,w} \sigma_{B,w}}$ | N/A | Time-varying linear dependency over lookback window $w$ |
| **Compound Annual Growth Rate** | `annualized_return` | `float` / `null` | Annual ratio | $\text{CAGR} = (1 + \text{CR})^{365.25 / \text{Days}} - 1$ | N/A | Geometric annualized return growth |
| **Overlapping Observations** | `observations` / `aligned_records` | `integer` | Count | Count of joint active trading dates | N/A | Sample size used for statistical validity |

---

## 5. Strategy Engine Fields & Signal Semantics (Phase 6)

| Field Name | API Key | Type | Possible Values / Unit | Description |
|---|---|---|---|---|
| **Strategy Identifier** | `strategy` | `string` | `sma_crossover`, `ema_trend`, `momentum`, `mean_reversion` | Quantitative strategy model identifier |
| **Trading Signal** | `signal` | `string` (Enum) | `BUY`, `HOLD`, `SELL` | Discrete regime entry/exit crossing event |
| **Fast SMA** | `fast_sma` | `float` / `null` | USD ($) | Moving average calculated over `fast_period` |
| **Slow SMA** | `slow_sma` | `float` / `null` | USD ($) | Moving average calculated over `slow_period` |
| **Short EMA** | `short_ema` | `float` / `null` | USD ($) | Exponential moving average over `short_period` span |
| **Long EMA** | `long_ema` | `float` / `null` | USD ($) | Exponential moving average over `long_period` span |
| **Continuous Momentum** | `momentum` | `float` / `null` | Percentage ratio | Rate of price change: $(P_t / P_{t-\text{lookback}}) - 1$ |
| **Moving Average Baseline** | `moving_average` | `float` / `null` | USD ($) | Rolling arithmetic mean baseline for mean reversion |
| **Deviation Ratio** | `deviation` | `float` / `null` | Ratio (e.g. `-0.03`) | Percentage deviation from baseline: $(P_t - \text{MA}_t) / \text{MA}_t$ |
| **Deviation Threshold** | `threshold` | `float` | Ratio (e.g. `0.02`) | Minimum deviation required to trigger mean reversion signals |
| **Signal Counts Breakdown** | `summary` | `object` | `{buy: N, sell: N, hold: N, total: N}` | Aggregate signal distribution for requested series |

---

## 6. Backtesting & Portfolio Simulation Fields (Phase 7)

| Field Name | API Key | Type | Unit / Format | Description |
|---|---|---|---|---|
| **Initial Capital** | `initial_capital` | `float` | USD ($) | Starting cash balance for the portfolio simulation |
| **Position Size** | `position_size` | `float` | Ratio $(0.0, 1.0]$ | Fraction of available cash allocated when entering trades |
| **Transaction Cost** | `transaction_cost` | `float` | Ratio (e.g. `0.001`) | Proportional fee applied on entry and exit notionals |
| **Final Portfolio Value** | `final_portfolio_value` | `float` | USD ($) | Total marked-to-market equity at simulation termination |
| **Cash Balance** | `cash` | `float` | USD ($) | Liquid uninvested capital held in portfolio |
| **Position Quantity** | `position_quantity` | `float` | Units | Number of asset units/shares currently held |
| **Position Value** | `position_value` | `float` | USD ($) | Current market value of open position ($\text{Quantity} \times P_{\text{close}}$) |
| **Portfolio Value** | `portfolio_value` | `float` | USD ($) | Total marked wealth: $\text{Cash} + \text{Position Value}$ |
| **Trade ID** | `trade_id` | `integer` | Sequential | Unique sequential identifier for completed trade |
| **Entry Date** | `entry_date` | `string` | `YYYY-MM-DD` | Session date when position was opened |
| **Exit Date** | `exit_date` | `string` | `YYYY-MM-DD` | Session date when position was closed |
| **Entry Price** | `entry_price` | `float` | USD ($) | Fill price on trade entry ($P_{\text{open}}$ of entry session) |
| **Exit Price** | `exit_price` | `float` | USD ($) | Fill price on trade exit ($P_{\text{open}}$ of exit session) |
| **Entry Notional** | `entry_notional` | `float` | USD ($) | Gross dollar value allocated at entry ($\text{Quantity} \times P_{\text{entry}}$) |
| **Exit Notional** | `exit_notional` | `float` | USD ($) | Gross dollar value realized at exit ($\text{Quantity} \times P_{\text{exit}}$) |
| **Entry Cost** | `entry_cost` | `float` | USD ($) | Dollar transaction fee deducted upon trade entry |
| **Exit Cost** | `exit_cost` | `float` | USD ($) | Dollar transaction fee deducted upon trade exit |
| **Gross P&L** | `gross_pnl` | `float` | USD ($) | Dollar profit/loss before deducting transaction fees |
| **Net P&L** | `net_pnl` | `float` | USD ($) | Net dollar profit/loss after subtracting entry and exit fees |
| **Trade Return** | `return_pct` | `float` | Ratio | Percentage net return earned on invested capital |
| **Holding Period** | `holding_period_days` | `integer` | Days | Total calendar days between entry date and exit date |
| **Number of Trades** | `number_of_trades` | `integer` | Count | Total round-trip trades completed in backtest |
| **Winning Trades** | `winning_trades` | `integer` | Count | Completed trades with positive net P&L |
| **Losing Trades** | `losing_trades` | `integer` | Count | Completed trades with negative net P&L |
| **Win Rate** | `win_rate` | `float` | Ratio $[0.0, 1.0]$ | Proportion of completed trades that were profitable |
| **Gross Profit** | `gross_profit` | `float` | USD ($) | Sum of net gains generated across all winning trades |
| **Gross Loss** | `gross_loss` | `float` | USD ($) | Sum of net losses generated across all losing trades |
| **Net Profit** | `net_profit` | `float` | USD ($) | Cumulative net profit/loss across all completed trades |
| **Average Trade Return** | `average_trade_return` | `float` | Ratio | Arithmetic mean percentage return across all trades |
| **Unrealized P&L** | `unrealized_pnl` | `float` | USD ($) | Floating profit/loss on open position held at backtest end |
| **Unrealized Return** | `unrealized_return_pct` | `float` | Ratio | Floating percentage return on open position |
| **Benchmark Final Value** | `final_value` | `float` | USD ($) | Final equity of 100% Buy-and-Hold passive benchmark |
| **Return Difference** | `return_difference` | `float` | Ratio | Strategy total return minus Benchmark total return |
| **Sharpe Difference** | `sharpe_difference` | `float` | Ratio | Strategy Sharpe ratio minus Benchmark Sharpe ratio |
| **MDD Difference** | `mdd_difference` | `float` | Ratio | Strategy Maximum Drawdown minus Benchmark Maximum Drawdown |

---

## 7. Strategy Robustness Fields (Phase 8)

| Field Name | API Key | Type | Unit / Format | Description |
|---|---|---|---|---|
| **Parameter Grid** | `strategy_parameter_grid` | `dict` | Key: List | Mapping of hyperparameter names to candidate test values |
| **Transaction Costs** | `transaction_costs` | `list[float]` | Ratio list | Collection of candidate friction rates tested |
| **Tested Periods** | `periods_tested` | `list[dict]` | Date ranges | Array of sub-window start/end date pairs evaluated |
| **Total Configurations** | `total_configurations` | `integer` | Count | Total Cartesian product backtests executed ($N \le 100$) |
| **Return Range** | `return_range` | `dict` | `min`/`max` | Minimum and maximum total returns observed across configurations |
| **Sharpe Range** | `sharpe_range` | `dict` | `min`/`max` | Minimum and maximum Sharpe ratios observed across configurations |
| **Drawdown Range** | `drawdown_range` | `dict` | `min`/`max` | Minimum and maximum maximum drawdowns observed across configurations |
| **Trades Range** | `trades_range` | `dict` | `min`/`max` | Minimum and maximum completed trade counts observed |
| **Win Rate Range** | `win_rate_range` | `dict` | `min`/`max` | Minimum and maximum win rates observed across configurations |

---

## 8. Market Regime Analysis Fields (Phase 8)

| Field Name | API Key | Type | Unit / Format | Description |
|---|---|---|---|---|
| **Trend Window** | `trend_window` | `integer` | Days (default: 50) | Lookback window for Simple Moving Average trend baseline |
| **Trend Value** | `trend_value` | `float` | USD ($) | Moving average price at date $t$ |
| **Primary Regime** | `regime` | `string` | `BULL` / `BEAR` / `null` | Trend classification: `BULL` ($P_t > \text{SMA}$) or `BEAR` ($P_t \le \text{SMA}$) |
| **Volatility Window** | `volatility_window` | `integer` | Days (default: 20) | Lookback window for rolling annualized volatility |
| **Rolling Volatility** | `rolling_volatility` | `float` | Annualized ratio | Rolling standard deviation scaled by $\sqrt{252}$ or $\sqrt{365}$ |
| **Volatility Threshold** | `volatility_threshold` | `float` | Annualized ratio | Median threshold dividing high vs low volatility regimes |
| **Threshold Mode** | `threshold_mode` | `string` | `historical_descriptive` / `expanding_threshold` | Methodology used to determine volatility cutoff |
| **Volatility State** | `volatility_state` | `string` | `HIGH_VOLATILITY` / `LOW_VOLATILITY` / `null` | Volatility state: `HIGH` ($\sigma > \theta$) or `LOW` ($\sigma \le \theta$) |
| **Transition Type** | `transition_type` | `string` | `regime` / `volatility` | Category of state change event |
| **From State** | `from_state` | `string` | State enum string | Prior active regime or volatility state |
| **To State** | `to_state` | `string` | State enum string | Newly activated regime or volatility state |



