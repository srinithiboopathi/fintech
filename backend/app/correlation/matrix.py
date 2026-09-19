"""
Correlation Matrix and Pairwise Correlation Module.
Computes Pearson correlation coefficient on aligned historical returns.
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from backend.app.correlation.alignment import align_two_asset_returns


def calculate_pearson_correlation(
    series_a: pd.Series,
    series_b: pd.Series
) -> Optional[float]:
    """
    Computes sample Pearson correlation between two aligned series.
    
    Formula:
        r = sum((x_i - mean_x) * (y_i - mean_y)) / (sqrt(sum((x_i - mean_x)^2)) * sqrt(sum((y_i - mean_y)^2)))
        
    Returns None if:
        - Series have length < 2
        - Standard deviation of either series is 0 / NaN
    """
    valid_df = pd.DataFrame({"a": series_a, "b": series_b}).dropna()
    if len(valid_df) < 2:
        return None
        
    a = valid_df["a"]
    b = valid_df["b"]
    
    std_a = float(a.std(ddof=1))
    std_b = float(b.std(ddof=1))
    
    if np.isnan(std_a) or np.isnan(std_b) or std_a <= 1e-12 or std_b <= 1e-12:
        return None
        
    cov = float(a.cov(b))
    r = cov / (std_a * std_b)
    
    if np.isnan(r) or np.isinf(r):
        return None
        
    # Clamp to [-1.0, 1.0] for slight floating point inaccuracies
    return float(np.clip(r, -1.0, 1.0))


def calculate_pairwise_correlation(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    name_a: str,
    name_b: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculates pairwise correlation between two assets on aligned dates.
    
    Returns:
        Dict with keys:
            - asset_a (str)
            - asset_b (str)
            - correlation (Optional[float])
            - observations (int)
            - start_date (str)
            - end_date (str)
    """
    aligned = align_two_asset_returns(df_a, df_b, name_a, name_b, start_date=start_date, end_date=end_date)
    
    if aligned.empty:
        return {
            "asset_a": name_a,
            "asset_b": name_b,
            "correlation": None,
            "observations": 0,
            "start_date": start_date or "",
            "end_date": end_date or "",
        }
        
    if name_a == name_b:
        corr = 1.0 if len(aligned) >= 2 else None
    else:
        corr = calculate_pearson_correlation(aligned[name_a], aligned[name_b])
    
    return {
        "asset_a": name_a,
        "asset_b": name_b,
        "correlation": corr,
        "observations": len(aligned),
        "start_date": str(aligned["date"].min()),
        "end_date": str(aligned["date"].max()),
    }


def calculate_correlation_matrix(
    asset_dataframes: Dict[str, pd.DataFrame],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Computes a complete cross-asset Pearson correlation matrix and pairwise observation counts.
    
    Parameters:
        asset_dataframes (Dict[str, pd.DataFrame]): Dictionary mapping asset names to historical price DataFrames.
        start_date (str, optional): Start date filter.
        end_date (str, optional): End date filter.
        
    Returns:
        Dict with:
            - assets (List[str])
            - matrix (Dict[str, Dict[str, Optional[float]]])
            - observation_counts (Dict[str, Dict[str, int]])
            - start_date (str)
            - end_date (str)
            - total_overlapping_dates (int)
    """
    assets = list(asset_dataframes.keys())
    matrix: Dict[str, Dict[str, Optional[float]]] = {}
    counts: Dict[str, Dict[str, int]] = {}
    
    min_dates = []
    max_dates = []
    
    for a in assets:
        matrix[a] = {}
        counts[a] = {}
        
    for i, a1 in enumerate(assets):
        for j, a2 in enumerate(assets):
            if i == j:
                # Self correlation
                df_single = asset_dataframes[a1]
                pair_res = calculate_pairwise_correlation(
                    df_single, df_single, a1, a2, start_date=start_date, end_date=end_date
                )
                matrix[a1][a2] = 1.0 if pair_res["observations"] >= 2 else None
                counts[a1][a2] = pair_res["observations"]
                if pair_res["start_date"]:
                    min_dates.append(pair_res["start_date"])
                    max_dates.append(pair_res["end_date"])
            elif j > i:
                # Calculate pair
                pair_res = calculate_pairwise_correlation(
                    asset_dataframes[a1], asset_dataframes[a2], a1, a2, start_date=start_date, end_date=end_date
                )
                corr_val = pair_res["correlation"]
                obs_val = pair_res["observations"]
                
                matrix[a1][a2] = corr_val
                matrix[a2][a1] = corr_val
                counts[a1][a2] = obs_val
                counts[a2][a1] = obs_val
                
                if pair_res["start_date"]:
                    min_dates.append(pair_res["start_date"])
                    max_dates.append(pair_res["end_date"])

    overall_start = min(min_dates) if min_dates else (start_date or "")
    overall_end = max(max_dates) if max_dates else (end_date or "")

    return {
        "assets": assets,
        "matrix": matrix,
        "observation_counts": counts,
        "start_date": overall_start,
        "end_date": overall_end,
    }
