"""
Drawdown and Downside Risk Module.
Calculates historical drawdown time-series and Maximum Drawdown (MDD).
"""
from typing import Optional, Tuple
import numpy as np
import pandas as pd


def calculate_drawdown_series(prices_or_wealth: pd.Series) -> pd.Series:
    """
    Calculates the percentage drawdown time-series from a price or cumulative wealth curve.
    
    Formula:
        Running Peak_t = max(V_0, ..., V_t)
        Drawdown_t = (V_t / Running Peak_t) - 1.0
        
    Parameters:
        prices_or_wealth (pd.Series): Chronologically sorted price or wealth series.
        
    Returns:
        pd.Series: Drawdown time-series as negative percentages (<= 0.0).
    """
    if prices_or_wealth.empty:
        return pd.Series(dtype=float, index=prices_or_wealth.index)
        
    running_peak = prices_or_wealth.cummax()
    drawdown = (prices_or_wealth / running_peak) - 1.0
    return drawdown


def calculate_max_drawdown(drawdown_series: pd.Series) -> Optional[float]:
    """
    Calculates the Maximum Drawdown (MDD) from a drawdown series.
    
    Formula:
        MDD = min(Drawdown_t)
        
    Parameters:
        drawdown_series (pd.Series): Drawdown series values (<= 0.0).
        
    Returns:
        float or None: Maximum percentage drawdown (negative float, e.g. -0.25 for -25%).
    """
    valid = drawdown_series.dropna()
    if valid.empty:
        return None
        
    mdd = float(valid.min())
    return mdd if not np.isnan(mdd) else None


def calculate_drawdown_and_peak(prices_or_wealth: pd.Series) -> Tuple[pd.Series, pd.Series, Optional[float]]:
    """
    Returns running peak, drawdown series, and maximum drawdown for comprehensive analysis.
    """
    if prices_or_wealth.empty:
        empty = pd.Series(dtype=float, index=prices_or_wealth.index)
        return empty, empty, None
        
    running_peak = prices_or_wealth.cummax()
    drawdown = (prices_or_wealth / running_peak) - 1.0
    mdd = float(drawdown.min()) if not drawdown.empty else None
    return running_peak, drawdown, mdd
