import pandas as pd


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    excess_returns = returns.dropna() - (
        risk_free_rate / periods_per_year
    )

    if excess_returns.std() == 0:
        return 0.0

    return float(
        excess_returns.mean()
        / excess_returns.std()
        * (periods_per_year ** 0.5)
    )