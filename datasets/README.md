# Datasets Directory

This directory is reserved for offline, exported, and benchmark quantitative datasets used across the **Quantexa** platform.

---

## Directory Purpose

- **Processed Datasets**: Cleaned, validated, and normalized multi-asset market datasets exported for quantitative research or offline reproducibility.
- **Exported Analysis Datasets**: Analytical outputs, such as rolling volatility matrices, computed technical indicators, or historical return series.
- **Optional Offline Datasets**: Pre-cached historical snapshots for testing in isolated or rate-limited environments.

---

## Important Security & Data Integrity Rules

> [!CAUTION]
> **Strict Rules for Datasets:**
> 1. **Do NOT store API keys or secrets** anywhere in this directory or in exported files.
> 2. **Do NOT commit raw API responses or large cache dumps** to Git.
> 3. **Do NOT use fake or randomly generated market data.** All datasets must originate from real market data ingested through verified providers (Twelve Data / Alpha Vantage).
> 4. Automated runtime cache files belong in `backend/data/cache/` (which is `.gitignore`d), not in this directory.

---

## Supported Asset Coverage

When exporting datasets, ensure records follow the standard schema for the supported asset universe:

| Asset | Symbol | Asset Class | Primary Identifier |
| :--- | :--- | :--- | :--- |
| **NVIDIA Corporation** | `NVDA` | Equity | `nvidia` |
| **Bitcoin USD** | `BTC/USD` | Cryptocurrency | `bitcoin` |
| **Gold Spot Bullion** | `XAU/USD` | Commodity / Forex | `gold` |

---

## Standard Clean Schema

Exported dataset files must follow the normalized Step 3 schema:

```json
{
  "timestamp": "2026-03-13T00:00:00Z",
  "open": 120.45,
  "high": 122.80,
  "low": 119.30,
  "close": 121.50,
  "volume": 45200000.0,
  "asset": "nvidia",
  "symbol": "NVDA",
  "source": "twelve_data"
}
```

*Note: For spot cryptocurrency (`BTC/USD`) and spot gold bullion (`XAU/USD`), `volume` is legitimately `null`.*
