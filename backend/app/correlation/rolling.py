"""
Rolling Correlation Engine.
Calculates strictly backward-looking rolling Pearson correlation time-series across asset pairs.
"""
from typing import Optional
import numpy as np
import pandas as pd

from backend.app.correlation.alignment import align_two_asset_returns
from backend.app.correlation.validation import validate_window_size


def calculate_rolling_correlation(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str,
    name_b: str,
    window: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Computes rolling Pearson correlation between two assets over a configurable lookback window.
    
    Formula:
        r_t = rolling_cov_w(R_A, R_B) / (rolling_std_w(R_A) * rolling_std_w(R_B))
        
    Parameters:
        df_a (pd.DataFrame): Historical price DataFrame for asset A.
        df_b (pd.DataFrame): Historical price DataFrame for asset B.
        name_a (str): Canonical symbol/name for asset A.
        name_b (str): Canonical symbol/name for asset B.
        window (int): Rolling window in days (window >= 2).
        start_date (str, optional): Start date filter.
        end_date (str, optional): End date filter.
        
    Returns:
        pd.DataFrame: DataFrame with columns ['date', 'rolling_correlation']
    """
    validate_window_size(window, min_value=2)
    
    # 1. Align on full available history to properly satisfy warm-up lookback
    aligned = align_two_asset_returns(df_a, df_b, name_a, name_b)
    
    if aligned.empty:
        return pd.DataFrame(columns=["date", "rolling_correlation"])
        
    s_a = aligned[name_a]
    s_b = aligned[name_b]
    
    # Rolling Pearson correlation with center=False to prevent look-ahead bias
    rolling_corr = s_a.rolling(window=window, min_periods=window, center=False).corr(s_b)
    
    # Replace infs / slight float inaccuracies
    rolling_corr = rolling_corr.replace([np.inf, -np.inf], np.nan)
    rolling_corr = rolling_corr.clip(-1.0, 1.0)
    
    result_df = pd.DataFrame({
        "date": aligned["date"],
        "rolling_correlation": rolling_corr
    })
    
    # 2. Slice to requested date range
    if start_date:
        result_df = result_df[result_df["date"] >= start_date]
    if end_date:
        result_df = result_df[result_df["date"] <= end_date]
        
    return result_df.reset_index(drop=True)
