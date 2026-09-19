"""
backend/app/services/backtesting.py

Strategy-Agnostic Quantitative Backtesting Engine.
Simulates portfolio execution, tracks cash/position accounting, computes risk/return statistics,
and benchmarks against Buy-and-Hold strictly from cleaned historical market records.

Mathematical & Causal Specifications:
1. Strategy-Agnostic Execution:
   - Ingests generic signals: BUY, SELL, HOLD.
   - Does not embed or require specific technical indicators.

2. Next-Observation Execution (Zero Look-Ahead Bias):
   - A signal generated at observation t is executed at observation t + 1 at close price P_(t+1).
   - Past trades and equity values remain invariant to future price modifications.

3. Position Sizing & Cash Invariants:
   - On BUY: Target investment = cash * allocation_fraction.
   - Sizing strictly accounts for transaction fees: Quantity = target_cash / (Price * (1 + fee_rate)).
   - Enforces cash >= 0 at all times; no borrowing or leverage.
   - On SELL: Liquidates entire accumulated position (no short selling).

4. Portfolio Accounting:
   - Portfolio Value_t = Cash_t + (Position_t * Close_Price_t)
   - Daily Return_t = ((Portfolio Value_t / Portfolio Value_(t-1)) - 1) * 100

5. Benchmark Comparison:
   - Buy-and-Hold on the same asset, allocated at inception with equivalent transaction cost.
"""

import math
from typing import List, Dict, Optional, Tuple, Any

from app.models.schemas import (
    CleanHistoricalPoint,
    SignalPoint,
    BacktestRequest,
    TradeRecord,
    PortfolioObservation,
    BenchmarkPoint,
    BenchmarkResults,
    BacktestPerformance,
    BacktestResponse,
)
from app.services.risk_analysis import calculate_drawdown, calculate_sharpe_ratio
from app.utils.exceptions import InvalidBacktestParameterError


class BacktestingEngine:
    """
    Production-grade strategy-agnostic backtesting simulation engine.
    """

    def validate_inputs(
        self,
        clean_points: List[CleanHistoricalPoint],
        initial_capital: float,
        transaction_cost_rate: float,
        allocation_fraction: float,
        signals: Optional[List[SignalPoint]] = None
    ) -> None:
        """
        Validates backtest inputs and parameters.
        Raises InvalidBacktestParameterError (HTTP 400) on invalid inputs.
        """
        if not clean_points:
            raise InvalidBacktestParameterError("Historical market data is empty.")

        # Validate initial_capital
        try:
            cap = float(initial_capital)
            if cap <= 0.0 or not math.isfinite(cap):
                raise InvalidBacktestParameterError("initial_capital must be a positive number greater than 0.")
        except (ValueError, TypeError):
            raise InvalidBacktestParameterError("initial_capital must be a valid numeric value.")

        # Validate transaction_cost_rate
        try:
            cost = float(transaction_cost_rate)
            if cost < 0.0 or not math.isfinite(cost):
                raise InvalidBacktestParameterError("transaction_cost_rate must be a non-negative number (>= 0).")
        except (ValueError, TypeError):
            raise InvalidBacktestParameterError("transaction_cost_rate must be a valid numeric value.")

        # Validate allocation_fraction
        try:
            alloc = float(allocation_fraction)
            if alloc <= 0.0 or alloc > 1.0 or not math.isfinite(alloc):
                raise InvalidBacktestParameterError("allocation_fraction must be a number greater than 0 and at most 1.0.")
        except (ValueError, TypeError):
            raise InvalidBacktestParameterError("allocation_fraction must be a valid numeric value.")

        # Validate signals sequence
        if signals is not None and len(signals) == 0:
            raise InvalidBacktestParameterError("Trading signals sequence cannot be empty.")

        if signals:
            prev_ts = None
            valid_signals = {"BUY", "SELL", "HOLD"}
            for i, s in enumerate(signals):
                sig_str = str(s.signal).strip().upper()
                if sig_str not in valid_signals:
                    raise InvalidBacktestParameterError(
                        f"Invalid signal '{s.signal}' at index {i}. Supported signals: BUY, SELL, HOLD."
                    )
                ts = str(s.timestamp).strip()
                if not ts:
                    raise InvalidBacktestParameterError(f"Signal at index {i} has empty timestamp.")
                if prev_ts is not None and ts < prev_ts:
                    raise InvalidBacktestParameterError(
                        f"Signals must be chronologically ordered. Discrepancy at index {i}: '{ts}' < '{prev_ts}'."
                    )
                prev_ts = ts

    def calculate_benchmark(
        self,
        clean_points: List[CleanHistoricalPoint],
        initial_capital: float,
        transaction_cost_rate: float
    ) -> BenchmarkResults:
        """
        Computes Buy-and-Hold benchmark equity curve on the same historical asset.
        Buys at first available observation price P_0 and holds to termination.
        """
        p0 = clean_points[0].close
        # Sizing with transaction cost: Q = Capital / (P_0 * (1 + fee_rate))
        cost_multiplier = 1.0 + transaction_cost_rate
        qty_bmk = initial_capital / (p0 * cost_multiplier)
        initial_trade_val = qty_bmk * p0
        initial_fee = initial_trade_val * transaction_cost_rate
        cash_bmk = initial_capital - (initial_trade_val + initial_fee)

        equity_curve: List[BenchmarkPoint] = []
        for pt in clean_points:
            p = pt.close
            val = cash_bmk + (qty_bmk * p)
            ret_pct = ((val - initial_capital) / initial_capital) * 100.0
            equity_curve.append(
                BenchmarkPoint(
                    timestamp=pt.timestamp,
                    portfolio_value=round(val, 4),
                    total_return_pct=round(ret_pct, 4)
                )
            )

        final_val = equity_curve[-1].portfolio_value if equity_curve else initial_capital
        total_ret = ((final_val - initial_capital) / initial_capital) * 100.0

        return BenchmarkResults(
            benchmark_name="Buy & Hold",
            initial_value=round(initial_capital, 4),
            final_value=round(final_val, 4),
            total_return_pct=round(total_ret, 4),
            equity_curve=equity_curve
        )

    def run_simulation(
        self,
        asset: str,
        symbol: str,
        clean_points: List[CleanHistoricalPoint],
        request: Optional[BacktestRequest] = None,
        initial_capital: Optional[float] = None,
        transaction_cost_rate: Optional[float] = None,
        allocation_fraction: Optional[float] = None,
        signals: Optional[List[SignalPoint]] = None,
        source: str = "Twelve Data",
        annualization_factor: int = 252,
        precision: int = 4
    ) -> BacktestResponse:
        """
        Simulates causal portfolio execution using Next-Observation Execution:
        Signal at time t executes at time t + 1 at close price P_(t+1).
        """
        if request is not None:
            if initial_capital is None:
                initial_capital = request.initial_capital
            if transaction_cost_rate is None:
                transaction_cost_rate = request.transaction_cost_rate
            if allocation_fraction is None:
                allocation_fraction = request.allocation_fraction
            if signals is None:
                signals = request.signals

        cap = 100000.0 if initial_capital is None else initial_capital
        cost_rate = 0.001 if transaction_cost_rate is None else transaction_cost_rate
        alloc = 1.0 if allocation_fraction is None else allocation_fraction

        self.validate_inputs(
            clean_points=clean_points,
            initial_capital=cap,
            transaction_cost_rate=cost_rate,
            allocation_fraction=alloc,
            signals=signals
        )

        initial_capital = float(cap)
        transaction_cost_rate = float(cost_rate)
        allocation_fraction = float(alloc)

        # Build signals lookup by full timestamp and date (YYYY-MM-DD)
        signals_map: Dict[str, str] = {}
        if signals:
            for s in signals:
                sig_upper = s.signal.strip().upper()
                signals_map[s.timestamp] = sig_upper
                signals_map[s.timestamp[:10]] = sig_upper

        n = len(clean_points)
        cash = float(initial_capital)
        position = 0.0
        avg_entry_price = 0.0
        total_fees = 0.0
        winning_trades = 0
        losing_trades = 0
        trade_id = 1

        trades: List[TradeRecord] = []
        equity_curve: List[PortfolioObservation] = []
        pending_signal: Optional[str] = None

        # Observation 0: Initialization
        p0 = clean_points[0].close
        ts0 = clean_points[0].timestamp
        s0 = signals_map.get(ts0) or signals_map.get(ts0[:10]) or "HOLD"

        equity_curve.append(
            PortfolioObservation(
                timestamp=ts0,
                close_price=round(p0, precision),
                signal=s0,
                executed_action="NONE",
                cash=round(cash, precision),
                position_quantity=0.0,
                position_market_value=0.0,
                transaction_cost=0.0,
                portfolio_value=round(cash, precision),
                portfolio_return_pct=0.0
            )
        )
        pending_signal = s0

        # Observations 1 to N - 1: Causal execution loop
        for t in range(1, n):
            pt = clean_points[t]
            curr_price = pt.close
            curr_ts = pt.timestamp
            curr_signal = signals_map.get(curr_ts) or signals_map.get(curr_ts[:10]) or "HOLD"

            executed_action = "NONE"
            fee = 0.0

            # Execute pending signal from observation t - 1
            if pending_signal == "BUY":
                if cash > 0.0 and curr_price > 0.0:
                    invest_cash = cash * allocation_fraction
                    cost_multiplier = 1.0 + transaction_cost_rate
                    quantity = invest_cash / (curr_price * cost_multiplier)
                    trade_value = quantity * curr_price
                    fee = trade_value * transaction_cost_rate
                    spent = trade_value + fee

                    cash -= spent
                    if cash < 0.0:
                        cash = 0.0  # Guard against micro-floating-point negative

                    new_position = position + quantity
                    # Weighted average entry price
                    avg_entry_price = (
                        ((position * avg_entry_price) + trade_value) / new_position
                        if new_position > 0
                        else curr_price
                    )
                    position = new_position
                    executed_action = "BUY"
                    total_fees += fee

                    trades.append(
                        TradeRecord(
                            trade_id=trade_id,
                            timestamp=curr_ts,
                            side="BUY",
                            price=round(curr_price, precision),
                            quantity=round(quantity, 6),
                            trade_value=round(trade_value, precision),
                            transaction_cost=round(fee, precision),
                            resulting_cash=round(cash, precision),
                            resulting_position=round(position, 6),
                            pnl=None,
                            pnl_percent=None
                        )
                    )
                    trade_id += 1

            elif pending_signal == "SELL":
                if position > 0.0 and curr_price > 0.0:
                    quantity = position
                    trade_value = quantity * curr_price
                    fee = trade_value * transaction_cost_rate
                    net_proceeds = trade_value - fee

                    realized_pnl = net_proceeds - (quantity * avg_entry_price)
                    realized_pnl_pct = (
                        ((net_proceeds / (quantity * avg_entry_price)) - 1.0) * 100.0
                        if avg_entry_price > 0
                        else 0.0
                    )

                    cash += net_proceeds
                    position = 0.0
                    avg_entry_price = 0.0
                    executed_action = "SELL"
                    total_fees += fee

                    if realized_pnl > 0:
                        winning_trades += 1
                    elif realized_pnl < 0:
                        losing_trades += 1

                    trades.append(
                        TradeRecord(
                            trade_id=trade_id,
                            timestamp=curr_ts,
                            side="SELL",
                            price=round(curr_price, precision),
                            quantity=round(quantity, 6),
                            trade_value=round(trade_value, precision),
                            transaction_cost=round(fee, precision),
                            resulting_cash=round(cash, precision),
                            resulting_position=0.0,
                            pnl=round(realized_pnl, precision),
                            pnl_percent=round(realized_pnl_pct, precision)
                        )
                    )
                    trade_id += 1

            elif pending_signal == "HOLD":
                executed_action = "HOLD"

            # Portfolio Valuation at time t
            mkt_val = position * curr_price
            port_val = cash + mkt_val
            prev_val = equity_curve[t - 1].portfolio_value
            daily_ret = (
                ((port_val - prev_val) / prev_val) * 100.0
                if prev_val > 0
                else 0.0
            )

            equity_curve.append(
                PortfolioObservation(
                    timestamp=curr_ts,
                    close_price=round(curr_price, precision),
                    signal=curr_signal,
                    executed_action=executed_action,
                    cash=round(cash, precision),
                    position_quantity=round(position, 6),
                    position_market_value=round(mkt_val, precision),
                    transaction_cost=round(fee, precision),
                    portfolio_value=round(port_val, precision),
                    portfolio_return_pct=round(daily_ret, precision)
                )
            )

            # Signal generated at observation t becomes pending for execution at t + 1
            pending_signal = curr_signal

        # Benchmark calculation
        benchmark = self.calculate_benchmark(
            clean_points=clean_points,
            initial_capital=initial_capital,
            transaction_cost_rate=transaction_cost_rate
        )

        # Performance calculations
        final_val = equity_curve[-1].portfolio_value if equity_curve else initial_capital
        tot_ret = ((final_val - initial_capital) / initial_capital) * 100.0
        tot_trades = len(trades)
        closed_trades = winning_trades + losing_trades
        win_rate = (
            round((winning_trades / closed_trades) * 100.0, precision)
            if closed_trades > 0
            else None
        )

        # Risk metrics integration: Maximum Drawdown & Sharpe Ratio
        port_values = [obs.portfolio_value for obs in equity_curve]
        port_timestamps = [obs.timestamp for obs in equity_curve]
        _, max_dd, max_dd_ts = calculate_drawdown(port_values, port_timestamps, precision=precision)

        daily_returns = [obs.portfolio_return_pct for obs in equity_curve]
        sharpe = calculate_sharpe_ratio(
            returns=daily_returns,
            risk_free_rate=0.0,
            annualization_factor=annualization_factor,
            precision=precision
        )

        performance = BacktestPerformance(
            initial_capital=round(initial_capital, precision),
            final_portfolio_value=round(final_val, precision),
            total_return_pct=round(tot_ret, precision),
            total_trades=tot_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate_pct=win_rate,
            total_fees_paid=round(total_fees, precision),
            maximum_drawdown_pct=max_dd,
            maximum_drawdown_timestamp=max_dd_ts,
            sharpe_ratio=sharpe
        )

        return BacktestResponse(
            asset=asset,
            symbol=symbol,
            source=source,
            data_status="calculated",
            execution_model="Next-Observation (Signal at t executes at t+1)",
            performance=performance,
            benchmark=benchmark,
            trade_history=trades,
            equity_curve=equity_curve
        )


backtesting_service = BacktestingEngine()
