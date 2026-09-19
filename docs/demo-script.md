# QUANTLAB Hackathon Presentation & Live Demo Script

**5–8 Minute Judge Presentation & Live Walkthrough**

---

## 🎯 Executive Elevator Pitch (30 Seconds)
> "QuantLab is an institutional-grade quantitative financial intelligence and strategy backtesting platform. Unlike toy finance apps or retail crypto dashboards, QuantLab is built for quantitative researchers, portfolio managers, and algorithmic traders. It provides real-time historical analytics across Gold, Bitcoin, and NVIDIA, compute-heavy cross-asset covariance matrices, parametric trading rule simulations with realistic transaction friction, parameter robustness sweeps to detect overfitting, and deterministic market regime classifications."

---

## ⏱️ Step-by-Step Live Demo Flow (6 Minutes)

```text
[0:00 - 0:30]  1. Authentication & Institutional Terminal Gateway
[0:30 - 1:15]  2. Dashboard: Multi-Asset Overview & Normalized Growth
[1:15 - 2:00]  3. Market Analysis: Quantitative Indicator Engine & Underwater Drawdown
[2:00 - 2:45]  4. Correlation Lab: Cross-Asset Covariance & Rolling Correlation Dynamics
[2:45 - 3:45]  5. Strategy Builder: Algorithmic Signal Engine & Execution Markers
[3:45 - 4:45]  6. Backtest Simulator: Portfolio Accounting & Benchmark Teardown
[4:45 - 5:15]  7. Robustness Lab: Hyperparameter Sensitivity Surfaces & Cliff Detection
[5:15 - 5:45]  8. Market Regimes: Dual-State Trend & Volatility Timeline
[5:45 - 6:30]  9. Research Report: Automated Quantitative Teardown & Summary
```

---

### Step 1: Authentication Gateway (`/login`)
- **Action**: Open QuantLab at `http://localhost:5173`. Click **Sign In** or **Email Login**.
- **Talking Points**:
  - Show clean Email/Password authentication backed by FastAPI, SQLite persistence, and secure bcrypt password hashing.
  - Demonstrate instant demo access via **"ENTER AS DEMO ANALYST"** or register a new analyst profile.
  - Protected route guard ensures all terminal capabilities require authentication.

---

### Step 2: Multi-Asset Dashboard (`/dashboard`)
- **Action**: View the primary QuantLab dashboard.
- **Talking Points**:
  - **Asset Coverage**: Real institutional historical data across 3 distinct asset classes — **Gold Spot** (Safe Haven/Precious Metals), **Bitcoin** (High-Beta Digital Asset, 2017 historical series), and **NVIDIA** (High-Growth Mega-Cap Tech).
  - **Live Scorecards**: Instant visibility into annualized volatility, Sharpe ratio, cumulative returns, and maximum drawdown.
  - **Normalized Performance Chart**: Highlight how all assets start from a normalized $1.00 base, making true performance comparison mathematically valid without price-scale distortion.
  - **Pearson Matrix Snapshot & Regime State**: Live correlation matrix and current historical Bull/Bear and Volatility state indicators.

---

### Step 3: Market Analysis & Quantitative Indicators (`/market-analysis`)
- **Action**: Select NVIDIA or Gold. Adjust SMA (Fast: 20) and EMA (Slow: 50) periods. Toggle between Daily Returns and Cumulative Returns.
- **Talking Points**:
  - Point out that **all calculations are performed server-side** by Python/NumPy/Pandas/SciPy (zero mock/client-side formulas).
  - Show the dynamic overlay of Fast SMA vs Slow EMA against historical price action with interactive crosshairs and datazoom.
  - Highlight the **Underwater Drawdown Chart**, showcasing peak-to-trough drop periods and recovery timeframes.

---

### Step 4: Correlation Lab (`/correlation`)
- **Action**: Inspect the full symmetric Pearson correlation matrix heatmap. Select `Gold` vs `Bitcoin` or `Gold` vs `NVIDIA`. Slide rolling window from 30 to 90 days.
- **Talking Points**:
  - Highlight cross-asset diversification dynamics (e.g., Gold's near-zero or negative correlation with equity tech during market shocks).
  - Point out date-alignment handling: Bitcoin's 2017 series is aligned on matching dates with Gold/NVIDIA to prevent observation mismatch.
  - Show the **Unranked Comparative Metrics Table** — strictly adhering to objective academic standards without declaring subjective "winner" assets.

---

### Step 5: Strategy Rule Engine & Signal Builder (`/strategy-builder`)
- **Action**: Choose **SMA Crossover** (20 / 50) or **Mean Reversion** (20-day window, 2% threshold).
- **Talking Points**:
  - QuantLab supports 4 core systematic trading models: SMA Crossover, EMA Trend, Momentum, and Mean Reversion.
  - Point-in-time signal generation: signals generated at market close on Day $t$ are executable at Day $t+1$, completely preventing look-ahead bias.
  - Visual BUY (emerald triangle) and SELL (rose triangle) markers overlaying price action with an event ledger.

---

### Step 6: Portfolio Backtesting Simulator (`/backtesting`)
- **Action**: Set Initial Capital to `$100,000`, Transaction Friction to `0.1%` (10 bps), Risk-Free Rate to `2.0%`. Click **RUN BACKTEST**.
- **Talking Points**:
  - **Realistic Portfolio Accounting**: Simulates trade execution, cash vs equity tracking, transaction slippage/fees, and position sizing.
  - **Equity Curve vs Buy & Hold**: Plots Strategy Equity Curve directly against the Buy & Hold benchmark curve.
  - **Trade Execution Ledger**: Shows filled entry/exit dates, trade duration in days, friction fees paid, net dollar profit, and percentage return.
  - **Open Position Handling**: Explicitly flags if a position remains open at the backtest end date, calculating unrealized P&L without fabricating an exit.

---

### Step 7: Strategy Robustness Lab (`/robustness`)
- **Action**: Execute a multi-parameter Cartesian sweep across fast/slow SMA grids (e.g. Fast: 10, 20, 30; Slow: 40, 50, 100) and friction steps (0%, 0.1%, 0.2%).
- **Talking Points**:
  - Overfitting is the #1 failure in quantitative trading. The Robustness Lab tests parameter stability.
  - Shows 2D sensitivity heatmaps: smooth performance surfaces indicate robust strategy rules, while isolated spikes reveal dangerous "parameter cliffs".
  - Enforces `MAX_CONFIGURATIONS = 100` safety limit.

---

### Step 8: Market Regime Analysis (`/market-regimes`)
- **Action**: View the multi-band Regime Timeline. Toggle between `historical_descriptive` and `expanding_threshold` modes.
- **Talking Points**:
  - Classifies market states into 4 distinct regimes: Bull/Low-Vol, Bull/High-Vol, Bear/Low-Vol, and Bear/High-Vol.
  - Explain the difference between retrospective full-sample classification (`historical_descriptive`) and causal point-in-time classification (`expanding_threshold` with zero look-ahead bias).
  - Displays empirical segment statistics (average daily returns, Sharpe, drawdown per regime) and chronological transition logs.

---

### Step 9: Research Report (`/research-report`)
- **Action**: Switch to the Research Report view and demonstrate print/PDF readiness.
- **Talking Points**:
  - Compiles an executive institutional summary combining risk metrics, correlation matrices, backtest equity results, and regime statistics.
  - Uses neutral, rigorous quantitative terminology with institutional disclaimers.

---

## 🏆 Key Takeaways for Judges
1. **Zero Fake / Mock Data**: Real processed Kaggle financial datasets for Gold, Bitcoin, and NVIDIA.
2. **Pure Architectural Integrity**: Complete separation of concerns (React frontend presentation $\leftrightarrow$ FastAPI REST API $\leftrightarrow$ Python analytics engine $\leftrightarrow$ Normalized data layer).
3. **Institutional Rigor**: Full transaction friction simulation, point-in-time execution, look-ahead bias protection, sensitivity testing, and regime classification.
4. **Production Quality**: 197 automated tests passing, clean TypeScript builds, and zero console errors.
