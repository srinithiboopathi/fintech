# QUANTLAB API Specification

This document defines the REST API surface for QUANTLAB.

## Base URL
- Development: `http://localhost:8000/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Redoc Reference: `http://localhost:8000/redoc`

---

## 1. System & Health

### `GET /health` / `GET /api/v1/health`
Checks server operational readiness.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "app_name": "QUANTLAB API",
  "environment": "development"
}
```

---

## 2. Upcoming Endpoints (Scheduled by Phase)

| Endpoint | Method | Phase | Description |
|---|---|---|---|
| `/api/v1/market/assets` | GET | Phase 3 | List supported multi-assets and available date ranges |
| `/api/v1/market/history` | GET | Phase 3 | Fetch historical OHLCV data for an asset |
| `/api/v1/quant/indicators` | POST | Phase 4 | Calculate SMA, EMA, Volatility, Sharpe, Drawdown |
| `/api/v1/quant/correlation` | POST | Phase 6 | Compute correlation matrices and rolling correlation |
| `/api/v1/strategy/signals` | POST | Phase 7 | Generate trading signals for configured strategy |
| `/api/v1/backtest/run` | POST | Phase 8 | Run portfolio backtest with transaction costs |
| `/api/v1/robustness/monte-carlo` | POST | Phase 11 | Parameter sensitivity & Monte Carlo simulations |
| `/api/v1/regime/detect` | POST | Phase 12 | Classify market volatility and trend regimes |
| `/api/v1/report/generate` | POST | Phase 13 | Generate downloadable research teardown report |
