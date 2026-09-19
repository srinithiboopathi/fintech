"""
QuantLab Quantitative Analytics Engine
"""

from .indicators import calculate_sma, calculate_ema
from .returns import (
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_cumulative_returns_from_prices,
)
from .volatility import calculate_annualized_volatility
from .sharpe import calculate_sharpe_ratio
from .drawdown import (
    calculate_peak_value,
    calculate_drawdown,
    calculate_max_drawdown,
)
from .rolling import (
    calculate_rolling_volatility,
    calculate_rolling_correlation,
)

__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_cumulative_returns_from_prices",
    "calculate_annualized_volatility",
    "calculate_sharpe_ratio",
    "calculate_peak_value",
    "calculate_drawdown",
    "calculate_max_drawdown",
    "calculate_rolling_volatility",
    "calculate_rolling_correlation",
]
