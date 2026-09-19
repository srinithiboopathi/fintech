"""
Trend Indicators Module (SMA, EMA).
Provides strictly backward-looking moving averages for time-series prices.
"""
import pandas as pd
from backend.app.quant.validation import validate_positive_integer


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """
    Calculates Simple Moving Average (SMA).
    
    Formula:
        SMA_n(t) = (1/n) * sum_{i=0}^{n-1} P_{t-i}
        
    Parameters:
        series (pd.Series): Chronologically sorted price series (Close).
        period (int): Lookback window period (n >= 1).
        
    Returns:
        pd.Series: SMA time series. First (period - 1) values are NaN.
    """
    validate_positive_integer(period, name="sma_period", min_value=1)
    if series.empty:
        return pd.Series(dtype=float, index=series.index)
        
    # min_periods=period guarantees that incomplete warmup periods remain NaN
    return series.rolling(window=period, min_periods=period, center=False).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculates Exponential Moving Average (EMA).
    
    Formula:
        alpha = 2 / (period + 1)
        EMA_t = alpha * P_t + (1 - alpha) * EMA_{t-1}
        where EMA_0 = P_0
        
    Parameters:
        series (pd.Series): Chronologically sorted price series (Close).
        period (int): Span period for alpha calculation (period >= 1).
        
    Returns:
        pd.Series: EMA time series with deterministic recursive calculation.
    """
    validate_positive_integer(period, name="ema_period", min_value=1)
    if series.empty:
        return pd.Series(dtype=float, index=series.index)
        
    # adjust=False calculates the standard recursive formula: EMA_t = (1-alpha)*EMA_{t-1} + alpha*P_t
    return series.ewm(span=period, adjust=False).mean()
