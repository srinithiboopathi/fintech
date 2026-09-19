# QUANTLAB

**Quantitative Multi-Asset Financial Intelligence & Backtesting Platform**

QUANTLAB is a full-stack institutional-grade quantitative finance platform designed to analyze historical market data, compute multi-asset performance and statistical indicators, explore cross-asset correlation dynamics, and backtest quantitative trading strategies with realistic transaction costs and portfolio simulation.

---

## 🚀 Key Platform Features

- **Multi-Asset Intelligence**: Comprehensive analytics across Gold, Bitcoin, and NVIDIA.
- **Quantitative Engine**: Moving averages (SMA/EMA), daily & cumulative returns, historical & annualized volatility, Sharpe ratio, max drawdown, and rolling metrics.
- **Cross-Asset Correlation Lab**: Multi-asset covariance, correlation matrices, and rolling correlation windows.
- **Strategy & Backtesting Engine**:
  - SMA Crossover
  - EMA Trend
  - Momentum Strategies
  - Mean Reversion
  - Portfolio Backtesting with transaction costs and slippage simulation
  - Buy-and-Hold Benchmark comparison
- **Institutional Research & Diagnostics**:
  - Robustness analysis (parameter sensitivity, monte carlo)
  - Market regime analysis (volatility & trend regimes)
  - Research report generation

---

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Apache ECharts, Zustand, React Router, Axios, React Hook Form, Zod
- **Backend**: Python 3.11+, FastAPI, Pandas, NumPy, SciPy, SQLAlchemy, PostgreSQL
- **Architecture**: Strict Separation of Concerns (Frontend Presentation $\leftrightarrow$ FastAPI REST API $\leftrightarrow$ Python Quantitative Analytics Engine $\leftrightarrow$ Normalized Data Layer)

---

## 📁 Repository Structure

```text
quantlab/
├── frontend/               # React + TypeScript + Vite + Tailwind frontend
│   ├── src/
│   │   ├── api/            # Centralized API modules (market, quant, correlation, strategy, backtesting, robustness, regime)
│   │   ├── components/     # UI primitives & Apache ECharts visualization components
│   │   ├── lib/            # Central Axios API client with error handling
│   │   ├── pages/          # 10 Institutional quantitative terminal views
│   │   ├── store/          # Zustand global application state
│   │   └── types/          # Full TypeScript schemas matching FastAPI models
├── backend/                # FastAPI + Pandas + NumPy + SciPy backend
│   ├── app/
│   │   ├── api/            # REST API routers
│   │   ├── backtesting/    # Portfolio simulation & execution engine
│   │   ├── correlation/    # Cross-asset covariance & correlation engine
│   │   ├── quant/          # Moving averages, returns, volatility & risk analytics
│   │   ├── regimes/        # Market regime classification & statistics
│   │   ├── robustness/     # Multi-parameter sensitivity sweep engine
│   │   ├── schemas/        # Pydantic v2 data models
│   │   ├── services/       # Service orchestration layer
│   │   └── strategies/     # Quantitative strategy rules & signal generation
├── datasets/               # Market data storage
│   ├── raw/                # Unmodified historical datasets (Gold, Bitcoin, NVIDIA)
│   └── processed/          # Normalized time-series datasets
├── scripts/                # Data pipelines and utility scripts
└── docs/                   # Comprehensive project architecture & quant documentation
```

---

## 🚦 Quick Start

### 1. Environment Setup

Copy example environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Frontend Environment (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Backend Startup
```bash
# From repository root
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix:
source venv/bin/activate

pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```
- API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 3. Frontend Startup
```bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
Frontend Terminal UI will be accessible at `http://localhost:5173`.

---

## 🧭 QuantLab Dashboard Routes

| Route | View | Description |
| :--- | :--- | :--- |
| `/` | **Landing Page** | Institutional overview, methodology primer, system architecture. |
| `/login` | **MAID Terminal Gateway** | Secure institutional gateway interface. |
| `/dashboard` | **Terminal Overview** | Multi-asset scorecard, normalized performance, Pearson matrix heatmap, live regime state. |
| `/market-analysis` | **Market Analysis** | Price & Moving Averages (SMA/EMA), daily vs cumulative returns, underwater drawdown curves. |
| `/correlation` | **Correlation Lab** | Interactive cross-asset correlation matrix, pairwise metrics, rolling window dynamics, aligned comparative tables. |
| `/strategy-builder` | **Strategy Builder** | Signal generation for SMA, EMA, Momentum & Mean Reversion with BUY/SELL chart overlays. |
| `/backtesting` | **Backtest Simulator** | Institutional portfolio simulation, equity curve vs Buy & Hold benchmark, friction costs, drawdown, trade log. |
| `/trade-history` | **Trade Execution Ledger** | Session trade history, win/loss breakdown, holding period analysis, open position tracking. |
| `/robustness` | **Robustness Lab** | Cartesian hyperparameter sensitivity sweeps, 2D stability heatmaps, friction testing, unranked tables. |
| `/market-regimes` | **Market Regimes** | Bull/Bear trend & High/Low volatility classification timeline, descriptive segment statistics, state transitions. |
| `/research-report` | **Research Report** | Exportable quantitative summary teardown across risk, strategies, regimes, and correlation dynamics. |

---

## 📖 Documentation

- [Architecture Guide](file:///docs/architecture.md)
- [API Reference](file:///docs/api.md)
- [Data Dictionary](file:///docs/data-dictionary.md)
- [Backtesting Methodology](file:///docs/backtesting-methodology.md)
- [Robustness Methodology](file:///docs/robustness-methodology.md)
- [Regime Methodology](file:///docs/regime-methodology.md)
- [Project Progress & Phase Log](file:///docs/PROJECT_PROGRESS.md)
- [Developer & Agent Rules](file:///AGENTS.md)
