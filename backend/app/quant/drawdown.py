"""
QuantLab - Drawdown Analysis Module

Calculates high-water mark (running peak), continuous drawdown series,
and maximum peak-to-trough drawdown for assets and investment portfolios.
"""

from typing import Tuple
import pandas as pd


def calculate_peak_value(series: pd.Series) -> pd.Series:
    """
    Calculate the running peak (high-water mark) of a price or portfolio equity series.

    Parameters
    ----------
    series : pd.Series
        Time-series of prices or cumulative equity values.

    Returns
    -------
    pd.Series
        Running maximum values aligned with the input index.
    """
    if series.empty:
        return pd.Series(dtype=float, index=series.index)

    return series.cummax()


def calculate_drawdown(series: pd.Series) -> pd.Series:
    """
    Calculate the drawdown series representing percentage decline from previous peak.

    Parameters
    ----------
    series : pd.Series
        Time-series of asset prices or portfolio equity.

    Returns
    -------
    pd.Series
        Continuous drawdown series (values are <= 0.0, e.g. -0.15 represents a 15% drawdown).
    """
    if series.empty:
        return pd.Series(dtype=float, index=series.index)

    peaks = calculate_peak_value(series)
    # Avoid division by zero if series starts at or reaches zero
    drawdown = (series - peaks) / peaks.replace(0, float("nan"))
    return drawdown.fillna(0.0)


def calculate_max_drawdown(series: pd.Series) -> float:
    """
    Calculate the Maximum Drawdown (MDD) observed over the entire series.

    Parameters
    ----------
    series : pd.Series
        Time-series of asset prices or portfolio equity.

    Returns
    -------
    float
        Maximum drawdown as a non-positive float (e.g., -0.32 for 32% maximum drop).
        Returns 0.0 if series is empty or experienced no drawdown.
    """
    if series.empty:
        return 0.0

    dd = calculate_drawdown(series)
    if dd.empty:
        return 0.0

    min_dd = float(dd.min())
    return min_dd if min_dd <= 0.0 else 0.0
