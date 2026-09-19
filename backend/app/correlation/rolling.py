"""
QuantLab - Cross-Asset Rolling Correlation Module

Calculates rolling pairwise Pearson correlations across configurable time windows,
enabling detection of market regime shifts and decoupling events between assets.
"""

from typing import Dict, Optional, Tuple
import pandas as pd


def calculate_rolling_pairwise_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 30,
    min_periods: Optional[int] = None
) -> pd.Series:
    """
    Calculate rolling Pearson correlation between two asset return or price series.

    Parameters
    ----------
    series_a : pd.Series
        First asset time series (e.g., daily returns).
    series_b : pd.Series
        Second asset time series (e.g., daily returns).
    window : int, default 30
        Rolling estimation window in trading sessions (must be >= 2).
    min_periods : Optional[int], default None
        Minimum observations in window required to produce a valid estimate.
        Defaults to `window` to prevent lookahead or unrepresentative early estimates.

    Returns
    -------
    pd.Series
        Rolling correlation coefficient series (-1.0 to 1.0) indexed by common trading dates.
        Returns NaN where observations in the window are fewer than min_periods.

    Raises
    ------
    ValueError
        If window < 2 or min_periods < 2.
    """
    if window < 2:
        raise ValueError(f"Rolling window must be an integer >= 2, received: {window}")

    if min_periods is None:
        min_periods = window
    elif min_periods < 2:
        raise ValueError(f"min_periods must be >= 2, received: {min_periods}")

    if series_a.empty or series_b.empty:
        return pd.Series(dtype=float)

    # Standardize series indices
    s_a = series_a.copy()
    s_b = series_b.copy()
    if not isinstance(s_a.index, pd.DatetimeIndex):
        s_a.index = pd.to_datetime(s_a.index)
    if not isinstance(s_b.index, pd.DatetimeIndex):
        s_b.index = pd.to_datetime(s_b.index)

    # Remove potential duplicated timestamps
    s_a = s_a[~s_a.index.duplicated(keep="last")]
    s_b = s_b[~s_b.index.duplicated(keep="last")]

    # Inner join to align strictly on intersecting dates
    aligned = pd.concat([s_a, s_b], axis=1, join="inner").dropna()

    if aligned.empty or len(aligned) < min_periods:
        # Return all-NaN or empty series with aligned index
        pair_name = f"{series_a.name or 'A'}_{series_b.name or 'B'}"
        return pd.Series(index=aligned.index, dtype=float, name=pair_name)

    col_a = aligned.iloc[:, 0]
    col_b = aligned.iloc[:, 1]

    rolling_corr = col_a.rolling(window=window, min_periods=min_periods).corr(col_b)
    pair_name = f"{series_a.name or 'A'}_{series_b.name or 'B'}"
    rolling_corr.name = pair_name

    return rolling_corr


def calculate_multi_asset_rolling_correlations(
    returns_df: pd.DataFrame,
    window: int = 30,
    min_periods: Optional[int] = None
) -> pd.DataFrame:
    """
    Calculate rolling correlations for all unique asset pairs in a multi-asset returns DataFrame.

    Parameters
    ----------
    returns_df : pd.DataFrame
        DataFrame of asset returns with columns representing asset names/symbols.
    window : int, default 30
        Rolling window in trading days (default 30 trading days).
    min_periods : Optional[int], default None
        Minimum periods required for valid estimation. Defaults to window.

    Returns
    -------
    pd.DataFrame
        DataFrame where each column represents a pairwise rolling correlation
        (e.g., 'Gold_Bitcoin', 'Gold_NVIDIA', 'Bitcoin_NVIDIA').
    """
    if returns_df.empty or len(returns_df.columns) < 2:
        return pd.DataFrame()

    assets = list(returns_df.columns)
    pair_series = {}

    for i in range(len(assets)):
        for j in range(i + 1, len(assets)):
            asset_1 = assets[i]
            asset_2 = assets[j]
            pair_key = f"{asset_1}_{asset_2}"

            corr_series = calculate_rolling_pairwise_correlation(
                returns_df[asset_1],
                returns_df[asset_2],
                window=window,
                min_periods=min_periods
            )
            pair_series[pair_key] = corr_series

    return pd.DataFrame(pair_series)
