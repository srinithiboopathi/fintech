"""
QuantLab - Sharpe Ratio Module

Calculates annualized Sharpe ratio adjusting for configurable risk-free rate.
"""

import numpy as np
import pandas as pd


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    trading_days: int = 252
) -> float:
    """
    Calculate the annualized Sharpe Ratio from daily returns.

    Parameters
    ----------
    returns : pd.Series
        Time-series of daily returns.
    risk_free_rate : float, default 0.0
        Annualized benchmark risk-free rate (e.g. 0.02 for 2%).
    trading_days : int, default 252
        Number of trading days per year for annualization.

    Returns
    -------
    float
        Annualized Sharpe ratio. Returns 0.0 if data is insufficient or volatility is zero.

    Raises
    ------
    ValueError
        If trading_days < 1.
    """
    if trading_days < 1:
        raise ValueError(f"trading_days must be >= 1, received: {trading_days}")

    if returns.empty:
        return 0.0

    clean_returns = returns.dropna()
    if len(clean_returns) < 2:
        return 0.0

    daily_rf = risk_free_rate / trading_days
    excess_returns = clean_returns - daily_rf

    excess_mean = float(excess_returns.mean())
    excess_std = float(excess_returns.std(ddof=1))

    if np.isnan(excess_std) or excess_std <= 0:
        return 0.0

    annualized_sharpe = (excess_mean / excess_std) * np.sqrt(trading_days)
    return float(annualized_sharpe)
