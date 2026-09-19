"""
backend/app/services/strategy_comparison.py

Quantitative Strategy Comparison & Parameter Robustness Analysis Service.

Responsibilities:
1. Compare all four trading strategies (SMA Crossover, EMA Trend, Momentum, Mean Reversion)
   under strictly identical baseline conditions:
   - Identical asset and historical time window
   - Identical initial capital
   - Identical transaction cost rate
   - Identical cash allocation fraction
   - Identical Next-Observation execution causality (P_{t+1})
   - Factual, objective metric reporting (NO ranking, NO "winner/loser" labeling)

2. Perform parameter sensitivity / robustness testing across bounded discrete grids:
   - Generate and validate explicit parameter combinations
   - Enforce parameter bounds (e.g. short_period < long_period for SMA)
   - Bounded combination limit (maximum 50 combinations) to prevent denial of service
   - Report factual metrics for every tested configuration without cherry-picking or optimization bias
"""

import itertools
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.models.schemas import (
    CleanHistoricalPoint,
    StrategyComparisonRequest,
    StrategyComparisonResponse,
    StrategyComparisonItem,
    RobustnessAnalysisRequest,
    RobustnessAnalysisResponse,
    RobustnessCombinationResult,
    BenchmarkResults,
)
from app.services.strategies import strategy_service, SUPPORTED_STRATEGIES
from app.services.backtesting import backtesting_service, BacktestRequest
from app.utils.exceptions import (
    UnsupportedStrategyError,
    InvalidComparisonRequestError,
    InvalidRobustnessParameterError,
    InvalidBacktestParameterError,
    InsufficientHistoricalDataError,
)

logger = logging.getLogger("market_ingestion")

MAX_ROBUSTNESS_COMBINATIONS = 50


class StrategyComparisonService:
    """Service orchestrating strategy comparison and parameter sensitivity testing."""

    def __init__(self):
        self.supported_strategies = list(SUPPORTED_STRATEGIES)

    def _validate_common_backtest_params(
        self,
        initial_capital: Optional[float],
        transaction_cost_rate: Optional[float],
        allocation: Optional[float],
    ) -> Tuple[float, float, float]:
        """Validates common financial simulation assumptions."""
        cap = 100000.0 if initial_capital is None else float(initial_capital)
        if cap <= 0.0:
            raise InvalidBacktestParameterError(
                f"initial_capital must be a positive number greater than 0, got {cap}."
            )

        fee = 0.001 if transaction_cost_rate is None else float(transaction_cost_rate)
        if fee < 0.0:
            raise InvalidBacktestParameterError(
                f"transaction_cost_rate must be non-negative (>= 0), got {fee}."
            )

        alloc = 1.0 if allocation is None else float(allocation)
        if alloc <= 0.0 or alloc > 1.0:
            raise InvalidBacktestParameterError(
                f"allocation must be strictly within range (0.0, 1.0], got {alloc}."
            )

        return cap, fee, alloc

    def compare_strategies(
        self,
        clean_points: List[CleanHistoricalPoint],
        request: StrategyComparisonRequest,
        asset_name: str,
        symbol: str,
        source: str = "Twelve Data",
    ) -> StrategyComparisonResponse:
        """
        Executes an objective, side-by-side comparison across the requested strategies
        under identical market assumptions.
        """
        if not clean_points or len(clean_points) < 2:
            raise InsufficientHistoricalDataError(
                f"Strategy comparison requires at least 2 historical data points, found {len(clean_points) if clean_points else 0}."
            )

        # 1. Validate common backtest parameters
        alloc_val = request.allocation_fraction if request.allocation_fraction is not None else request.allocation
        cap, fee, alloc = self._validate_common_backtest_params(
            initial_capital=request.initial_capital,
            transaction_cost_rate=request.transaction_cost_rate,
            allocation=alloc_val,
        )

        # 2. Determine target strategies
        target_strats = request.strategies or self.supported_strategies
        if not target_strats:
            raise InvalidComparisonRequestError("Strategies list cannot be empty.")

        for strat in target_strats:
            if strat not in self.supported_strategies:
                raise UnsupportedStrategyError(strat, self.supported_strategies)

        # 3. Calculate baseline Buy & Hold benchmark once for the shared dataset
        benchmark = backtesting_service.calculate_benchmark(
            clean_points=clean_points,
            initial_capital=cap,
            transaction_cost_rate=fee,
        )
        benchmark_return = benchmark.total_return_pct

        # 4. Simulate each strategy using identical parameters
        comparison_results: List[StrategyComparisonItem] = []

        for strat_name in target_strats:
            strat_params = request.strategy_configs.get(strat_name, {}) if request.strategy_configs else {}

            # Generate signals
            strat_signals, active_params = strategy_service.generate_signals(
                strategy_name=strat_name,
                clean_points=clean_points,
                params=strat_params,
            )

            # Convert to generic Step 8 SignalPoint list
            generic_signals = strategy_service.to_generic_signals(strat_signals)

            # Run Step 8 simulation
            bt_req = BacktestRequest(
                initial_capital=cap,
                transaction_cost_rate=fee,
                allocation_fraction=alloc,
                signals=generic_signals,
            )

            bt_res = backtesting_service.run_simulation(
                asset=asset_name,
                symbol=symbol,
                clean_points=clean_points,
                request=bt_req,
                source=source,
            )

            perf = bt_res.performance
            total_ret = perf.total_return_pct
            excess_ret = round(total_ret - benchmark_return, 4)
            max_dd = perf.maximum_drawdown_pct or 0.0

            item = StrategyComparisonItem(
                strategy=strat_name,
                parameters=active_params,
                initial_capital=perf.initial_capital,
                final_portfolio_value=perf.final_portfolio_value,
                total_return=total_ret,
                total_trades=perf.total_trades,
                number_of_trades=perf.total_trades,
                winning_trades=perf.winning_trades,
                losing_trades=perf.losing_trades,
                win_rate_pct=perf.win_rate_pct,
                maximum_drawdown=max_dd,
                max_drawdown=max_dd,
                sharpe_ratio=perf.sharpe_ratio,
                total_fees_paid=perf.total_fees_paid,
                benchmark_return=benchmark_return,
                excess_return_vs_benchmark=excess_ret,
            )
            comparison_results.append(item)

        start_date = clean_points[0].timestamp if clean_points else None
        end_date = clean_points[-1].timestamp if clean_points else None

        return StrategyComparisonResponse(
            asset=asset_name,
            symbol=symbol,
            source=source,
            data_status="calculated",
            execution_model="Next-Observation (Signal at t executes at t+1 at P_{t+1})",
            observation_count=len(clean_points),
            start_date=start_date,
            end_date=end_date,
            benchmark=benchmark,
            benchmark_buy_and_hold=benchmark,
            strategies=comparison_results,
        )

    def analyze_robustness(
        self,
        clean_points: List[CleanHistoricalPoint],
        request: RobustnessAnalysisRequest,
        asset_name: str,
        symbol: str,
        source: str = "Twelve Data",
    ) -> RobustnessAnalysisResponse:
        """
        Executes controlled parameter sensitivity testing over a bounded discrete grid
        for a specified strategy.
        """
        if not clean_points or len(clean_points) < 2:
            raise InsufficientHistoricalDataError(
                f"Robustness analysis requires at least 2 historical data points, found {len(clean_points) if clean_points else 0}."
            )

        strategy_name = request.strategy.strip().lower()
        if strategy_name not in self.supported_strategies:
            raise UnsupportedStrategyError(strategy_name, self.supported_strategies)

        # 1. Validate common backtest parameters
        alloc_val = request.allocation_fraction if request.allocation_fraction is not None else request.allocation
        cap, fee, alloc = self._validate_common_backtest_params(
            initial_capital=request.initial_capital,
            transaction_cost_rate=request.transaction_cost_rate,
            allocation=alloc_val,
        )

        # 2. Validate parameter grid structure
        grid = request.parameter_grid
        if not grid:
            raise InvalidRobustnessParameterError(
                "parameter_grid must be a non-empty dictionary mapping parameter names to lists of values."
            )

        combinations = self._generate_and_validate_parameter_combinations(strategy_name, grid)

        if not combinations:
            raise InvalidRobustnessParameterError(
                f"No valid parameter combinations could be formed from parameter_grid for strategy '{strategy_name}'."
            )

        if len(combinations) > MAX_ROBUSTNESS_COMBINATIONS:
            raise InvalidRobustnessParameterError(
                f"Parameter grid generated {len(combinations)} combinations, exceeding the maximum allowed limit of {MAX_ROBUSTNESS_COMBINATIONS}."
            )

        # 3. Calculate baseline Buy & Hold benchmark once
        benchmark = backtesting_service.calculate_benchmark(
            clean_points=clean_points,
            initial_capital=cap,
            transaction_cost_rate=fee,
        )
        benchmark_return = benchmark.total_return_pct

        # 4. Evaluate each parameter combination
        results: List[RobustnessCombinationResult] = []

        for param_dict in combinations:
            # Generate signals
            strat_signals, active_params = strategy_service.generate_signals(
                strategy_name=strategy_name,
                clean_points=clean_points,
                params=param_dict,
            )

            # Convert to generic signals
            generic_signals = strategy_service.to_generic_signals(strat_signals)

            # Run Step 8 simulation
            bt_req = BacktestRequest(
                initial_capital=cap,
                transaction_cost_rate=fee,
                allocation_fraction=alloc,
                signals=generic_signals,
            )

            bt_res = backtesting_service.run_simulation(
                asset=asset_name,
                symbol=symbol,
                clean_points=clean_points,
                request=bt_req,
                source=source,
            )

            perf = bt_res.performance
            total_ret = perf.total_return_pct
            excess_ret = round(total_ret - benchmark_return, 4)
            max_dd = perf.maximum_drawdown_pct or 0.0

            comb_result = RobustnessCombinationResult(
                strategy=strategy_name,
                parameters=active_params,
                initial_capital=perf.initial_capital,
                final_portfolio_value=perf.final_portfolio_value,
                total_return=total_ret,
                total_trades=perf.total_trades,
                number_of_trades=perf.total_trades,
                maximum_drawdown=max_dd,
                max_drawdown=max_dd,
                sharpe_ratio=perf.sharpe_ratio,
                total_fees_paid=perf.total_fees_paid,
                benchmark_return=benchmark_return,
                excess_return_vs_benchmark=excess_ret,
            )
            results.append(comb_result)

        start_date = clean_points[0].timestamp if clean_points else None
        end_date = clean_points[-1].timestamp if clean_points else None

        return RobustnessAnalysisResponse(
            asset=asset_name,
            symbol=symbol,
            strategy=strategy_name,
            source=source,
            data_status="calculated",
            execution_model="Next-Observation (Signal at t executes at t+1 at P_{t+1})",
            observation_count=len(clean_points),
            start_date=start_date,
            end_date=end_date,
            benchmark=benchmark,
            benchmark_buy_and_hold=benchmark,
            total_combinations_tested=len(results),
            results=results,
        )

    def _generate_and_validate_parameter_combinations(
        self, strategy_name: str, grid: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validates individual parameter values and builds valid combinations.
        Rejects invalid parameters or empty sets with HTTP 400.
        """
        # Ensure all values in grid are non-empty lists
        for k, v in grid.items():
            if not isinstance(v, list):
                raise InvalidRobustnessParameterError(
                    f"Parameter '{k}' in parameter_grid must be a list of values, got {type(v).__name__}."
                )
            if len(v) == 0:
                raise InvalidRobustnessParameterError(
                    f"Parameter '{k}' list in parameter_grid cannot be empty."
                )

        if strategy_name == "sma_crossover":
            if "short_period" not in grid or "long_period" not in grid:
                raise InvalidRobustnessParameterError(
                    "parameter_grid for 'sma_crossover' must specify both 'short_period' and 'long_period' lists."
                )

            # Validate each value
            short_vals = []
            for val in grid["short_period"]:
                try:
                    ival = int(val)
                    if ival < 1:
                        raise ValueError()
                    short_vals.append(ival)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"short_period values must be integers >= 1, got {val}."
                    )

            long_vals = []
            for val in grid["long_period"]:
                try:
                    ival = int(val)
                    if ival < 2:
                        raise ValueError()
                    long_vals.append(ival)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"long_period values must be integers >= 2, got {val}."
                    )

            # Generate pairs where short < long
            combinations = []
            for s, l in itertools.product(short_vals, long_vals):
                if s < l:
                    combinations.append({"short_period": s, "long_period": l})

            if not combinations:
                raise InvalidRobustnessParameterError(
                    "No valid parameter combinations where short_period < long_period could be generated."
                )

            return combinations

        elif strategy_name == "ema_trend":
            if "ema_period" not in grid:
                raise InvalidRobustnessParameterError(
                    "parameter_grid for 'ema_trend' must specify 'ema_period' list."
                )

            ema_vals = []
            for val in grid["ema_period"]:
                try:
                    ival = int(val)
                    if ival < 1:
                        raise ValueError()
                    ema_vals.append(ival)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"ema_period values must be integers >= 1, got {val}."
                    )

            return [{"ema_period": p} for p in ema_vals]

        elif strategy_name == "momentum":
            if "lookback" not in grid:
                raise InvalidRobustnessParameterError(
                    "parameter_grid for 'momentum' must specify 'lookback' list."
                )

            lookback_vals = []
            for val in grid["lookback"]:
                try:
                    ival = int(val)
                    if ival < 1:
                        raise ValueError()
                    lookback_vals.append(ival)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"lookback values must be integers >= 1, got {val}."
                    )

            return [{"lookback": lb} for lb in lookback_vals]

        elif strategy_name == "mean_reversion":
            if "lookback" not in grid or "entry_threshold" not in grid:
                raise InvalidRobustnessParameterError(
                    "parameter_grid for 'mean_reversion' must specify both 'lookback' and 'entry_threshold' lists."
                )

            lb_vals = []
            for val in grid["lookback"]:
                try:
                    ival = int(val)
                    if ival < 2:
                        raise ValueError()
                    lb_vals.append(ival)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"lookback values for mean_reversion must be integers >= 2, got {val}."
                    )

            thresh_vals = []
            for val in grid["entry_threshold"]:
                try:
                    fval = float(val)
                    if fval <= 0.0:
                        raise ValueError()
                    thresh_vals.append(fval)
                except (ValueError, TypeError):
                    raise InvalidRobustnessParameterError(
                        f"entry_threshold values must be positive floats > 0.0, got {val}."
                    )

            combinations = []
            for lb, th in itertools.product(lb_vals, thresh_vals):
                combinations.append({"lookback": lb, "entry_threshold": th})

            return combinations

        else:
            raise UnsupportedStrategyError(strategy_name, self.supported_strategies)


strategy_comparison_service = StrategyComparisonService()
