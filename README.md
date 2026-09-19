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
├── backend/                # FastAPI + Pandas + NumPy + SciPy backend
├── datasets/               # Market data storage
│   ├── raw/                # Unmodified Kaggle datasets (Gold, Bitcoin, NVIDIA)
│   └── processed/          # Normalized time-series datasets
├── scripts/                # Data pipelines and utility scripts
└── docs/                   # Comprehensive project architecture & quant documentation
```

---

## 🚦 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend will be accessible at `http://localhost:5173`.

---

## 📖 Documentation

- [Architecture Guide](file:///docs/architecture.md)
- [API Reference](file:///docs/api.md)
- [Data Dictionary](file:///docs/data-dictionary.md)
- [Backtesting Methodology](file:///docs/backtesting-methodology.md)
- [Hackathon Demo Guide](file:///docs/hackathon-demo.md)
- [Project Progress & Phase Log](file:///docs/PROJECT_PROGRESS.md)
- [Developer & Agent Rules](file:///AGENTS.md)
