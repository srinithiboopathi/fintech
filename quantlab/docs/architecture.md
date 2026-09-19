# QuantLab Architecture & System Design

## 1. Executive Overview

QuantLab is a high-performance quantitative analytics and algorithmic backtesting platform designed for quantitative traders, portfolio managers, and fintech researchers. The platform bridges the gap between exploratory data analysis, systematic strategy modeling, and institutional risk management.

```
+-------------------------------------------------------------------------------+
|                             QuantLab Frontend                                |
|  [React 18 + Vite + TypeScript + Glassmorphism UI + Custom Dark Design]       |
|                                                                               |
|  - Multi-Asset Terminal      - Correlation Lab         - Strategy Builder     |
|  - Interactive Charts        - Regime Detection Radar  - Tear Sheet Exporter  |
|  - Robustness & Monte Carlo  - Trade Execution History - Dashboard KPI Grid   |
+---------------------------------------+---------------------------------------+
                                        | REST / JSON
                                        v
+-------------------------------------------------------------------------------+
|                             QuantLab Backend                                 |
|                         [FastAPI + Python 3.10+]                              |
|                                                                               |
|  +---------------------+   +-----------------------+   +-------------------+  |
|  |     API Routers     |   |   Quantitative Engine |   |  Backtest Engine  |  |
|  | - Auth & Sessions   |   | - Technical Indicators|   | - Bar-by-bar sim  |  |
|  | - Market & OHLCV    |   | - Sharpe / Sortino    |   | - Order execution |  |
|  | - Correlation Lab   |   | - Volatility & VaR    |   | - Position sizing |  |
|  | - Backtest Service  |   | - Drawdown & Duration |   | - Slippage & Fees |  |
|  | - Regime & Reports  |   | - Rolling Metrics     |   | - PnL attribution |  |
|  +---------------------+   +-----------------------+   +-------------------+  |
|                                                                               |
|  +---------------------+   +-----------------------+   +-------------------+  |
|  |   Data Providers    |   |   Analysis & Regimes  |   | Database Models   |  |
|  | - CSV File Provider |   | - Regime Detection    |   | - SQLite ORM      |  |
|  | - Yahoo/Stooq Fetch |   | - Monte Carlo Engine  |   | - Repositories    |  |
|  | - Validator & Clean |   | - Parameter Heatmaps  |   | - Pydantic DTOs   |  |
|  +---------------------+   +-----------------------+   +-------------------+  |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                             Data & Storage Tier                               |
|  - Raw Market CSVs (Gold, Bitcoin, Nvidia)                                    |
|  - Cleaned & Normalized Continuous Time-Series Matrices                       |
|  - SQLite Database (User profiles, strategies, backtest runs, trade logs)     |
+-------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### A. Quantitative Engine (`app/quant/`)
1. **Technical Indicators**: Vectorized calculations using NumPy/Pandas for SMA, EMA, MACD (12, 26, 9), Bollinger Bands (20, 2σ), RSI (14), ATR (14), Stochastic Oscillator (%K, %D), and VWAP.
2. **Return & Risk Computation**:
   - Compounded Annual Growth Rate (CAGR)
   - Annualized Volatility ($\sigma_{ann} = \sigma_{daily} \times \sqrt{252}$)
   - Sharpe Ratio ($S = \frac{R_p - R_f}{\sigma_p}$)
   - Sortino Ratio ($Sortino = \frac{R_p - R_f}{\sigma_{downside}}$)
   - Calmar Ratio ($Calmar = \frac{CAGR}{|MaxDD|}$)
   - Value at Risk (Historical & Parametric VaR at 95% and 99% confidence)
   - Conditional Value at Risk (Expected Shortfall / CVaR)
3. **Drawdown Metrics**: High-water mark tracking, peak-to-trough calculation, drawdown duration, and recovery time tracking.

### B. Event-Driven & Vectorized Backtester (`app/backtesting/`)
- **Execution Modeling**: Supports Market and Limit orders with fill prices adjusted for custom slippage (basis points or percentage) and exchange commissions.
- **Position Sizing**:
  - Fixed dollar amount
  - Percentage of total portfolio equity
  - Volatility-targeted risk parity
  - Kelly Criterion fractional sizing
- **Risk Safeguards**: Built-in dynamic Stop Loss (%) and Take Profit (%) triggers checked bar-by-bar.

### C. Cross-Asset Correlation Lab (`app/correlation/`)
- Multi-asset Pearson ($r$) and Spearman rank correlation computation.
- Rolling window (30-day, 60-day, 90-day) correlation time series to detect macro decoupling between traditional safe havens (Gold), speculative tech equities (NVIDIA), and digital store-of-value (Bitcoin).

### D. Market Regime Detection & Robustness (`app/analysis/`)
- **Regime Classification**: 4-state market regime classifier combining trend momentum (200-day EMA slope) and realized rolling volatility into:
  - *State 1: Bullish Trend (Low/Moderate Volatility)*
  - *State 2: Bearish Trend (High Volatility)*
  - *State 3: Volatile Choppy (Mean-Reverting High Volatility)*
  - *State 4: Consolidation (Low Volatility Sideways Range)*
- **Monte Carlo Robustness Testing**: 1,000 synthetic return trajectories generated via bootstrap sampling to determine probability distribution of maximum drawdown, terminal wealth, and Sharpe ratio confidence intervals.

---

## 3. Frontend Architecture

- **React 18 + TypeScript**: Strict type safety across all quant schemas, DTOs, and component props.
- **State Management**: Lightweight, decoupled state using Zustand stores (`authStore`, `marketStore`, `backtestStore`).
- **Data Visualization**:
  - Interactive candlestick chart engine with multi-timeframe navigation.
  - Multi-indicator sub-charts with synchronized crosshair cursor.
  - Underwater drawdown & equity growth comparison curves.
  - Interactive heatmaps with hover data inspection.
- **Design System**: Tailored dark-mode glassmorphism styling (`#0a0e17` deep space canvas, `#10192d` card surfaces, `#00f5a0` neon emerald, `#00d8ff` electric cyan, `#9d4edd` violet accents).
