# QUANTLAB Architecture & System Design

## 1. High-Level Architecture

QUANTLAB is structured as a decoupled multi-tier quantitative analytics platform:

```
+-------------------------------------------------------------------------+
|                         React Client Application                         |
|  - React 18, TypeScript, Vite                                           |
|  - Apache ECharts Time-Series Visualizations                            |
|  - Zustand State Management                                             |
|  - Tailwind CSS Institutional Terminal UI                               |
+-------------------------------------------------------------------------+
                                    │  HTTP / REST (JSON)
                                    ▼
+-------------------------------------------------------------------------+
|                            FastAPI REST API                             |
|  - Request Validation (Pydantic schemas)                                |
|  - Endpoint Routing & Middleware (CORS, Error Handling)                |
|  - Response Serialization                                               |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                        Quantitative Core Engines                        |
|  - Indicator Engine (SMA, EMA, Returns, Volatility, Sharpe, Drawdown)   |
|  - Correlation Engine (Covariance, Pearson matrices, Rolling windows)  |
|  - Strategy Engine (SMA Crossover, EMA Trend, Momentum, Mean Reversion) |
|  - Backtesting Engine (Portfolio simulation, Slippage, Fees, Equity)    |
|  - Robustness & Regime Engine (Monte Carlo, Parameter Sensitivity)      |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                           Data & Storage Tier                           |
|  - Processed Normalized Parquet / CSV Datasets                          |
|  - PostgreSQL Database (Historical Storage & Strategy Records)          |
+-------------------------------------------------------------------------+
```

## 2. Directory Structure

```text
quantlab/
├── frontend/
│   ├── src/
│   │   ├── components/       # UI building blocks & Terminal panels
│   │   ├── lib/              # API clients and utility functions
│   │   ├── store/            # Zustand global state slices
│   │   ├── types/            # TypeScript domain and financial types
│   │   ├── App.tsx           # Route definitions and layout
│   │   ├── main.tsx          # React application root
│   │   └── index.css         # Global institutional design system
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints and routers
│   │   ├── core/             # Configuration and environment settings
│   │   ├── engine/           # Quantitative calculation modules (Phases 4+)
│   │   ├── models/           # Pydantic schemas & SQLAlchemy models
│   │   ├── services/         # Data loading and business logic
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # Automated pytest suite
│   └── requirements.txt
├── datasets/
│   ├── raw/                  # Immutable Kaggle raw datasets (Gold, BTC, NVDA)
│   └── processed/            # Cleaned, standardized time-series datasets
├── scripts/                  # Data ingestion & normalization scripts
└── docs/                     # Documentation and project progress
```

## 3. Communication Protocols

- **RESTful Endpoints**: Versioned under `/api/v1/`
- **JSON Serialization**: High-precision numerical arrays and time-series records.
- **Stateless Quantitative API**: Backend services receive analysis parameters (asset, date window, indicator parameters, transaction fee rates) and compute results deterministically.
