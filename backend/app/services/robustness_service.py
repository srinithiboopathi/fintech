"""
Robustness Service Layer for QUANTLAB (Phase 8).
Coordinates parameter grid sweeps and sensitivity analysis across assets and strategies.
"""
from typing import Dict, Any, List, Optional
from backend.app.robustness.runner import robustness_runner, RobustnessRunner
from backend.app.robustness.validation import MAX_CONFIGURATIONS


class RobustnessService:
    """Service layer managing strategy robustness and sensitivity evaluation."""

    def __init__(self):
        self.runner: RobustnessRunner = robustness_runner

    def run_robustness(
        self,
        asset: str,
        strategy: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        periods: Optional[List[Dict[str, Optional[str]]]] = None,
        initial_capital: float = 100000.0,
        position_size: float = 1.0,
        transaction_costs: Optional[List[float]] = None,
        risk_free_rate: float = 0.0,
        strategy_parameter_grid: Optional[Dict[str, List[Any]]] = None,
        max_configurations: int = MAX_CONFIGURATIONS,
    ) -> Dict[str, Any]:
        """Runs multi-configuration sensitivity sweep across parameter grid."""
        # If explicit periods not provided, use global start_date / end_date
        test_periods = periods
        if not test_periods:
            test_periods = [{"start_date": start_date, "end_date": end_date}]

        return self.runner.run_sweep(
            asset=asset,
            strategy=strategy,
            parameter_grid=strategy_parameter_grid,
            transaction_costs=transaction_costs,
            periods=test_periods,
            initial_capital=initial_capital,
            position_size=position_size,
            risk_free_rate=risk_free_rate,
            max_configurations=max_configurations,
        )


# Global singleton robustness service
robustness_service = RobustnessService()
