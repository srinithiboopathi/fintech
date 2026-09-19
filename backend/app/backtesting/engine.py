"""
Backtesting Engine for QUANTLAB (Phase 7).
Executes realistic portfolio simulations with next-session open fills, transaction costs,
and institutional performance attribution.
"""
from typing import Optional, Dict, Any
import pandas as pd

from backend.app.services.market_service import market_service
from backend.app.strategies.enums import StrategyType
from backend.app.strategies.sma_crossover import calculate_sma_crossover_signals
from backend.app.strategies.ema_trend import calculate_ema_trend_signals
from backend.app.strategies.momentum import calculate_momentum_signals
from backend.app.strategies.mean_reversion import calculate_mean_reversion_signals

from backend.app.backtesting.validation import (
    validate_backtest_parameters,
    validate_backtest_dates,
    validate_strategy_config,
)
from backend.app.backtesting.portfolio import PortfolioTracker
from backend.app.backtesting.performance import calculate_portfolio_performance
from backend.app.backtesting.benchmark import (
    calculate_buy_and_hold_benchmark,
    calculate_strategy_comparison,
)


class BacktestEngine:
    """Deterministic, pure-python backtesting engine."""

    def __init__(self):
        self.market_service = market_service

    def run(
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
        """
        Runs an end-to-end backtest simulation for an asset and quantitative strategy.
        """
        validate_backtest_parameters(
            initial_capital=initial_capital,
            position_size=position_size,
            transaction_cost=transaction_cost,
            risk_free_rate=risk_free_rate,
        )
        validate_backtest_dates(start_date, end_date)
        validated_params = validate_strategy_config(strategy, strategy_parameters)

        canonical = self.market_service.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(
                f"Asset '{asset}' is not recognized. Supported assets: Gold, Bitcoin, NVIDIA."
            )

        # 1. Load full historical dataset
        df = self.market_service._get_dataset(canonical)
        sorted_df = df.sort_values("date", ascending=True).reset_index(drop=True)

        # 2. Compute strategy signals across full history to prevent warm-up distortion
        prices = sorted_df["close"]
        strat_key = strategy.strip().lower().replace("-", "_")

        if strat_key == StrategyType.SMA_CROSSOVER.value:
            sig_df = calculate_sma_crossover_signals(
                prices,
                fast_period=validated_params["fast_period"],
                slow_period=validated_params["slow_period"],
            )
        elif strat_key == StrategyType.EMA_TREND.value:
            sig_df = calculate_ema_trend_signals(
                prices,
                short_period=validated_params["short_period"],
                long_period=validated_params["long_period"],
            )
        elif strat_key == StrategyType.MOMENTUM.value:
            sig_df = calculate_momentum_signals(
                prices,
                lookback=validated_params["lookback"],
            )
        elif strat_key == StrategyType.MEAN_REVERSION.value:
            sig_df = calculate_mean_reversion_signals(
                prices,
                window=validated_params["window"],
                threshold=validated_params["threshold"],
            )
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

        sorted_df["signal"] = sig_df["signal"]

        # 3. Filter to requested backtest date range
        sim_df = sorted_df.copy()
        if start_date:
            sim_df = sim_df[sim_df["date"] >= start_date]
        if end_date:
            sim_df = sim_df[sim_df["date"] <= end_date]

        sim_df = sim_df.reset_index(drop=True)
        if sim_df.empty:
            raise ValueError(
                f"No market data available for {canonical} in date range {start_date} to {end_date}."
            )

        # 4. Run portfolio simulation loop
        tracker = PortfolioTracker(
            initial_capital=initial_capital,
            position_size=position_size,
            transaction_cost=transaction_cost,
            asset=canonical,
            strategy=strat_key,
        )

        n = len(sim_df)
        for i in range(n):
            current_date = str(sim_df["date"].iloc[i])
            open_price = float(sim_df["open"].iloc[i])
            if open_price <= 0:
                open_price = float(sim_df["close"].iloc[i])
            close_price = float(sim_df["close"].iloc[i])
            signal = str(sim_df["signal"].iloc[i])

            # Morning: Execute any orders triggered by previous session's close
            tracker.process_morning_execution(date=current_date, open_price=open_price)

            # Evening: Mark portfolio to market at close
            tracker.process_evening_mark_to_market(date=current_date, close_price=close_price)

            # Evening: Evaluate today's closing signal for tomorrow's open
            tracker.evaluate_signal_for_next_session(signal=signal)

        # 5. Extract results
        final_close = float(sim_df["close"].iloc[-1])
        open_pos = tracker.get_open_position_summary(final_close=final_close)

        strategy_perf = calculate_portfolio_performance(
            equity_curve=tracker.equity_curve,
            trades=tracker.trades,
            initial_capital=initial_capital,
            asset=canonical,
            risk_free_rate=risk_free_rate,
        )

        # 6. Calculate Buy-and-Hold benchmark over identical date window
        benchmark_res = calculate_buy_and_hold_benchmark(
            df=sim_df,
            initial_capital=initial_capital,
            transaction_cost=transaction_cost,
            asset=canonical,
            risk_free_rate=risk_free_rate,
        )

        benchmark_perf = {
            "initial_capital": benchmark_res["initial_capital"],
            "final_value": benchmark_res["final_value"],
            "total_return": benchmark_res["total_return"],
            "annualized_return": benchmark_res["annualized_return"],
            "annualized_volatility": benchmark_res["annualized_volatility"],
            "sharpe_ratio": benchmark_res["sharpe_ratio"],
            "maximum_drawdown": benchmark_res["maximum_drawdown"],
        }

        comparison = calculate_strategy_comparison(
            strategy_perf=strategy_perf,
            benchmark_perf=benchmark_perf,
        )

        equity_curve_dicts = [pt.to_dict() for pt in tracker.equity_curve]
        trade_dicts = [t.to_dict() for t in tracker.trades]

        return {
            "backtest": {
                "asset": canonical,
                "start_date": str(sim_df["date"].iloc[0]),
                "end_date": str(sim_df["date"].iloc[-1]),
                "records": len(sim_df),
                "initial_capital": initial_capital,
                "position_size": position_size,
                "transaction_cost": transaction_cost,
                "risk_free_rate": risk_free_rate,
            },
            "strategy": {
                "name": strat_key,
                "parameters": validated_params,
            },
            "performance": strategy_perf,
            "benchmark": benchmark_perf,
            "comparison": comparison,
            "equity_curve": equity_curve_dicts,
            "trades": trade_dicts,
            "open_position": open_pos,
        }


# Global singleton backtest engine instance
backtest_engine = BacktestEngine()
