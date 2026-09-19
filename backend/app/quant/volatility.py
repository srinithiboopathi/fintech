"""
QuantLab - Volatility Module

Calculates annualized volatility and dispersion metrics from daily return series.
"""

import numpy as np
import pandas as pd


def calculate_annualized_volatility(
    returns: pd.Series,
    trading_days: int = 252,
    ddof: int = 1
) -> float:
    """
    Calculate the annualized volatility (standard deviation) from daily returns.

    Parameters
    ----------
    returns : pd.Series
        Series of daily returns.
    trading_days : int, default 252
        Number of trading sessions in a year for annualization.
    ddof : int, default 1
        Delta Degrees of Freedom for sample standard deviation.

    Returns
    -------
    float
        Annualized volatility. Returns 0.0 if insufficient observations exist.

    Raises
    ------
    ValueError
        If trading_days < 1 or ddof < 0.
    """
    if trading_days < 1:
        raise ValueError(f"trading_days must be >= 1, received: {trading_days}")
    if ddof < 0:
        raise ValueError(f"ddof must be >= 0, received: {ddof}")

    if returns.empty:
        return 0.0

    clean_returns = returns.dropna()
    if len(clean_returns) <= ddof:
        return 0.0

    daily_std = float(clean_returns.std(ddof=ddof))
    if np.isnan(daily_std) or daily_std <= 0:
        return 0.0

    return float(daily_std * np.sqrt(trading_days))
