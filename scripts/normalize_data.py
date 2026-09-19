"""
Script to execute the complete end-to-end data normalization pipeline.
Usage: python scripts/normalize_data.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from backend.app.data.pipeline import run_pipeline


def main():
    print("=" * 60)
    print("QUANTLAB DATA NORMALIZATION PIPELINE")
    print("=" * 60)

    try:
        result_dfs, report = run_pipeline()
        
        print("\n[OK] Pipeline executed successfully!")
        print("\nGenerated Processed Datasets:")
        for name, file_path in report["output_files"].items():
            df = result_dfs[name.replace(".csv", "")]
            print(f"  * {name}: {len(df):,} rows, {len(df.columns)} cols -> {file_path}")
            
        print("\nDataset Summary:")
        for asset, stats in report["cleaning_stats"].items():
            print(f"  * {asset}: {stats}")
            
        print("\nValidation Summary:")
        for name, val in report["validation_results"].items():
            status = "PASSED" if val["is_valid"] else "FAILED"
            print(f"  * {name}: {status} ({val['rows']} rows, {val['date_range'][0]} to {val['date_range'][1]})")

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
