"""
QuantLab - Technical Indicators Module

Provides core moving average indicators:
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
"""

from typing import Optional
import pandas as pd


def calculate_sma(series: pd.Series, window: int, min_periods: Optional[int] = None) -> pd.Series:
    """
    Calculate the Simple Moving Average (SMA) of a price series.

    Parameters
    ----------
    series : pd.Series
        Time-series of numerical asset prices.
    window : int
        Size of the moving window (number of periods). Must be >= 1.
    min_periods : Optional[int], default None
        Minimum number of observations required to have a value. Defaults to `window`
        to prevent look-ahead or unrepresentative averages at the series start.

    Returns
    -------
    pd.Series
        Rolling simple moving average aligned with the input index.

    Raises
    ------
    ValueError
        If window is less than 1.
    """
    if window < 1:
        raise ValueError(f"Window must be a positive integer >= 1, received: {window}")

    if series.empty:
        return pd.Series(dtype=float, index=series.index)

    if min_periods is None:
        min_periods = window

    return series.rolling(window=window, min_periods=min_periods).mean()


def calculate_ema(series: pd.Series, span: int, adjust: bool = False) -> pd.Series:
    """
    Calculate the Exponential Moving Average (EMA) of a price series.

    Parameters
    ----------
    series : pd.Series
        Time-series of numerical asset prices.
    span : int
        Decay span for exponential weighting (alpha = 2 / (span + 1)). Must be >= 1.
    adjust : bool, default False
        Whether to divide by decaying adjustment factor in beginning periods.
        False aligns with standard institutional trading platform conventions.

    Returns
    -------
    pd.Series
        Exponential moving average aligned with the input index.

    Raises
    ------
    ValueError
        If span is less than 1.
    """
    if span < 1:
        raise ValueError(f"Span must be a positive integer >= 1, received: {span}")

    if series.empty:
        return pd.Series(dtype=float, index=series.index)

    return series.ewm(span=span, adjust=adjust).mean()
