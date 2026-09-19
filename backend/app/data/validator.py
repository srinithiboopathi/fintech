"""
Data Validator Module for QUANTLAB.
Enforces strict quantitative integrity and schema conformity.
"""
from typing import Dict, Any, List, Tuple
import pandas as pd
import re


class DataValidator:
    REQUIRED_COLUMNS = ['date', 'asset', 'open', 'high', 'low', 'close', 'volume']
    ALLOWED_ASSETS = {'Gold', 'Bitcoin', 'NVIDIA'}
    DATE_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    @classmethod
    def validate_normalized_dataframe(cls, df: pd.DataFrame, expected_asset: str = None) -> Tuple[bool, List[str]]:
        """
        Runs comprehensive validation checks on a normalized DataFrame.
        Returns (is_valid, list_of_errors).
        """
        errors = []

        # 1. Schema check
        if list(df.columns) != cls.REQUIRED_COLUMNS:
            errors.append(f"Schema mismatch. Expected {cls.REQUIRED_COLUMNS}, got {list(df.columns)}")

        if len(df) == 0:
            errors.append("DataFrame is empty.")
            return False, errors

        # 2. Asset check
        unique_assets = set(df['asset'].unique())
        if not unique_assets.issubset(cls.ALLOWED_ASSETS):
            errors.append(f"Invalid asset names found: {unique_assets - cls.ALLOWED_ASSETS}")
        if expected_asset and unique_assets != {expected_asset}:
            errors.append(f"Expected asset '{expected_asset}', found {unique_assets}")

        # 3. Null / NaN check
        null_counts = df.isnull().sum()
        if null_counts.any():
            errors.append(f"Null/NaN values detected: {null_counts[null_counts > 0].to_dict()}")

        # 4. Date format & uniqueness check
        invalid_dates = df[~df['date'].astype(str).str.match(cls.DATE_REGEX)]
        if len(invalid_dates) > 0:
            errors.append(f"Found {len(invalid_dates)} invalid date formats (expected YYYY-MM-DD)")

        # Duplicate check per asset
        duplicate_count = df.duplicated(subset=['date', 'asset']).sum()
        if duplicate_count > 0:
            errors.append(f"Found {duplicate_count} duplicate (date, asset) records")

        # 5. Sorting check per asset
        for asset, group in df.groupby('asset'):
            if not group['date'].is_monotonic_increasing:
                errors.append(f"Dates for asset '{asset}' are not strictly ascending chronologically")

        # 6. Price positivity check
        for col in ['open', 'high', 'low', 'close']:
            if (df[col] <= 0).any():
                invalid_count = (df[col] <= 0).sum()
                errors.append(f"Found {invalid_count} non-positive values in '{col}' column")

        # 7. Volume non-negativity check
        if (df['volume'] < 0).any():
            errors.append(f"Found {(df['volume'] < 0).sum()} negative volume values")

        # 8. OHLC Logical Envelope Integrity
        invalid_high_low = (df['high'] < df['low']).sum()
        if invalid_high_low > 0:
            errors.append(f"Found {invalid_high_low} rows where high < low")

        invalid_high_open = (df['high'] < df['open']).sum()
        if invalid_high_open > 0:
            errors.append(f"Found {invalid_high_open} rows where high < open")

        invalid_high_close = (df['high'] < df['close']).sum()
        if invalid_high_close > 0:
            errors.append(f"Found {invalid_high_close} rows where high < close")

        invalid_low_open = (df['low'] > df['open']).sum()
        if invalid_low_open > 0:
            errors.append(f"Found {invalid_low_open} rows where low > open")

        invalid_low_close = (df['low'] > df['close']).sum()
        if invalid_low_close > 0:
            errors.append(f"Found {invalid_low_close} rows where low > close")

        return len(errors) == 0, errors
