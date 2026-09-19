"""
Volatility Analysis Module (Historical and Annualized Volatility).
Provides rolling and overall standard deviation metrics of return series.
"""
from typing import Optional
import numpy as np
import pandas as pd
from backend.app.quant.validation import validate_positive_integer


def get_annualization_factor(asset: Optional[str]) -> int:
    """
    Returns the appropriate annualization trading-day factor.
    
    - Bitcoin: 365 days (24/7 continuous digital asset market)
    - Gold / NVIDIA / Traditional Equities & Commodities: 252 trading days
    """
    if not asset:
        return 252
    cleaned = asset.strip().lower()
    if cleaned in ["bitcoin", "btc", "btc-usd", "btc/usd"]:
        return 365
    return 252


def calculate_rolling_volatility(returns: pd.Series, window: int) -> pd.Series:
    """
    Calculates rolling historical sample standard deviation of daily returns.
    
    Formula:
        sigma_t = sqrt( (1 / (w - 1)) * sum_{i=0}^{w-1} (R_{t-i} - mean_R)^2 )
        
    Parameters:
        returns (pd.Series): Daily percentage returns.
        window (int): Rolling lookback window in days (window >= 2).
        
    Returns:
        pd.Series: Rolling daily standard deviation. First (window - 1) entries are NaN.
    """
    validate_positive_integer(window, name="volatility_window", min_value=2)
    if returns.empty:
        return pd.Series(dtype=float, index=returns.index)
        
    return returns.rolling(window=window, min_periods=window, center=False).std(ddof=1)


def calculate_annualized_volatility(
    returns: pd.Series,
    annualization_factor: int = 252
) -> Optional[float]:
    """
    Calculates annualized volatility for a given series of daily returns.
    
    Formula:
        Annualized Volatility = std(daily_returns, ddof=1) * sqrt(annualization_factor)
        
    Parameters:
        returns (pd.Series): Daily percentage returns.
        annualization_factor (int): 252 for traditional assets, 365 for 24/7 crypto.
        
    Returns:
        float or None: Annualized volatility or None if insufficient observations.
    """
    validate_positive_integer(annualization_factor, name="annualization_factor", min_value=1)
    valid_returns = returns.dropna()
    if len(valid_returns) < 2:
        return None
        
    daily_std = float(valid_returns.std(ddof=1))
    if np.isnan(daily_std):
        return None
    return float(daily_std * np.sqrt(annualization_factor))


def calculate_rolling_annualized_volatility(
    returns: pd.Series,
    window: int,
    annualization_factor: int = 252
) -> pd.Series:
    """
    Calculates rolling annualized volatility.
    
    Formula:
        Rolling Annualized Volatility_t = rolling_std_t * sqrt(annualization_factor)
    """
    validate_positive_integer(window, name="volatility_window", min_value=2)
    validate_positive_integer(annualization_factor, name="annualization_factor", min_value=1)
    
    rolling_daily = calculate_rolling_volatility(returns, window)
    return rolling_daily * np.sqrt(annualization_factor)
