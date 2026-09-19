"""
Data Pipeline Orchestrator for QUANTLAB.
Executes end-to-end deterministic ingestion, cleaning, validation, and normalization.
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd

from backend.app.data.loader import DataLoader
from backend.app.data.aggregator import DataAggregator
from backend.app.data.cleaner import DataCleaner
from backend.app.data.validator import DataValidator
from backend.app.data.normalizer import DataNormalizer


def run_pipeline(
    raw_dir: Path = None,
    processed_dir: Path = None
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """
    Executes the deterministic data processing pipeline.
    """
    repo_root = Path(__file__).resolve().parents[3]
    if raw_dir is None:
        raw_dir = repo_root / "datasets" / "raw"
    if processed_dir is None:
        processed_dir = repo_root / "datasets" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)
    loader = DataLoader(raw_dir)

    report: Dict[str, Any] = {
        "raw_inspection": {},
        "cleaning_stats": {},
        "validation_results": {},
        "output_files": {},
    }

    # 1. Inspect Raw Files
    for asset_name, path in loader.get_raw_file_paths().items():
        report["raw_inspection"][asset_name] = loader.inspect_file(path)

    # 2. Process Gold Data
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
    report["cleaning_stats"]["Gold"] = gold_stats

    # 3. Process Bitcoin Data (Minute -> Daily Aggregation)
    df_btc_raw = loader.load_bitcoin_raw()
    df_btc_clean, btc_stats = DataAggregator.aggregate_bitcoin_minutes_to_daily(df_btc_raw)
    report["cleaning_stats"]["Bitcoin"] = btc_stats

    # 4. Process NVIDIA Data
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
    report["cleaning_stats"]["NVIDIA"] = nvda_stats

    # 5. Combine All Assets
    df_combined = DataNormalizer.combine_assets([df_gold_clean, df_btc_clean, df_nvda_clean])

    # 6. Validate All Processed DataFrames
    datasets_to_validate = {
        "gold_daily": (df_gold_clean, "Gold"),
        "bitcoin_daily": (df_btc_clean, "Bitcoin"),
        "nvidia_daily": (df_nvda_clean, "NVIDIA"),
        "market_data": (df_combined, None),
    }

    all_valid = True
    for name, (df_target, expected_asset) in datasets_to_validate.items():
        is_valid, errors = DataValidator.validate_normalized_dataframe(df_target, expected_asset)
        report["validation_results"][name] = {
            "is_valid": is_valid,
            "errors": errors,
            "rows": len(df_target),
            "columns": list(df_target.columns),
            "date_range": [df_target['date'].min(), df_target['date'].max()]
        }
        if not is_valid:
            all_valid = False

    if not all_valid:
        raise ValueError(f"Data validation failed: {report['validation_results']}")

    # 7. Write to datasets/processed/
    gold_out = processed_dir / "gold_daily.csv"
    btc_out = processed_dir / "bitcoin_daily.csv"
    nvda_out = processed_dir / "nvidia_daily.csv"
    combined_out = processed_dir / "market_data.csv"

    df_gold_clean.to_csv(gold_out, index=False)
    df_btc_clean.to_csv(btc_out, index=False)
    df_nvda_clean.to_csv(nvda_out, index=False)
    df_combined.to_csv(combined_out, index=False)

    report["output_files"] = {
        "gold_daily.csv": str(gold_out),
        "bitcoin_daily.csv": str(btc_out),
        "nvidia_daily.csv": str(nvda_out),
        "market_data.csv": str(combined_out),
    }

    result_dfs = {
        "gold_daily": df_gold_clean,
        "bitcoin_daily": df_btc_clean,
        "nvidia_daily": df_nvda_clean,
        "market_data": df_combined,
    }

    return result_dfs, report
