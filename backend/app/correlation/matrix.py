"""
QuantLab - Cross-Asset Correlation Matrix Module

Provides institutional-grade cross-asset alignment, returns normalization,
and Pearson correlation matrix calculations across multiple asset time series.
"""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np


def align_price_series(
    prices: Union[Dict[str, pd.Series], pd.DataFrame],
    join: str = "inner",
    ffill_missing: bool = False
) -> pd.DataFrame:
    """
    Align multiple asset price series along a standardized chronological date index.

    Parameters
    ----------
    prices : Union[Dict[str, pd.Series], pd.DataFrame]
        Dictionary mapping asset symbols/names to price Series (indexed by date),
        or a DataFrame with asset price columns indexed by date.
    join : str, default 'inner'
        Alignment method ('inner' for intersection of trading dates, 'outer' for union).
    ffill_missing : bool, default False
        Whether to forward-fill prices for assets not trading on particular calendar dates
        (e.g., crypto trades 24/7/365, while commodities and equities trade on weekdays).
        Only applicable when join='outer'.

    Returns
    -------
    pd.DataFrame
        Aligned price DataFrame sorted chronologically with standardized DatetimeIndex.
    """
    if isinstance(prices, pd.DataFrame):
        if prices.empty:
            return pd.DataFrame()
        df = prices.copy()
    elif isinstance(prices, dict):
        if not prices:
            return pd.DataFrame()
        # Clean each series to ensure DatetimeIndex and deduplication
        cleaned_series = {}
        for asset, s in prices.items():
            if s.empty:
                continue
            s_clean = s.copy()
            if not isinstance(s_clean.index, pd.DatetimeIndex):
                s_clean.index = pd.to_datetime(s_clean.index)
            # Remove duplicated timestamps keeping last
            s_clean = s_clean[~s_clean.index.duplicated(keep="last")]
            s_clean.name = asset
            cleaned_series[asset] = s_clean

        if not cleaned_series:
            return pd.DataFrame()

        df = pd.DataFrame(cleaned_series)
    else:
        raise TypeError(f"Expected dict of pd.Series or pd.DataFrame, received: {type(prices)}")

    if df.empty:
        return pd.DataFrame()

    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Sort chronologically ascending
    df = df.sort_index()

    # Deduplicate index if present
    df = df[~df.index.duplicated(keep="last")]

    if join == "inner":
        df = df.dropna(how="any")
    elif join == "outer":
        if ffill_missing:
            df = df.ffill().dropna(how="all")
    else:
        raise ValueError(f"Unsupported join type: '{join}'. Use 'inner' or 'outer'.")

    return df


def calculate_multi_asset_returns(
    prices_df: pd.DataFrame,
    method: str = "simple",
    drop_first: bool = True
) -> pd.DataFrame:
    """
    Calculate daily percentage or log returns for aligned multi-asset prices.

    Parameters
    ----------
    prices_df : pd.DataFrame
        Aligned price DataFrame with DatetimeIndex.
    method : str, default 'simple'
        Return calculation methodology: 'simple' (pct_change) or 'log' (np.log(P_t / P_{t-1})).
    drop_first : bool, default True
        Whether to drop the initial period which produces NaN.

    Returns
    -------
    pd.DataFrame
        Asset return time-series aligned on date index.
    """
    if prices_df.empty or len(prices_df) < 2:
        return pd.DataFrame(index=prices_df.index, columns=prices_df.columns, dtype=float)

    if method == "simple":
        returns_df = prices_df.pct_change()
    elif method == "log":
        returns_df = np.log(prices_df / prices_df.shift(1))
    else:
        raise ValueError(f"Unsupported return method: '{method}'. Use 'simple' or 'log'.")

    if drop_first:
        returns_df = returns_df.dropna(how="all")

    return returns_df


def calculate_correlation_matrix(
    returns_df: pd.DataFrame,
    method: str = "pearson",
    min_periods: int = 2
) -> pd.DataFrame:
    """
    Calculate the pairwise correlation matrix across multiple asset returns.

    Parameters
    ----------
    returns_df : pd.DataFrame
        Multi-asset returns DataFrame.
    method : str, default 'pearson'
        Correlation method: 'pearson', 'kendall', or 'spearman'.
    min_periods : int, default 2
        Minimum number of overlapping observations required per pair.

    Returns
    -------
    pd.DataFrame
        Symmetric N x N correlation matrix with values between -1.0 and 1.0.
    """
    if returns_df.empty or len(returns_df) < min_periods:
        cols = returns_df.columns if not returns_df.empty else []
        return pd.DataFrame(index=cols, columns=cols, dtype=float)

    clean_returns = returns_df.dropna(how="all")
    corr_matrix = clean_returns.corr(method=method, min_periods=min_periods)
    return corr_matrix


def compute_cross_asset_correlation_matrix(
    prices: Union[Dict[str, pd.Series], pd.DataFrame],
    join: str = "inner",
    method: str = "pearson",
    min_periods: int = 2
) -> pd.DataFrame:
    """
    End-to-end pipeline: Aligns price series, computes daily returns,
    and calculates the cross-asset correlation matrix.

    Parameters
    ----------
    prices : Union[Dict[str, pd.Series], pd.DataFrame]
        Raw asset price series dictionary or DataFrame.
    join : str, default 'inner'
        Alignment join method ('inner' or 'outer').
    method : str, default 'pearson'
        Correlation metric.
    min_periods : int, default 2
        Minimum overlapping observations.

    Returns
    -------
    pd.DataFrame
        Symmetric correlation matrix.
    """
    aligned_prices = align_price_series(prices, join=join)
    if aligned_prices.empty or len(aligned_prices) < 2:
        cols = list(prices.keys()) if isinstance(prices, dict) else prices.columns.tolist()
        return pd.DataFrame(index=cols, columns=cols, dtype=float)

    returns = calculate_multi_asset_returns(aligned_prices, method="simple", drop_first=True)
    return calculate_correlation_matrix(returns, method=method, min_periods=min_periods)
