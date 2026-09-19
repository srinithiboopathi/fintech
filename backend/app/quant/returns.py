"""
QuantLab - Returns Analytics Module

Computes simple/daily returns and cumulative performance metrics.
"""

from typing import Optional
import pandas as pd


def calculate_daily_returns(series: pd.Series, fill_zero: bool = False) -> pd.Series:
    """
    Calculate daily (simple) percentage returns from an asset price series.

    Parameters
    ----------
    series : pd.Series
        Time-series of asset prices.
    fill_zero : bool, default False
        Whether to fill the initial return observation with 0.0 instead of NaN.

    Returns
    -------
    pd.Series
        Daily percentage returns aligned with the input index.
    """
    if series.empty:
        return pd.Series(dtype=float, index=series.index)

    returns = series.pct_change()

    if fill_zero and not returns.empty:
        returns = returns.fillna(0.0)

    return returns


def calculate_cumulative_returns(returns: pd.Series, compound: bool = True) -> pd.Series:
    """
    Calculate cumulative returns from a series of periodic returns.

    Parameters
    ----------
    returns : pd.Series
        Time-series of periodic (daily) percentage returns.
    compound : bool, default True
        If True, calculates geometric compounding (prod(1 + r) - 1).
        If False, calculates simple arithmetic sum (cumsum(r)).

    Returns
    -------
    pd.Series
        Cumulative returns series aligned with the input index.
    """
    if returns.empty:
        return pd.Series(dtype=float, index=returns.index)

    # Treat NaN returns (like day 0) as 0.0 return for cumulative compounding
    clean_returns = returns.fillna(0.0)

    if compound:
        return (1.0 + clean_returns).cumprod() - 1.0
    else:
        return clean_returns.cumsum()


def calculate_cumulative_returns_from_prices(prices: pd.Series) -> pd.Series:
    """
    Calculate cumulative returns directly from asset prices relative to initial price.

    Parameters
    ----------
    prices : pd.Series
        Time-series of asset prices.

    Returns
    -------
    pd.Series
        Cumulative returns relative to the first non-null observation.
    """
    if prices.empty:
        return pd.Series(dtype=float, index=prices.index)

    valid_prices = prices.dropna()
    if valid_prices.empty:
        return pd.Series(dtype=float, index=prices.index)

    base_price = valid_prices.iloc[0]
    if base_price == 0:
        raise ValueError("Initial price is zero; cannot compute percentage returns.")

    return (prices - base_price) / base_price
