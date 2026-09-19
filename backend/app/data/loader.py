"""
Data Loader Module for QUANTLAB.
Provides read-only access to raw Kaggle datasets.
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import os


class DataLoader:
    def __init__(self, raw_data_dir: Path = None):
        if raw_data_dir is None:
            # Default to repo_root/datasets/raw
            self.raw_data_dir = Path(__file__).resolve().parents[3] / "datasets" / "raw"
        else:
            self.raw_data_dir = Path(raw_data_dir)

    def get_raw_file_paths(self) -> Dict[str, Path]:
        """Returns verified paths to all raw dataset files."""
        return {
            "Gold": self.raw_data_dir / "gold" / "Gold_Spot_historical_data.csv",
            "Bitcoin": self.raw_data_dir / "bitcoin" / "BTC-2017min.csv",
            "NVIDIA": self.raw_data_dir / "nvidia" / "NVIDIA_historical_data.csv",
        }

    def inspect_file(self, file_path: Path) -> Dict[str, Any]:
        """Inspects a raw CSV file and returns structural metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Raw dataset file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        df_sample = pd.read_csv(file_path, nrows=5)
        
        # Read full file for row count and column data types
        df_full = pd.read_csv(file_path)
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "row_count": len(df_full),
            "column_count": len(df_full.columns),
            "columns": list(df_full.columns),
            "dtypes": {col: str(dtype) for col, dtype in df_full.dtypes.items()},
            "first_row": df_full.head(1).to_dict(orient="records"),
            "last_row": df_full.tail(1).to_dict(orient="records"),
            "missing_values": df_full.isnull().sum().to_dict(),
            "exact_duplicate_rows": int(df_full.duplicated().sum()),
        }

    def load_gold_raw(self) -> pd.DataFrame:
        """Loads raw Gold historical data."""
        path = self.get_raw_file_paths()["Gold"]
        if not path.exists():
            raise FileNotFoundError(f"Raw Gold file missing: {path}")
        return pd.read_csv(path)

    def load_bitcoin_raw(self) -> pd.DataFrame:
        """Loads raw Bitcoin minute-level historical data."""
        path = self.get_raw_file_paths()["Bitcoin"]
        if not path.exists():
            raise FileNotFoundError(f"Raw Bitcoin file missing: {path}")
        return pd.read_csv(path)

    def load_nvidia_raw(self) -> pd.DataFrame:
        """Loads raw NVIDIA historical data."""
        path = self.get_raw_file_paths()["NVIDIA"]
        if not path.exists():
            raise FileNotFoundError(f"Raw NVIDIA file missing: {path}")
        return pd.read_csv(path)
