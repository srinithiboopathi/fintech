"""
Sharpe Ratio and Risk-Adjusted Return Module.
Computes annualized Sharpe ratio and rolling Sharpe ratio with zero-volatility protection.
"""
from typing import Optional
import numpy as np
import pandas as pd
from backend.app.quant.validation import validate_positive_integer


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate_annual: float = 0.0,
    annualization_factor: int = 252
) -> Optional[float]:
    """
    Calculates the annualized Sharpe Ratio.
    
    Formula:
        r_f_daily = risk_free_rate_annual / annualization_factor
        excess_returns = daily_returns - r_f_daily
        Sharpe = (mean(excess_returns) / std(excess_returns, ddof=1)) * sqrt(annualization_factor)
        
    Parameters:
        returns (pd.Series): Daily percentage returns.
        risk_free_rate_annual (float): Annualized risk-free interest rate (e.g. 0.02 for 2%). Default 0.0.
        annualization_factor (int): 252 for traditional assets, 365 for 24/7 crypto.
        
    Returns:
        float or None: Annualized Sharpe ratio or None if volatility is zero or data is insufficient.
    """
    validate_positive_integer(annualization_factor, name="annualization_factor", min_value=1)
    valid_returns = returns.dropna()
    if len(valid_returns) < 2:
        return None
        
    daily_rf = risk_free_rate_annual / float(annualization_factor)
    excess_returns = valid_returns - daily_rf
    
    mean_excess = float(excess_returns.mean())
    std_excess = float(excess_returns.std(ddof=1))
    
    # Protect against zero or near-zero volatility to avoid division by zero / infinity
    if np.isnan(std_excess) or std_excess <= 1e-12:
        return None
        
    sharpe = (mean_excess / std_excess) * np.sqrt(annualization_factor)
    if np.isnan(sharpe) or np.isinf(sharpe):
        return None
        
    return float(sharpe)


def calculate_rolling_sharpe(
    returns: pd.Series,
    window: int,
    risk_free_rate_annual: float = 0.0,
    annualization_factor: int = 252
) -> pd.Series:
    """
    Calculates rolling annualized Sharpe Ratio over a specified lookback window.
    
    Parameters:
        returns (pd.Series): Daily percentage returns.
        window (int): Rolling lookback window in days (window >= 2).
        risk_free_rate_annual (float): Annualized risk-free rate.
        annualization_factor (int): 252 for traditional assets, 365 for crypto.
        
    Returns:
        pd.Series: Rolling annualized Sharpe ratio.
    """
    validate_positive_integer(window, name="rolling_window", min_value=2)
    validate_positive_integer(annualization_factor, name="annualization_factor", min_value=1)
    
    if returns.empty:
        return pd.Series(dtype=float, index=returns.index)
        
    daily_rf = risk_free_rate_annual / float(annualization_factor)
    excess_returns = returns - daily_rf
    
    rolling_mean = excess_returns.rolling(window=window, min_periods=window, center=False).mean()
    rolling_std = excess_returns.rolling(window=window, min_periods=window, center=False).std(ddof=1)
    
    # Handle zero/near-zero std without generating inf
    rolling_sharpe = (rolling_mean / rolling_std.replace(0, np.nan)) * np.sqrt(annualization_factor)
    return rolling_sharpe.replace([np.inf, -np.inf], np.nan)
