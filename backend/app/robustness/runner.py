"""
Runner Engine for Multi-Configuration Robustness Sweeps.
"""
from typing import List, Dict, Any, Optional

from backend.app.backtesting.engine import backtest_engine, BacktestEngine
from backend.app.robustness.models import RobustnessResult, BacktestConfig
from backend.app.robustness.validation import (
    validate_robustness_inputs,
    MAX_CONFIGURATIONS,
)
from backend.app.robustness.parameter_grid import build_backtest_configurations
from backend.app.robustness.comparison import summarize_robustness_results


class RobustnessRunner:
    """Coordinates execution of parameter sweeps across costs, periods, and hyperparameters."""

    def __init__(self, engine: Optional[BacktestEngine] = None):
        self.engine = engine or backtest_engine

    def run_sweep(
        self,
        asset: str,
        strategy: str,
        parameter_grid: Optional[Dict[str, List[Any]]] = None,
        transaction_costs: Optional[List[float]] = None,
        periods: Optional[List[Dict[str, Optional[str]]]] = None,
        initial_capital: float = 100000.0,
        position_size: float = 1.0,
        risk_free_rate: float = 0.0,
        max_configurations: int = MAX_CONFIGURATIONS,
    ) -> Dict[str, Any]:
        """
        Executes backtests across all Cartesian combinations in the parameter grid.
        """
        costs = validate_robustness_inputs(
            asset=asset,
            strategy=strategy,
            initial_capital=initial_capital,
            position_size=position_size,
            transaction_costs=transaction_costs,
            risk_free_rate=risk_free_rate,
        )

        test_periods = periods if periods is not None and len(periods) > 0 else [{"start_date": None, "end_date": None}]

        configs = build_backtest_configurations(
            strategy=strategy,
            grid=parameter_grid,
            transaction_costs=costs,
            periods=test_periods,
            initial_capital=initial_capital,
            position_size=position_size,
            risk_free_rate=risk_free_rate,
            max_limit=max_configurations,
        )

        results: List[RobustnessResult] = []

        for cfg in configs:
            bt_res = self.engine.run(
                asset=asset,
                strategy=strategy,
                start_date=cfg.start_date,
                end_date=cfg.end_date,
                initial_capital=cfg.initial_capital,
                position_size=cfg.position_size,
                transaction_cost=cfg.transaction_cost,
                risk_free_rate=cfg.risk_free_rate,
                strategy_parameters=cfg.parameters,
            )

            perf = bt_res["performance"]
            meta = bt_res["backtest"]

            results.append(
                RobustnessResult(
                    parameters=cfg.parameters,
                    transaction_cost=cfg.transaction_cost,
                    start_date=meta["start_date"],
                    end_date=meta["end_date"],
                    initial_capital=perf["initial_capital"],
                    final_portfolio_value=perf["final_portfolio_value"],
                    total_return=perf["total_return"],
                    annualized_return=perf["annualized_return"],
                    annualized_volatility=perf["annualized_volatility"],
                    sharpe_ratio=perf["sharpe_ratio"],
                    maximum_drawdown=perf["maximum_drawdown"],
                    number_of_trades=perf["number_of_trades"],
                    win_rate=perf["win_rate"],
                )
            )

        canonical = self.engine.market_service.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(f"Asset '{asset}' is not recognized. Supported assets: Gold, Bitcoin, NVIDIA.")

        summary = summarize_robustness_results(
            results=results,
            transaction_costs=costs,
            periods=test_periods,
            parameter_grid=parameter_grid or {},
        )

        return {
            "asset": canonical,
            "strategy": strategy.strip().lower().replace("-", "_"),
            "summary": summary,
            "results": [r.to_dict() for r in results],
        }


# Global singleton runner
robustness_runner = RobustnessRunner()

