"""
Returns Calculation Module (Daily and Cumulative Returns).
Provides arithmetic returns and compounded growth series.
"""
import pandas as pd
import numpy as np


def calculate_daily_returns(series: pd.Series) -> pd.Series:
    """
    Calculates simple daily percentage returns from a close price series.
    
    Formula:
        Return_t = (P_t / P_{t-1}) - 1
        
    Parameters:
        series (pd.Series): Chronologically sorted price series.
        
    Returns:
        pd.Series: Daily arithmetic percentage returns. The first entry is NaN.
    """
    if series.empty:
        return pd.Series(dtype=float, index=series.index)
        
    return series.pct_change(fill_method=None)


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    Calculates compounded cumulative return series from daily percentage returns.
    
    Formula:
        Cumulative_Return_t = prod_{i=1}^t (1 + Return_i) - 1
        
    Parameters:
        returns (pd.Series): Daily percentage returns series (first value may be NaN).
        
    Returns:
        pd.Series: Compounded cumulative return starting at 0.0 at baseline.
    """
    if returns.empty:
        return pd.Series(dtype=float, index=returns.index)
        
    # Replace initial NaN with 0 for compounding baseline
    cleaned_returns = returns.fillna(0.0)
    wealth_index = (1.0 + cleaned_returns).cumprod()
    return wealth_index - 1.0
