"""
Market Data Service Module for QUANTLAB.
Handles in-memory cached access to processed market datasets.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd


class MarketDataService:
    ASSET_ALIASES = {
        "gold": "Gold",
        "gc=f": "Gold",
        "bitcoin": "Bitcoin",
        "btc": "Bitcoin",
        "btc-usd": "Bitcoin",
        "btc/usd": "Bitcoin",
        "nvidia": "NVIDIA",
        "nvda": "NVIDIA",
    }

    ASSET_METADATA = {
        "Gold": {"name": "Gold", "category": "Commodity"},
        "Bitcoin": {"name": "Bitcoin", "category": "Cryptocurrency"},
        "NVIDIA": {"name": "NVIDIA", "category": "Equities"},
    }

    def __init__(self, processed_dir: Optional[Path] = None):
        if processed_dir is None:
            # Default to repo_root/datasets/processed
            self.processed_dir = Path(__file__).resolve().parents[3] / "datasets" / "processed"
        else:
            self.processed_dir = Path(processed_dir)
            
        self._cache: Dict[str, pd.DataFrame] = {}

    def normalize_asset_name(self, asset: str) -> Optional[str]:
        """Normalizes case-insensitive input and aliases to canonical asset names."""
        if not asset:
            return None
        cleaned = asset.strip().lower()
        return self.ASSET_ALIASES.get(cleaned, None)

    def _get_dataset(self, asset: str) -> pd.DataFrame:
        """Loads and caches processed dataset for a specific asset."""
        canonical = self.normalize_asset_name(asset)
        if not canonical:
            raise ValueError(f"Unknown asset identifier: {asset}")

        if canonical not in self._cache:
            file_map = {
                "Gold": self.processed_dir / "gold_daily.csv",
                "Bitcoin": self.processed_dir / "bitcoin_daily.csv",
                "NVIDIA": self.processed_dir / "nvidia_daily.csv",
            }
            file_path = file_map[canonical]
            if not file_path.exists():
                raise FileNotFoundError(f"Processed dataset not found: {file_path}")
            
            df = pd.read_csv(file_path)
            # Ensure sorting
            df = df.sort_values("date", ascending=True).reset_index(drop=True)
            self._cache[canonical] = df

        return self._cache[canonical]

    def _get_combined_dataset(self) -> pd.DataFrame:
        """Loads and caches combined processed dataset."""
        if "market_data" not in self._cache:
            file_path = self.processed_dir / "market_data.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"Combined processed dataset not found: {file_path}")
            
            df = pd.read_csv(file_path)
            df = df.sort_values(by=["date", "asset"], ascending=[True, True]).reset_index(drop=True)
            self._cache["market_data"] = df

        return self._cache["market_data"]

    def get_available_assets(self) -> List[Dict[str, str]]:
        """Returns list of all available assets."""
        assets_list = []
        for symbol, info in self.ASSET_METADATA.items():
            assets_list.append({
                "symbol": symbol,
                "name": info["name"],
                "category": info["category"]
            })
        return assets_list

    def get_asset_metadata(self, asset: str) -> Dict[str, Any]:
        """Returns calculated metadata for a single asset."""
        canonical = self.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(f"Asset '{asset}' is not recognized")

        df = self._get_dataset(canonical)
        return {
            "asset": canonical,
            "start_date": str(df["date"].min()),
            "end_date": str(df["date"].max()),
            "records": int(len(df)),
            "frequency": "daily"
        }

    def get_all_date_ranges(self) -> Dict[str, Dict[str, Any]]:
        """Returns available date ranges for all assets."""
        result = {}
        for canonical in self.ASSET_METADATA.keys():
            df = self._get_dataset(canonical)
            result[canonical] = {
                "start_date": str(df["date"].min()),
                "end_date": str(df["date"].max()),
                "records": int(len(df))
            }
        return result

    def get_asset_history(
        self,
        asset: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves filtered daily OHLCV records for a specific asset.
        Returns (records_list, total_filtered_count).
        """
        canonical = self.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(f"Asset '{asset}' is not recognized")

        df = self._get_dataset(canonical)

        # Apply date filters
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]

        total_count = len(df)
        
        # Apply limit
        if limit and limit > 0:
            df = df.head(limit)

        records = df.to_dict(orient="records")
        return records, total_count

    def get_multi_asset_history(
        self,
        assets: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 2000
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves filtered multi-asset daily OHLCV records from combined dataset.
        Returns (records_list, total_filtered_count).
        """
        df = self._get_combined_dataset()

        # Filter by assets if specified
        if assets:
            canonical_assets = []
            for a in assets:
                norm = self.normalize_asset_name(a)
                if norm:
                    canonical_assets.append(norm)
            if canonical_assets:
                df = df[df["asset"].isin(canonical_assets)]

        # Apply date filters
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]

        total_count = len(df)

        # Apply limit
        if limit and limit > 0:
            df = df.head(limit)

        records = df.to_dict(orient="records")
        return records, total_count


# Global singleton service instance
market_service = MarketDataService()
