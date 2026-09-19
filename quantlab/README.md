# QuantLab: Quantitative Research & Backtesting Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_+_Vite-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-blue.svg)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)

**QuantLab** is an institutional-grade quantitative finance platform engineered for data-driven alpha generation, multi-asset technical analysis, strategy backtesting, cross-asset correlation modeling, market regime detection, and Monte Carlo robustness analytics.

---

## Key Features

1. **Multi-Asset Market Terminal**
   - Interactive candlestick charts with dynamic overlays (SMA, EMA, Bollinger Bands, RSI, MACD, ATR, Stochastic).
   - High-precision time-series data for Equities (NVIDIA), Digital Assets (Bitcoin), and Commodities (Gold).

2. **Cross-Asset Correlation Lab**
   - Real-time Pearson and Spearman NxN correlation matrices.
   - Rolling correlation time series (30d, 60d, 90d) to spot macro structural regime shifts and market decoupling.
   - Spread and cointegration tracking for statistical arbitrage and pair trading.

3. **Algorithmic Strategy Builder & Engine**
   - Visual and rule-based strategy configurator.
   - Pre-built quant models: Dual SMA Crossover, EMA Trend Ribbon, Momentum Breakout, and Mean Reversion (RSI + Bollinger Bands).
   - Realistic execution simulation: fractional position sizing, slippage modeling, commission fee schedules, and stop-loss/take-profit order management.

4. **Institutional Tear Sheets & Performance Analytics**
   - Real-time computation of Sharpe Ratio, Sortino Ratio, Calmar Ratio, Maximum Drawdown, Value at Risk (VaR 95/99), Expected Shortfall (CVaR), and Beta/Alpha vs Benchmark.
   - Underwater drawdown visualization and recovery phase diagnostics.

5. **Robustness & Regime Detection Lab**
   - 1,000+ run Monte Carlo equity curve resampling.
   - Walk-forward optimization and parameter sensitivity matrix.
   - Volatility & trend Hidden Markov / Clustering regime detection (Bull Trend, Bear Trend, Choppy/High Volatility, Mean-Reverting Consolidation).

6. **Automated Institutional Research Reports**
   - PDF/HTML exportable quant tear sheets with executive summaries, risk breakdowns, and trade log statistics.

---

## Platform Architecture

```
quantlab/
├── frontend/             # React 18, Vite, TypeScript, Glassmorphism UI, Lucide
├── backend/              # FastAPI, NumPy, Pandas, SciPy, SQLAlchemy, SQLite
├── datasets/             # Raw & Processed Multi-Asset Daily Datasets (Gold, BTC, NVDA)
├── scripts/              # ETL Pipelines & Database Seeders
└── docs/                 # Architectural & Methodology Documentation
```

---

## Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm 9+**
- (Optional) **Docker & Docker Compose**

### Running with Docker Compose
```bash
cd quantlab
docker-compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`

### Manual Setup

#### 1. Backend Setup
```bash
cd quantlab/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd quantlab/frontend
npm install
npm run dev
```

#### 3. Data Ingestion & Seed Scripts
```bash
cd quantlab/scripts
python download_data.py
python clean_data.py
python normalize_data.py
python seed_database.py
```

---

## License
MIT License. See [LICENSE](LICENSE) for details.
