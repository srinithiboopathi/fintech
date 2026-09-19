"""
Backtest Service Layer for QUANTLAB (Phase 7).
Orchestrates portfolio simulations, strategy configurations, and performance reporting.
"""
from typing import Dict, Any, List, Optional

from backend.app.backtesting.engine import backtest_engine, BacktestEngine
from backend.app.strategies.enums import StrategyType


class BacktestService:
    """Service layer managing backtesting executions and strategy metadata."""

    def __init__(self):
        self.engine: BacktestEngine = backtest_engine

    def run_backtest(
        self,
        asset: str,
        strategy: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 100000.0,
        position_size: float = 1.0,
        transaction_cost: float = 0.001,
        risk_free_rate: float = 0.0,
        strategy_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs an end-to-end deterministic portfolio simulation."""
        return self.engine.run(
            asset=asset,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            position_size=position_size,
            transaction_cost=transaction_cost,
            risk_free_rate=risk_free_rate,
            strategy_parameters=strategy_parameters,
        )

    def get_supported_strategies(self) -> List[Dict[str, Any]]:
        """Returns catalog of available trading strategies and default parameters."""
        return [
            {
                "name": StrategyType.SMA_CROSSOVER.value,
                "display_name": "SMA Crossover",
                "description": "Captures trend direction by tracking when a Fast SMA crosses above or below a Slow SMA baseline.",
                "default_parameters": {
                    "fast_period": 20,
                    "slow_period": 50,
                },
            },
            {
                "name": StrategyType.EMA_TREND.value,
                "display_name": "EMA Trend",
                "description": "Generates trend-following signals via Short EMA and Long EMA cross events.",
                "default_parameters": {
                    "short_period": 20,
                    "long_period": 50,
                },
            },
            {
                "name": StrategyType.MOMENTUM.value,
                "display_name": "Momentum",
                "description": "Evaluates rate-of-change momentum and trades zero-line transition crossings.",
                "default_parameters": {
                    "lookback": 20,
                },
            },
            {
                "name": StrategyType.MEAN_REVERSION.value,
                "display_name": "Mean Reversion",
                "description": "Identifies overextended price deviations from a central rolling moving average baseline.",
                "default_parameters": {
                    "window": 20,
                    "threshold": 0.02,
                },
            },
        ]


# Global singleton service instance
backtest_service = BacktestService()
