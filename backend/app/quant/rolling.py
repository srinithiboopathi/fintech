"""
QuantLab - Rolling Analytics Module

Computes time-varying statistical dynamics:
- Rolling Annualized Volatility
- Rolling Pearson Correlation
"""

import numpy as np
import pandas as pd


def calculate_rolling_volatility(
    returns: pd.Series,
    window: int = 20,
    trading_days: int = 252,
    ddof: int = 1
) -> pd.Series:
    """
    Calculate rolling annualized volatility across a moving time window.

    Parameters
    ----------
    returns : pd.Series
        Time-series of periodic daily returns.
    window : int, default 20
        Number of periods in the rolling estimation window (must be >= 2).
    trading_days : int, default 252
        Number of trading sessions per year for annualization.
    ddof : int, default 1
        Delta Degrees of Freedom for sample standard deviation.

    Returns
    -------
    pd.Series
        Rolling annualized volatility aligned with the input index.

    Raises
    ------
    ValueError
        If window < 2 or trading_days < 1 or ddof < 0.
    """
    if window < 2:
        raise ValueError(f"Rolling window must be >= 2 for volatility calculation, received: {window}")
    if trading_days < 1:
        raise ValueError(f"trading_days must be >= 1, received: {trading_days}")
    if ddof < 0:
        raise ValueError(f"ddof must be >= 0, received: {ddof}")

    if returns.empty:
        return pd.Series(dtype=float, index=returns.index)

    rolling_std = returns.rolling(window=window, min_periods=window).std(ddof=ddof)
    return rolling_std * np.sqrt(trading_days)


def calculate_rolling_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    Calculate rolling Pearson correlation between two aligned asset series.

    Parameters
    ----------
    series_a : pd.Series
        First asset series (returns or prices).
    series_b : pd.Series
        Second asset series (returns or prices).
    window : int, default 20
        Number of periods in the rolling correlation window (must be >= 2).

    Returns
    -------
    pd.Series
        Rolling correlation coefficient (-1.0 to 1.0) indexed by common timestamps.

    Raises
    ------
    ValueError
        If window < 2.
    """
    if window < 2:
        raise ValueError(f"Rolling window must be >= 2 for correlation calculation, received: {window}")

    if series_a.empty or series_b.empty:
        return pd.Series(dtype=float)

    # Align on common index to ensure paired observations without lookahead
    aligned = pd.concat([series_a, series_b], axis=1, join="inner")
    if aligned.empty:
        return pd.Series(dtype=float)

    s1 = aligned.iloc[:, 0]
    s2 = aligned.iloc[:, 1]

    rolling_corr = s1.rolling(window=window, min_periods=window).corr(s2)
    return rolling_corr
