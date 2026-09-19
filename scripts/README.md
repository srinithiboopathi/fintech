# Scripts Directory

This directory is reserved for **reusable, project-level operational and automation scripts**.

---

## Intended Purpose

The `scripts/` directory is designed for cross-cutting, repository-level utilities, including:
- Developer environment bootstrapping and onboarding scripts
- Database setup and migration tooling (when applicable in future steps)
- CI/CD pipeline automation and repository health checks
- Production deployment or container preparation scripts

---

## Backend-Specific Tests & Verification Scripts

> [!NOTE]
> **Notice on Backend Internal Scripts:**
> Backend unit tests, integration tests, and live endpoint verification scripts are located directly inside:
> ```
> backend/tests/
> ```
> These scripts rely directly on internal backend packages (`app.services`, `app.models`, `app.config`). Keeping them inside `backend/tests/` maintains modularity and ensures proper test discovery with `pytest`.

### Key Verification Scripts in `backend/tests/`:
- `pytest backend/tests` — Comprehensive automated test suite (53 tests covering Steps 1–5).
- `python backend/tests/verify_step2_live.py` — Live validation of Twelve Data ingestion, fallback, and caching.
- `python backend/tests/verify_step3_live.py` — Live validation of data cleaning and quality summaries.
- `python backend/tests/verify_step4_live.py` — Live validation of SMA and EMA quantitative indicators.
- `python backend/tests/verify_step5_live.py` — Live validation of percentage returns and rolling volatility.
