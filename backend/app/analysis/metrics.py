import pandas as pd

from app.quant.sharpe import calculate_sharpe_ratio
from app.quant.volatility import calculate_annualized_volatility
from app.quant.drawdown import calculate_max_drawdown


def calculate_performance_metrics(
    equity: pd.Series,
    initial_capital: float,
) -> dict:
    returns = equity.pct_change().dropna()

    final_value = float(equity.iloc[-1])

    total_return = (
        (final_value - initial_capital) / initial_capital
        if initial_capital > 0
        else 0.0
    )

    return {
        "initial_capital": float(initial_capital),
        "final_value": final_value,
        "total_return": float(total_return),
        "annualized_volatility": calculate_annualized_volatility(returns),
        "sharpe_ratio": calculate_sharpe_ratio(returns),
        "maximum_drawdown": calculate_max_drawdown(equity),
    }