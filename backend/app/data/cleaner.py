"""
Data Cleaner Module for QUANTLAB.
Cleans, sorts, and aligns OHLC envelopes with full audit tracking.
"""
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np


class DataCleaner:
    @staticmethod
    def clean_daily_asset(
        df_raw: pd.DataFrame,
        asset_name: str,
        date_col: str = "Date",
        open_col: str = "Open",
        high_col: str = "High",
        low_col: str = "Low",
        close_col: str = "Close",
        volume_col: str = "Volume"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cleans and aligns daily OHLCV dataset for a given asset.
        """
        df = df_raw.copy()
        raw_count = len(df)
        
        # 1. Parse and normalize dates to YYYY-MM-DD
        parsed_dates = pd.to_datetime(df[date_col], utc=True)
        df['date'] = parsed_dates.dt.strftime('%Y-%m-%d')
        
        # 2. Extract and cast OHLCV columns to float
        df['open'] = df[open_col].astype(float)
        df['high'] = df[high_col].astype(float)
        df['low'] = df[low_col].astype(float)
        df['close'] = df[close_col].astype(float)
        df['volume'] = df[volume_col].astype(float)
        df['asset'] = asset_name
        
        # 3. Sort ascending chronologically
        df = df.sort_values('date', ascending=True).reset_index(drop=True)
        
        # 4. Check for duplicate dates
        duplicate_dates_count = int(df['date'].duplicated().sum())
        if duplicate_dates_count > 0:
            # Aggregate or drop duplicate dates
            df = df.drop_duplicates(subset=['date'], keep='last').reset_index(drop=True)
            
        # 5. Audit OHLC Envelope Inconsistencies
        # Identify rows where high < low, high < open, high < close, low > open, or low > close
        inconsistent_mask = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        inconsistent_count = int(inconsistent_mask.sum())
        
        # Track specific condition counts for reporting
        high_lt_low_count = int((df['high'] < df['low']).sum())
        high_lt_open_count = int((df['high'] < df['open']).sum())
        high_lt_close_count = int((df['high'] < df['close']).sum())
        low_gt_open_count = int((df['low'] > df['open']).sum())
        low_gt_close_count = int((df['low'] > df['close']).sum())
        
        # Fix OHLC envelope:
        # High must be at least max(High, Open, Close)
        # Low must be at most min(Low, Open, Close)
        df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
        df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
        
        # 6. Select and order common schema columns
        cleaned_df = df[['date', 'asset', 'open', 'high', 'low', 'close', 'volume']]
        
        stats = {
            "asset": asset_name,
            "raw_rows": raw_count,
            "cleaned_rows": len(cleaned_df),
            "duplicates_removed": duplicate_dates_count,
            "ohlc_inconsistencies_adjusted": inconsistent_count,
            "high_lt_low_count": high_lt_low_count,
            "high_lt_open_count": high_lt_open_count,
            "high_lt_close_count": high_lt_close_count,
            "low_gt_open_count": low_gt_open_count,
            "low_gt_close_count": low_gt_close_count,
            "date_start": cleaned_df['date'].min(),
            "date_end": cleaned_df['date'].max(),
        }
        
        return cleaned_df, stats
