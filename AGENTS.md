# AGENTS.md - QUANTLAB Engineering & Architectural Rules

This document outlines mandatory guidelines for all AI agents and engineers working on the **QUANTLAB** platform.

---

## 1. Branch & Git Discipline

- **Current Working Branch**: `feature/quantlab-platform`
- **Never Modify Main Directly**: All development happens strictly on feature branches.
- **No Force Pushes / Resets**: `git reset --hard`, `git push --force`, or deleting branches is strictly prohibited.
- **Developer Review Before Commit**: Do NOT automatically commit or push code. Changes must be verified, presented, and reviewed before the developer manually commits/pushes.

---

## 2. Phase-by-Phase Development Lifecycle

- Development proceeds strictly **ONE PHASE AT A TIME**.
- Never jump ahead to future phases or pre-implement future features unless strictly required as a dependency.
- Update `docs/PROJECT_PROGRESS.md` at the conclusion of every phase.
- Always wait for developer confirmation before initiating the next phase.

---

## 3. Architecture & Separation of Concerns

```text
React Frontend (UI/UX, Charts, Routing, State)
      ↓ REST API
FastAPI Backend (Authentication, Endpoints, Serialization)
      ↓ Service Layer
Quantitative Engines (Calculations, Indicators, Correlations, Strategies, Backtests)
      ↓ Storage Layer
Normalized Historical Data / PostgreSQL
```

- **Frontend Responsibility**: Presentation, responsive layouts, forms, filters, chart rendering (Apache ECharts), and API communication.
- **Backend Responsibility**: Data ingestion, normalization, quantitative indicators, statistical models, correlation matrices, strategy signal generation, portfolio backtesting, and robustness testing.
- **Strict Rule**: The frontend must **NEVER** perform core financial calculations. All mathematical/financial computation belongs exclusively in the Python backend.

---

## 4. Financial Integrity & Data Rigor

- **No Fake Data**: Never invent financial data or synthetic prices. All analysis must run on actual historical data.
- **No Look-Ahead Bias**: Historical indicators and signals at time $t$ must only use information available up to time $t$.
- **No Data Leakage**: Training/optimization sets (if used) must remain strictly isolated from testing periods.
- **Raw Data Immutability**: Datasets in `datasets/raw/` must NEVER be modified or overwritten. Normalization outputs are stored in `datasets/processed/`.
- **Realistic Backtesting**:
  - Backtests must simulate actual portfolio cash and equity curves over time.
  - Realistic transaction costs (commission, spread/slippage) must be incorporated into backtesting computations.
  - Historical performance is never presented as a guarantee of future performance.

---

## 5. Technology Stack Standards

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui patterns, Apache ECharts, Zustand, React Router, Axios, React Hook Form, Zod.
- **Backend**: Python 3.11+, FastAPI, Pydantic, Pandas, NumPy, SciPy, SQLAlchemy, PostgreSQL.
- **Prohibitions**: No Node.js backend; no microservices architecture; no unnecessary third-party services.
