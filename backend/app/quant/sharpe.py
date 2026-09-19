import pandas as pd


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
    trading_days: int | None = None,
) -> float:
    if trading_days is not None:
        periods_per_year = trading_days

    clean_returns = returns.dropna()

    if len(clean_returns) < 2:
        return 0.0

    excess_returns = clean_returns - (
        risk_free_rate / periods_per_year
    )

    std = excess_returns.std(ddof=1)

    if std == 0 or pd.isna(std):
        return 0.0

    return float(
        excess_returns.mean()
        / std
        * (periods_per_year ** 0.5)
    )