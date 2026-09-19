# QuantLab Datasets

This directory houses raw and processed time-series market data for key benchmark assets:
1. **Gold (GC=F / XAU-USD)**: Continuous commodity futures / spot benchmark.
2. **Bitcoin (BTC-USD)**: Digital asset, 24/7 global crypto market.
3. **NVIDIA Corp (NVDA)**: Benchmark mega-cap tech / semiconductor growth equity.

## Directory Layout
- `raw/`: Unaltered ingested data files with original trading venue timestamps and headers.
- `processed/`: Cleaned, outlier-checked, missing-value-interpolated, and calendar-aligned daily time-series ready for backtesting and analytics.
- `processed/market_data.csv`: Unified multi-asset time-series matrix for cross-asset correlation and portfolio backtesting.
