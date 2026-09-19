"""
Parameter Grid Generator for Multi-Asset Strategy Robustness Testing.
"""
import itertools
from typing import Dict, Any, List, Optional

from backend.app.strategies.enums import StrategyType
from backend.app.strategies.validation import validate_strategy_name
from backend.app.robustness.models import BacktestConfig
from backend.app.robustness.validation import validate_grid_size


def generate_strategy_parameter_combinations(
    strategy: str,
    grid: Optional[Dict[str, List[Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Constructs valid hyperparameter tuples for the specified quantitative strategy.
    Skips mathematically invalid combinations (e.g. fast >= slow).
    """
    strat_type = validate_strategy_name(strategy)
    grid = grid or {}
    valid_combos: List[Dict[str, Any]] = []

    if strat_type == StrategyType.SMA_CROSSOVER:
        fast_list = grid.get("fast_period", [20])
        slow_list = grid.get("slow_period", [50])
        if not isinstance(fast_list, list):
            fast_list = [fast_list]
        if not isinstance(slow_list, list):
            slow_list = [slow_list]

        for fast, slow in itertools.product(fast_list, slow_list):
            if isinstance(fast, int) and isinstance(slow, int) and fast >= 2 and slow >= 2 and fast < slow:
                valid_combos.append({"fast_period": fast, "slow_period": slow})

    elif strat_type == StrategyType.EMA_TREND:
        short_list = grid.get("short_period", [20])
        long_list = grid.get("long_period", [50])
        if not isinstance(short_list, list):
            short_list = [short_list]
        if not isinstance(long_list, list):
            long_list = [long_list]

        for short, long in itertools.product(short_list, long_list):
            if isinstance(short, int) and isinstance(long, int) and short >= 2 and long >= 2 and short < long:
                valid_combos.append({"short_period": short, "long_period": long})

    elif strat_type == StrategyType.MOMENTUM:
        lookback_list = grid.get("lookback", [20])
        if not isinstance(lookback_list, list):
            lookback_list = [lookback_list]

        for lookback in lookback_list:
            if isinstance(lookback, int) and lookback >= 1:
                valid_combos.append({"lookback": lookback})

    elif strat_type == StrategyType.MEAN_REVERSION:
        window_list = grid.get("window", [20])
        threshold_list = grid.get("threshold", [0.02])
        if not isinstance(window_list, list):
            window_list = [window_list]
        if not isinstance(threshold_list, list):
            threshold_list = [threshold_list]

        for window, threshold in itertools.product(window_list, threshold_list):
            if isinstance(window, int) and isinstance(threshold, (int, float)) and window >= 2 and threshold > 0:
                valid_combos.append({"window": window, "threshold": float(threshold)})

    return valid_combos


def build_backtest_configurations(
    strategy: str,
    grid: Optional[Dict[str, List[Any]]],
    transaction_costs: List[float],
    periods: List[Dict[str, Optional[str]]],
    initial_capital: float = 100000.0,
    position_size: float = 1.0,
    risk_free_rate: float = 0.0,
    max_limit: int = 100,
) -> List[BacktestConfig]:
    """
    Generates the Cartesian product of (Strategy Parameters x Transaction Costs x Backtest Periods).
    Enforces maximum grid configuration limits.
    """
    param_combos = generate_strategy_parameter_combinations(strategy, grid)
    if not param_combos:
        raise ValueError(
            f"No valid parameter combinations could be formed for strategy '{strategy}' with grid: {grid}"
        )

    configs: List[BacktestConfig] = []

    for param_dict, cost, period_dict in itertools.product(param_combos, transaction_costs, periods):
        configs.append(
            BacktestConfig(
                parameters=param_dict,
                transaction_cost=cost,
                start_date=period_dict.get("start_date"),
                end_date=period_dict.get("end_date"),
                initial_capital=initial_capital,
                position_size=position_size,
                risk_free_rate=risk_free_rate,
            )
        )

    validate_grid_size(len(configs), max_limit=max_limit)
    return configs
