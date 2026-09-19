"""
Data Normalizer Module for QUANTLAB.
Transforms individual asset datasets into unified multi-asset structures.
"""
from typing import List
import pandas as pd


class DataNormalizer:
    @staticmethod
    def combine_assets(asset_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Combines multiple normalized asset DataFrames into a single unified dataset.
        Sorts by date ascending, then asset name.
        """
        if not asset_dfs:
            raise ValueError("No asset DataFrames provided to combine")
            
        combined = pd.concat(asset_dfs, ignore_index=True)
        
        # Sort chronologically by date, then asset
        combined = combined.sort_values(by=['date', 'asset'], ascending=[True, True]).reset_index(drop=True)
        
        # Enforce exact column order
        return combined[['date', 'asset', 'open', 'high', 'low', 'close', 'volume']]
