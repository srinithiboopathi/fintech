import pandas as pd


def calculate_annualized_volatility(
    returns: pd.Series,
    periods_per_year: int = 252,
    trading_days: int | None = None,
) -> float:
    if trading_days is not None:
        periods_per_year = trading_days

    clean_returns = returns.dropna()

    if len(clean_returns) < 2:
        return 0.0

    return float(clean_returns.std(ddof=1) * (periods_per_year ** 0.5))