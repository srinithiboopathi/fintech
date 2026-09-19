import pandas as pd


def calculate_peak_value(equity: pd.Series) -> pd.Series:
    return equity.cummax()


def calculate_drawdown(equity: pd.Series) -> pd.Series:
    peak = calculate_peak_value(equity)
    return (equity - peak) / peak


def calculate_max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0

    drawdown = calculate_drawdown(equity)
    return float(drawdown.min())