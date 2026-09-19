# Agent Development Guidelines & Rules of Engagement

This document defines the strict operating constraints, engineering standards, and architectural rules for all AI agents and developers contributing to the **Quantexa** quantitative platform.

---

## 1. Zero Fake Market Data
- **Rule**: Never use random, simulated, hardcoded, or mock price time series in production logic or production API responses.
- **Enforcement**: All market data must be ingested from verified real-world financial providers (Twelve Data / Alpha Vantage). If external providers are inaccessible and no valid cache exists, return an explicit error (`HTTP 502/504`) rather than generating synthetic quotes.

## 2. API Key Security & Secrets Protection
- **Rule**: Never expose, hardcode, or print API keys in source code, logs, commit messages, or terminal outputs.
- **Enforcement**:
  - Always load credentials dynamically from environment variables or `.env`.
  - Always mask keys in API responses and console logs (e.g. `settings.masked_twelve_data_key`).
  - Keep `backend/.env` strictly ignored by version control. Never commit `.env` or files containing secrets.

## 3. Provider Hierarchy & Resilient Ingestion
- **Primary Provider**: **Twelve Data** (`twelve_data`).
- **Fallback Provider**: **Alpha Vantage** (`alpha_vantage`).
- **Enforcement**: Requests must always query Twelve Data first. Alpha Vantage is invoked only when Twelve Data encounters rate limits (HTTP 429), timeouts, or server errors. Both providers must be normalized to standard internal schemas.

## 4. Preserve API Backwards Compatibility
- **Rule**: Existing endpoints, route signatures, schema fields, and query parameter contracts must NEVER be broken or altered.
- **Enforcement**: All existing endpoints (`/health`, `/assets`, `/market/{asset}/historical`, `/market/{asset}/latest`, `/market/{asset}/data`, `/market/{asset}/data/summary`, `/market/{asset}/indicators`, `/market/{asset}/risk-metrics`) must continue to function predictably.

## 5. Automated Verification Before Any Commit
- **Rule**: Never commit or push code without running the full automated test suite.
- **Enforcement**: Run `pytest backend/tests` and confirm 100% pass rate before requesting a commit or completing a milestone.

## 6. Strict Step-by-Step Scope Discipline
- **Rule**: Implement ONLY the currently assigned milestone.
- **Enforcement**: Do not implement future steps (e.g., Sharpe ratio, maximum drawdown, portfolio correlation, or backtesting) ahead of time. Keep upcoming steps marked as `NOT STARTED` until explicitly instructed.

## 7. Caching & Quota Conservation
- **Rule**: Avoid redundant external API calls.
- **Enforcement**:
  - Respect `CacheManager` TTL policies (24 hours for historical daily bars, 60 seconds for latest quotes).
  - Derived datasets (clean data, indicators, risk metrics) must reuse local caches whenever available.

## 8. Quantitative Integrity & Zero Look-Ahead Bias
- **Rule**: Causal temporal integrity is non-negotiable.
- **Enforcement**: At any time step $t$, calculations must access only observations at indices $i \le t$. Never slice forward in time. Ensure input data is strictly sorted ascending by UTC timestamp.

## 9. Data Hygiene & Asset Semantics
- **Rule**: Enforce financial validity rules across all asset classes.
- **Enforcement**:
  - Deduplicate timestamps and convert all timestamps to ISO-8601 UTC format.
  - Reject non-numeric, zero, or negative prices.
  - Validate OHLC boundaries ($\text{Low} \le \text{Open}, \text{Close} \le \text{High}$).
  - Preserve legitimate `null` volume for spot crypto (`BTC/USD`) and spot gold bullion (`XAU/USD`). Do not coerce `null` volume to zero.
