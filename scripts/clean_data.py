"""
Script to inspect, clean, and validate raw market data.
Usage: python scripts/clean_data.py
"""
import sys
from pathlib import Path
import json

# Add project root to sys.path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from backend.app.data.loader import DataLoader
from backend.app.data.cleaner import DataCleaner
from backend.app.data.aggregator import DataAggregator


def main():
    print("=" * 60)
    print("QUANTLAB DATA CLEANING SCRIPT")
    print("=" * 60)

    loader = DataLoader()
    
    # 1. Gold
    print("\n[1/3] Loading & Cleaning Gold Data...")
    df_gold_raw = loader.load_gold_raw()
    df_gold_clean, gold_stats = DataCleaner.clean_daily_asset(
        df_gold_raw,
        asset_name="Gold",
        date_col="Date",
        open_col="Open",
        high_col="High",
        low_col="Low",
        close_col="Close",
        volume_col="Volume"
    )
    print(f"  Gold cleaned: {gold_stats['cleaned_rows']} rows (Date range: {gold_stats['date_start']} to {gold_stats['date_end']})")
    print(f"  OHLC envelope adjustments: {gold_stats['ohlc_inconsistencies_adjusted']}")

    # 2. Bitcoin
    print("\n[2/3] Loading & Aggregating Bitcoin Minute Data...")
    df_btc_raw = loader.load_bitcoin_raw()
    df_btc_clean, btc_stats = DataAggregator.aggregate_bitcoin_minutes_to_daily(df_btc_raw)
    print(f"  Bitcoin aggregated: {btc_stats['daily_bars_count']} daily bars from {btc_stats['source_minutes_count']} minute rows")
    print(f"  Date range: {btc_stats['date_range_start']} to {btc_stats['date_range_end']}")

    # 3. NVIDIA
    print("\n[3/3] Loading & Cleaning NVIDIA Data...")
    df_nvda_raw = loader.load_nvidia_raw()
    df_nvda_clean, nvda_stats = DataCleaner.clean_daily_asset(
        df_nvda_raw,
        asset_name="NVIDIA",
        date_col="Date",
        open_col="Open",
        high_col="High",
        low_col="Low",
        close_col="Close",
        volume_col="Volume"
    )
    print(f"  NVIDIA cleaned: {nvda_stats['cleaned_rows']} rows (Date range: {nvda_stats['date_start']} to {nvda_stats['date_end']})")
    print(f"  OHLC envelope adjustments: {nvda_stats['ohlc_inconsistencies_adjusted']}")

    print("\nCleaning inspection complete. Run scripts/normalize_data.py to generate processed datasets.")


if __name__ == "__main__":
    main()
