import numpy as np
import pandas as pd


def calculate_simple_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change()


def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change()


def calculate_log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1))


def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    return (1 + returns.fillna(0)).cumprod() - 1


def calculate_cumulative_returns_from_prices(prices: pd.Series) -> pd.Series:
    return prices / prices.iloc[0] - 1