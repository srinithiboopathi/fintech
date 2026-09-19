import uuid
from typing import List, Dict, Any, Optional
from app.backtesting.transaction_costs import TransactionCostModel
from app.backtesting.position_sizing import PositionSizer
from app.backtesting.execution import ExecutionSimulator
from app.backtesting.portfolio import PortfolioTracker
from app.quant.returns import ReturnMetrics
from app.quant.volatility import VolatilityMetrics
from app.quant.sharpe import RiskAdjustedMetrics
from app.quant.drawdown import DrawdownAnalysis

class BacktestEngine:
    """
    Quantitative Event-Driven & Vectorized Backtesting Engine
    Execution Assumption:
    - Signals generated at bar T (using information available at time T close)
    - Orders filled at bar T close / execution price adjusted for slippage and commission
    - Strict avoidance of look-ahead bias
    """
    def __init__(
        self,
        strategy,
        bars: List[Dict[str, Any]],
        initial_capital: float = 100000.0,
        position_sizing: str = "percent_equity",
        position_size_value: float = 0.95,
        commission_bps: float = 5.0,
        slippage_pct: float = 0.001
    ):
        self.strategy = strategy
        self.bars = bars
        self.initial_capital = initial_capital
        self.position_sizing = position_sizing
        self.position_size_value = position_size_value
        
        self.cost_model = TransactionCostModel(commission_bps, slippage_pct)
        self.exec_sim = ExecutionSimulator(self.cost_model)
        self.portfolio = PortfolioTracker(initial_capital)

    def run(self) -> Dict[str, Any]:
        if not self.bars:
            raise ValueError("No historical price bars provided for backtest.")

        signals = self.strategy.generate_signals(self.bars)
        equity_curve = []
        trades = []
        peak_equity = self.initial_capital
        total_friction_paid = 0.0

        # Benchmark reference
        benchmark_start_price = self.bars[0]["close"]
        benchmark_shares = self.initial_capital / benchmark_start_price if benchmark_start_price > 0 else 1.0

        # Optional risk management stops
        stop_loss_pct = float(self.strategy.params.get("stop_loss_pct", 0.0))
        take_profit_pct = float(self.strategy.params.get("take_profit_pct", 0.0))

        for i in range(len(self.bars)):
            bar = self.bars[i]
            date = bar["date"]
            price = bar["close"]
            sig = signals[i]

            # Check stop loss / take profit if currently holding position
            if self.portfolio.is_invested():
                p_entry = self.portfolio.entry_price
                curr_pnl_pct = (price - p_entry) / p_entry if p_entry > 0 else 0.0
                
                stop_triggered = stop_loss_pct > 0 and curr_pnl_pct <= -stop_loss_pct
                tp_triggered = take_profit_pct > 0 and curr_pnl_pct >= take_profit_pct

                if stop_triggered or tp_triggered or sig == 0:
                    # Execute Exit (SELL)
                    exec_order = self.exec_sim.execute_market_order(
                        symbol=bar.get("symbol", ""),
                        raw_price=price,
                        side="SELL",
                        quantity=self.portfolio.position_qty
                    )
                    total_friction_paid += exec_order["commission"] + exec_order["slippage_cost"]
                    trade_info = self.portfolio.exit_long(
                        date=date,
                        fill_price=exec_order["fill_price"],
                        commission=exec_order["commission"]
                    )
                    trade_info["trade_id"] = f"tr-{uuid.uuid4().hex[:6]}"
                    trade_info["symbol"] = bar.get("symbol", "")
                    trade_info["side"] = "LONG"
                    trade_info["action"] = "SELL"
                    trade_info["date"] = date
                    trade_info["price"] = exec_order["fill_price"]
                    trade_info["quantity"] = trade_info["quantity"]
                    trade_info["portfolio_value"] = round(self.portfolio.cash, 2)
                    trade_info["slippage"] = exec_order["slippage_cost"]
                    trade_info["exit_reason"] = "STOP_LOSS" if stop_triggered else ("TAKE_PROFIT" if tp_triggered else "SIGNAL_REVERSAL")
                    trade_info["duration_days"] = max(1, i - (i - 1))
                    trades.append(trade_info)

            # Check for entry signal (BUY)
            elif sig == 1 and not self.portfolio.is_invested():
                current_equity = self.portfolio.cash
                qty = PositionSizer.calculate_units(
                    method=self.position_sizing,
                    value=self.position_size_value,
                    portfolio_equity=current_equity,
                    price=price
                )
                if qty > 0:
                    exec_order = self.exec_sim.execute_market_order(
                        symbol=bar.get("symbol", ""),
                        raw_price=price,
                        side="BUY",
                        quantity=qty
                    )
                    total_friction_paid += exec_order["commission"] + exec_order["slippage_cost"]
                    self.portfolio.enter_long(
                        date=date,
                        fill_price=exec_order["fill_price"],
                        quantity=exec_order["quantity"],
                        commission=exec_order["commission"]
                    )

            # Record daily equity point
            curr_equity = self.portfolio.total_equity(price)
            if curr_equity > peak_equity:
                peak_equity = curr_equity
            dd_pct = (curr_equity - peak_equity) / peak_equity if peak_equity > 0 else 0.0

            benchmark_equity = benchmark_shares * price

            equity_curve.append({
                "date": date,
                "equity": round(curr_equity, 2),
                "benchmark_equity": round(benchmark_equity, 2),
                "drawdown_pct": round(dd_pct, 4),
                "cash": round(self.portfolio.cash, 2),
                "holdings_value": round(self.portfolio.position_qty * price, 2)
            })

        # Calculate comprehensive quant metrics for strategy
        final_equity = equity_curve[-1]["equity"] if equity_curve else self.initial_capital
        total_return_pct = ((final_equity - self.initial_capital) / self.initial_capital) * 100.0

        daily_equities = [pt["equity"] for pt in equity_curve]
        daily_returns = ReturnMetrics.simple_returns(daily_equities)
        num_days = len(self.bars)

        cagr_val = ReturnMetrics.cagr(self.initial_capital, final_equity, num_days) * 100.0
        ann_vol = VolatilityMetrics.annualized_volatility(daily_returns) * 100.0
        sharpe = RiskAdjustedMetrics.sharpe_ratio(daily_returns)
        sortino = RiskAdjustedMetrics.sortino_ratio(daily_returns)
        
        underwater, max_dd, max_dd_len = DrawdownAnalysis.calculate_drawdowns(daily_equities)
        calmar = RiskAdjustedMetrics.calmar_ratio(cagr_val / 100.0, max_dd)

        # Calculate Buy and Hold Benchmark Metrics
        bench_equities = [pt["benchmark_equity"] for pt in equity_curve]
        bench_returns = ReturnMetrics.simple_returns(bench_equities)
        bench_final = bench_equities[-1] if bench_equities else self.initial_capital
        bench_total_return = ((bench_final - self.initial_capital) / self.initial_capital) * 100.0
        bench_cagr = ReturnMetrics.cagr(self.initial_capital, bench_final, num_days) * 100.0
        bench_vol = VolatilityMetrics.annualized_volatility(bench_returns) * 100.0
        bench_sharpe = RiskAdjustedMetrics.sharpe_ratio(bench_returns)
        _, bench_max_dd, _ = DrawdownAnalysis.calculate_drawdowns(bench_equities)

        # Trade analytics
        total_t = len(trades)
        wins = [t for t in trades if t["pnl_usd"] > 0]
        losses = [t for t in trades if t["pnl_usd"] <= 0]
        win_rate = (len(wins) / total_t * 100.0) if total_t > 0 else 0.0

        gross_profit = sum(t["pnl_usd"] for t in wins)
        gross_loss = abs(sum(t["pnl_usd"] for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (5.0 if gross_profit > 0 else 1.0)

        pnls = [t["pnl_pct"] for t in trades]
        avg_pnl = (sum(pnls) / len(pnls)) if pnls else 0.0
        max_win = max(pnls) if pnls else 0.0
        max_loss = min(pnls) if pnls else 0.0

        benchmark_comparison = {
            "strategy": {
                "initial_capital": self.initial_capital,
                "final_value": round(final_equity, 2),
                "total_return_pct": round(total_return_pct, 2),
                "cagr": round(cagr_val, 2),
                "annualized_volatility": round(ann_vol, 2),
                "sharpe_ratio": round(sharpe, 2),
                "max_drawdown_pct": round(max_dd * 100.0, 2),
                "number_of_trades": total_t
            },
            "buy_and_hold": {
                "initial_capital": self.initial_capital,
                "final_value": round(bench_final, 2),
                "total_return_pct": round(bench_total_return, 2),
                "cagr": round(bench_cagr, 2),
                "annualized_volatility": round(bench_vol, 2),
                "sharpe_ratio": round(bench_sharpe, 2),
                "max_drawdown_pct": round(bench_max_dd * 100.0, 2),
                "number_of_trades": 1
            },
            "alpha_excess_return_pct": round(total_return_pct - bench_total_return, 2)
        }

        return {
            "run_id": f"run-{uuid.uuid4().hex[:8]}",
            "strategy_id": getattr(self.strategy, "slug", self.strategy.name.lower().replace(" ", "_")),
            "strategy_name": self.strategy.name,
            "symbol": self.bars[0].get("symbol", ""),
            "start_date": self.bars[0]["date"],
            "end_date": self.bars[-1]["date"],
            "initial_capital": self.initial_capital,
            "final_equity": round(final_equity, 2),
            "final_value": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "total_return": round(total_return_pct, 2),
            "benchmark_return_pct": round(bench_total_return, 2),
            "cagr": round(cagr_val, 2),
            "annualized_volatility": round(ann_vol, 2),
            "volatility": round(ann_vol, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "max_drawdown_pct": round(max_dd * 100.0, 2),
            "max_drawdown": round(max_dd * 100.0, 2),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "total_trades": total_t,
            "number_of_trades": total_t,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "avg_trade_pnl_pct": round(avg_pnl, 2),
            "max_win_pct": round(max_win, 2),
            "max_loss_pct": round(max_loss, 2),
            "transaction_cost": round(total_friction_paid, 2),
            "equity_curve": equity_curve,
            "trades": trades,
            "parameters": self.strategy.params,
            "benchmark_comparison": benchmark_comparison
        }
