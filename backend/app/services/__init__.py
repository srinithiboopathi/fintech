"""
Services Package for QUANTLAB Backend.
"""
from backend.app.services.market_service import market_service, MarketDataService
from backend.app.services.quant_service import quant_service, QuantService
from backend.app.services.correlation_service import correlation_service, CorrelationService
from backend.app.services.strategy_service import strategy_service, StrategyService
from backend.app.services.backtesting_service import backtest_service, BacktestService

__all__ = [
    "market_service",
    "MarketDataService",
    "quant_service",
    "QuantService",
    "correlation_service",
    "CorrelationService",
    "strategy_service",
    "StrategyService",
    "backtest_service",
    "BacktestService",
]


