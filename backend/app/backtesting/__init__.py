"""
Backtesting Package for QUANTLAB.
Provides deterministic portfolio simulation, trade execution, and performance attribution.
"""
from backend.app.backtesting.enums import PositionStatus, OrderType, TradeStatus
from backend.app.backtesting.models import Position, TradeRecordInternal, DailyPortfolioState
from backend.app.backtesting.validation import (
    validate_backtest_parameters,
    validate_backtest_dates,
    validate_strategy_config,
)
from backend.app.backtesting.execution import execute_buy, execute_sell
from backend.app.backtesting.portfolio import PortfolioTracker
from backend.app.backtesting.performance import calculate_portfolio_performance
from backend.app.backtesting.benchmark import (
    calculate_buy_and_hold_benchmark,
    calculate_strategy_comparison,
)
from backend.app.backtesting.engine import BacktestEngine, backtest_engine

__all__ = [
    "PositionStatus",
    "OrderType",
    "TradeStatus",
    "Position",
    "TradeRecordInternal",
    "DailyPortfolioState",
    "validate_backtest_parameters",
    "validate_backtest_dates",
    "validate_strategy_config",
    "execute_buy",
    "execute_sell",
    "PortfolioTracker",
    "calculate_portfolio_performance",
    "calculate_buy_and_hold_benchmark",
    "calculate_strategy_comparison",
    "BacktestEngine",
    "backtest_engine",
]
