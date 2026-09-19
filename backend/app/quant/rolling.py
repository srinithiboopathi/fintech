"""
Rolling Performance Metrics Engine.
Computes multi-window rolling return, rolling volatility, rolling Sharpe, and drawdown series.
"""
import numpy as np
import pandas as pd
from backend.app.quant.validation import validate_positive_integer
from backend.app.quant.returns import calculate_daily_returns
from backend.app.quant.volatility import calculate_rolling_annualized_volatility
from backend.app.quant.sharpe import calculate_rolling_sharpe
from backend.app.quant.drawdown import calculate_drawdown_series


def calculate_rolling_returns(prices: pd.Series, window: int) -> pd.Series:
    """
    Calculates rolling window arithmetic returns from a price series.
    
    Formula:
        Rolling_Return_t = (P_t / P_{t - window}) - 1.0
        
    Parameters:
        prices (pd.Series): Chronologically sorted price series.
        window (int): Lookback period in days (window >= 1).
        
    Returns:
        pd.Series: Rolling percentage return series.
    """
    validate_positive_integer(window, name="rolling_window", min_value=1)
    if prices.empty:
        return pd.Series(dtype=float, index=prices.index)
        
    return prices.pct_change(periods=window, fill_method=None)


def calculate_rolling_metrics(
    df: pd.DataFrame,
    window: int,
    risk_free_rate_annual: float = 0.0,
    annualization_factor: int = 252
) -> pd.DataFrame:
    """
    Computes a comprehensive set of rolling performance metrics on a price DataFrame.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing 'date' and 'close' columns.
        window (int): Rolling lookback window in days (window >= 2).
        risk_free_rate_annual (float): Annualized risk-free rate.
        annualization_factor (int): 252 for traditional markets, 365 for crypto.
        
    Returns:
        pd.DataFrame: DataFrame with columns:
            ['date', 'rolling_return', 'rolling_volatility', 'rolling_sharpe', 'drawdown']
    """
    validate_positive_integer(window, name="rolling_window", min_value=2)
    validate_positive_integer(annualization_factor, name="annualization_factor", min_value=1)
    
    if df.empty or "close" not in df.columns:
        return pd.DataFrame(columns=["date", "rolling_return", "rolling_volatility", "rolling_sharpe", "drawdown"])
        
    prices = df["close"]
    daily_returns = calculate_daily_returns(prices)
    
    rolling_ret = calculate_rolling_returns(prices, window=window)
    rolling_vol = calculate_rolling_annualized_volatility(daily_returns, window=window, annualization_factor=annualization_factor)
    rolling_shp = calculate_rolling_sharpe(daily_returns, window=window, risk_free_rate_annual=risk_free_rate_annual, annualization_factor=annualization_factor)
    dd_series = calculate_drawdown_series(prices)
    
    result = pd.DataFrame({
        "date": df["date"],
        "rolling_return": rolling_ret,
        "rolling_volatility": rolling_vol,
        "rolling_sharpe": rolling_shp,
        "drawdown": dd_series,
    })
    
    return result
