"""
Quantitative Analysis Package for QUANTLAB.
Provides pure, reusable, deterministic mathematical algorithms for:
- Trend Indicators (SMA, EMA)
- Returns (Daily, Cumulative)
- Volatility (Historical, Annualized)
- Risk-Adjusted Metrics (Sharpe Ratio)
- Drawdown (Time-Series, Maximum Drawdown)
- Rolling Performance
"""
from backend.app.quant.indicators import calculate_sma, calculate_ema
from backend.app.quant.returns import calculate_daily_returns, calculate_cumulative_returns
from backend.app.quant.volatility import (
    calculate_rolling_volatility,
    calculate_annualized_volatility,
    calculate_rolling_annualized_volatility,
    get_annualization_factor,
)
from backend.app.quant.sharpe import calculate_sharpe_ratio, calculate_rolling_sharpe
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown
from backend.app.quant.rolling import calculate_rolling_metrics, calculate_rolling_returns
from backend.app.quant.validation import validate_positive_integer, validate_date_order

__all__ = [
    "calculate_sma",
    "calculate_ema",
    "calculate_daily_returns",
    "calculate_cumulative_returns",
    "calculate_rolling_volatility",
    "calculate_annualized_volatility",
    "calculate_rolling_annualized_volatility",
    "get_annualization_factor",
    "calculate_sharpe_ratio",
    "calculate_rolling_sharpe",
    "calculate_drawdown_series",
    "calculate_max_drawdown",
    "calculate_rolling_metrics",
    "calculate_rolling_returns",
    "validate_positive_integer",
    "validate_date_order",
]
