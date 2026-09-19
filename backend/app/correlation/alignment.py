"""
Date Alignment and Return Series Synchronization Module.
Ensures cross-asset correlation is calculated ONLY on overlapping real market dates.
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd

from backend.app.quant.returns import calculate_daily_returns


def align_two_asset_returns(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str,
    name_b: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Aligns daily returns of two assets on overlapping calendar dates.
    
    Parameters:
        df_a (pd.DataFrame): DataFrame for asset A with ['date', 'close'].
        df_b (pd.DataFrame): DataFrame for asset B with ['date', 'close'].
        name_a (str): Canonical name of asset A.
        name_b (str): Canonical name of asset B.
        start_date (str, optional): Start date filter (YYYY-MM-DD).
        end_date (str, optional): End date filter (YYYY-MM-DD).
        
    Returns:
        pd.DataFrame: Aligned DataFrame with columns ['date', name_a, name_b],
                      sorted ascending by date, with all NaNs dropped.
    """
    # Calculate daily returns independently per asset on sorted price series
    df_a_sorted = df_a.sort_values("date", ascending=True).reset_index(drop=True)
    df_b_sorted = df_b.sort_values("date", ascending=True).reset_index(drop=True)
    
    ret_a = calculate_daily_returns(df_a_sorted["close"])
    ret_b = calculate_daily_returns(df_b_sorted["close"])
    
    if name_a == name_b:
        merged = pd.DataFrame({"date": df_a_sorted["date"], name_a: ret_a}).dropna()
        if start_date:
            merged = merged[merged["date"] >= start_date]
        if end_date:
            merged = merged[merged["date"] <= end_date]
        return merged.reset_index(drop=True)

    series_a = pd.DataFrame({"date": df_a_sorted["date"], name_a: ret_a}).dropna()
    series_b = pd.DataFrame({"date": df_b_sorted["date"], name_b: ret_b}).dropna()
    
    # Inner join on common calendar dates
    merged = pd.merge(series_a, series_b, on="date", how="inner")
    merged = merged.sort_values("date", ascending=True).reset_index(drop=True)
    
    if start_date:
        merged = merged[merged["date"] >= start_date]
    if end_date:
        merged = merged[merged["date"] <= end_date]
        
    return merged.reset_index(drop=True)


def align_asset_returns(
    asset_dataframes: Dict[str, pd.DataFrame],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    how: str = "inner"
) -> pd.DataFrame:
    """
    Synchronizes daily returns across multiple assets by calendar date.
    
    Parameters:
        asset_dataframes (Dict[str, pd.DataFrame]): Dictionary mapping asset name to DataFrame with ['date', 'close'].
        start_date (str, optional): Start date filter (YYYY-MM-DD).
        end_date (str, optional): End date filter (YYYY-MM-DD).
        how (str): 'inner' (only overlapping dates for all assets) or 'outer' (pairwise union).
        
    Returns:
        pd.DataFrame: Synchronized return matrix with 'date' as primary column and asset returns as features.
    """
    if not asset_dataframes:
        return pd.DataFrame(columns=["date"])
        
    merged_df = None
    for asset_name, df in asset_dataframes.items():
        sorted_df = df.sort_values("date", ascending=True).reset_index(drop=True)
        returns = calculate_daily_returns(sorted_df["close"])
        asset_ret = pd.DataFrame({"date": sorted_df["date"], asset_name: returns}).dropna()
        
        if merged_df is None:
            merged_df = asset_ret
        else:
            merged_df = pd.merge(merged_df, asset_ret, on="date", how=how)
            
    if merged_df is not None and not merged_df.empty:
        merged_df = merged_df.sort_values("date", ascending=True).reset_index(drop=True)
        if start_date:
            merged_df = merged_df[merged_df["date"] >= start_date]
        if end_date:
            merged_df = merged_df[merged_df["date"] <= end_date]
        merged_df = merged_df.reset_index(drop=True)
    else:
        merged_df = pd.DataFrame(columns=["date"] + list(asset_dataframes.keys()))
        
    return merged_df
