import pandas as pd


def calculate_daily_volatility(returns: pd.Series) -> float:
    return float(returns.std())


def calculate_annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = 252,
) -> float:
    return float(returns.std() * (periods_per_year ** 0.5))