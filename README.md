# QUANTLAB

**Quantitative Multi-Asset Financial Intelligence & Backtesting Platform**

QUANTLAB is a full-stack institutional-grade quantitative finance platform designed to analyze historical market data, compute multi-asset performance and statistical indicators, explore cross-asset correlation dynamics, and backtest quantitative trading strategies with realistic transaction costs and portfolio simulation.

---

## 🚀 Key Platform Features

- **Multi-Asset Intelligence**: Comprehensive analytics across Gold, Bitcoin, and NVIDIA.
- **Quantitative Engine**: Moving averages (SMA/EMA), daily & cumulative returns, historical & annualized volatility, Sharpe ratio, max drawdown, and rolling metrics.
- **Cross-Asset Correlation Lab**: Multi-asset covariance, correlation matrices, and rolling correlation windows.
- **Advanced Portfolio Analytics (Phase 11)**:
  - Custom multi-asset portfolio construction across Gold, Bitcoin, and NVIDIA
  - Calendar date synchronization and daily return aggregation ($r_{p,t} = \sum w_i r_{i,t}$)
  - Compounded equity curve growth ($V_t = V_0(1+C_{p,t})$)
  - Institutional performance metrics (CAGR, Annualized Volatility, Sharpe, Max Drawdown)
  - Standalone and weighted performance contribution decomposition ($w_i \times R_i$)
  - Euler risk decomposition via annualized covariance matrix ($\mathbf{\Sigma} = 252 \times \mathbf{\Sigma}_{\text{daily}}$, Marginal & Component Risk Contributions $\text{CCR}_i$, Percentage Risk $\% \text{CR}_i$)
  - Normalized Base-100 comparative performance curves
- **Portfolio Optimization & Efficient Frontier (Phase 12)**:
  - Constrained Markowitz Modern Portfolio Theory (MPT) optimization engine using SciPy SLSQP
  - Global Minimum Variance (GMV) portfolio solving ($\min \mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$)
  - Maximum Sharpe Ratio (Tangency) portfolio solving ($\max (\mu_p - r_f) / \sigma_p$)
  - 1/N Equal-Weight benchmark portfolio evaluation with constraint feasibility checks
  - Markowitz Efficient Frontier continuous curve generation via target-return sweeps
  - Deterministic random feasible portfolio sampling on the constrained simplex for cloud scatter visualization (5,000+ points, seed 42)
  - Interactive Apache ECharts Efficient Frontier visualization with risk/return coordinates and allocation tooltips
  - Descriptive, non-ranking comparative matrix across strategy configurations
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

## 🔐 Authentication & Session Access

QuantLab includes a functional email/password authentication system built on FastAPI, SQLite persistence, bcrypt password hashing, and JWT Bearer tokens.

### Creating an Account & Logging In
1. Navigate to `/login` (or click **Email Login** / **Enter QuantLab** on the landing page).
2. To create a new account: Select **Create Account**, enter your email, password (min 6 characters), and optional name, then click **Create Account →**.
3. To sign in: Select **Sign In**, enter your registered email and password, then click **Continue →**.
4. **Demo Analyst Mode**: For immediate evaluation, click **ENTER AS DEMO ANALYST** to instantly launch an authenticated evaluation session without registration.
5. **Session Persistence**: JWT access tokens are securely managed in `localStorage`. Page refreshes maintain authentication, and the **Logout** button on the top bar cleanly clears credentials.

---

## 🧭 QuantLab Dashboard Routes

| Route | View | Description | Access |
| :--- | :--- | :--- | :--- |
| `/` | **Landing Page** | Institutional overview, methodology primer, system architecture. | Public |
| `/login` | **Email Login & Gateway** | Secure email/password login, account registration, and demo access. | Public |
| `/dashboard` | **Terminal Overview** | Multi-asset scorecard, normalized performance, Pearson matrix heatmap, live regime state. | Protected |
| `/market-analysis` | **Market Analysis** | Price & Moving Averages (SMA/EMA), daily vs cumulative returns, underwater drawdown curves. | Protected |
| `/correlation` | **Correlation Lab** | Interactive cross-asset correlation matrix, pairwise metrics, rolling window dynamics, aligned comparative tables. | Protected |
| `/strategy-builder` | **Strategy Builder** | Signal generation for SMA, EMA, Momentum & Mean Reversion with BUY/SELL chart overlays. | Protected |
| `/backtesting` | **Backtest Simulator** | Institutional portfolio simulation, equity curve vs Buy & Hold benchmark, friction costs, drawdown, trade log. | Protected |
| `/trade-history` | **Trade Execution Ledger** | Session trade history, win/loss breakdown, holding period analysis, open position tracking. | Protected |
| `/robustness` | **Robustness Lab** | Cartesian hyperparameter sensitivity sweeps, 2D stability heatmaps, friction testing, unranked tables. | Protected |
| `/market-regimes` | **Market Regimes** | Bull/Bear trend & High/Low volatility classification timeline, descriptive segment statistics, state transitions. | Protected |
| `/research-report` | **Research Report** | Exportable quantitative summary teardown across risk, strategies, regimes, and correlation dynamics. | Protected |

---

## 📊 Dataset Coverage & Important Notes

- **Gold Spot (`datasets/processed/gold_daily.csv`)**: Historical daily prices from 2013-01-02 to 2024-12-31.
- **Bitcoin (`datasets/processed/bitcoin_daily.csv`)**: Historical daily prices covering the 2017 market cycle (**2017-01-01 to 2017-12-31**).
  > [!NOTE]
  > Bitcoin's historical dataset covers the 2017 calendar year. QuantLab automatically handles date alignment for cross-asset comparisons and correlation without forward-filling or fabricating synthetic data.
- **NVIDIA (`datasets/processed/nvidia_daily.csv`)**: Historical daily prices from 2013-01-02 to 2024-12-31.
- **Combined Market Data (`datasets/processed/market_data.csv`)**: Aligned multi-asset time series.

---

## ⚖️ Quantitative Methodology & Disclaimers

- **Zero Look-Ahead Bias**: Quantitative indicators, moving averages, and strategy signals at time $t$ use only information available up to market close on date $t$. Backtest orders execute at date $t+1$.
- **Friction Realism**: Portfolio backtesting simulates transaction friction (slippage + commissions) per trade execution.
- **Descriptive Sensitivity**: Robustness parameter sweeps display empirical metric surfaces without ranking subjective "winner" strategies.
- **Disclaimer**: *Historical performance does not guarantee future results. QuantLab is designed strictly for research, simulation, and analytical exploration.*

---

## 📖 Documentation

- [Hackathon Judge Demo Script (5–8 Min)](file:///docs/demo-script.md)
- [Hackathon Readiness Checklist](file:///docs/hackathon-checklist.md)
- [Architecture Guide](file:///docs/architecture.md)
- [API Reference](file:///docs/api.md)
- [Data Dictionary](file:///docs/data-dictionary.md)
- [Backtesting Methodology](file:///docs/backtesting-methodology.md)
- [Robustness Methodology](file:///docs/robustness-methodology.md)
- [Regime Methodology](file:///docs/regime-methodology.md)
- [Project Progress & Phase Log](file:///docs/PROJECT_PROGRESS.md)
- [Developer & Agent Rules](file:///AGENTS.md)
