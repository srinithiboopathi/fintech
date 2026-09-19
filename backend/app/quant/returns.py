import pandas as pd


def calculate_daily_returns(
    prices: pd.Series,
    fill_zero: bool = False,
) -> pd.Series:
    returns = prices.pct_change()

    if fill_zero:
        returns = returns.fillna(0.0)

    return returns


def calculate_cumulative_returns(
    daily_returns: pd.Series,
    compound: bool = False,
) -> pd.Series:
    if daily_returns.empty:
        return daily_returns.copy()

    if compound:
        return (1.0 + daily_returns.fillna(0.0)).cumprod() - 1.0

    return daily_returns.cumsum()


def calculate_cumulative_returns_from_prices(
    prices: pd.Series,
) -> pd.Series:
    if prices.empty:
        return prices.copy()

    return prices / prices.iloc[0] - 1.0