import random
from typing import List, Dict, Any, Type
from app.quant.drawdown import DrawdownAnalysis
from app.quant.sharpe import RiskAdjustedMetrics
from app.backtesting.engine import BacktestEngine

class RobustnessEngine:
    @staticmethod
    def monte_carlo_simulation(
        daily_returns: List[float],
        initial_capital: float = 100000.0,
        num_simulations: int = 500,
        horizon_days: int = 252,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Bootstrap resampling over historical return distribution to simulate
        future equity growth envelopes and tail-risk confidence intervals.
        """
        random.seed(seed)
        if not daily_returns:
            return {"simulations": [], "percentiles": {}}

        trajectories = []
        max_drawdowns = []
        terminal_values = []
        sharpe_ratios = []

        for _ in range(num_simulations):
            path = [initial_capital]
            sim_rets = []
            curr_equity = initial_capital
            
            for _ in range(horizon_days):
                r = random.choice(daily_returns)
                sim_rets.append(r)
                curr_equity *= (1.0 + r)
                path.append(round(curr_equity, 2))

            trajectories.append(path)
            terminal_values.append(curr_equity)
            _, max_dd, _ = DrawdownAnalysis.calculate_drawdowns(path)
            max_drawdowns.append(max_dd)
            sharpe = RiskAdjustedMetrics.sharpe_ratio(sim_rets)
            sharpe_ratios.append(sharpe)

        terminal_values.sort()
        max_drawdowns.sort()
        sharpe_ratios.sort()

        p5_idx = int(0.05 * num_simulations)
        p50_idx = int(0.50 * num_simulations)
        p95_idx = int(0.95 * num_simulations)

        # Generate median and confidence percentile lines for charting
        time_steps = len(trajectories[0])
        p5_curve = []
        p50_curve = []
        p95_curve = []

        for t in range(time_steps):
            col = sorted([traj[t] for traj in trajectories])
            p5_curve.append(col[p5_idx])
            p50_curve.append(col[p50_idx])
            p95_curve.append(col[p95_idx])

        return {
            "num_simulations": num_simulations,
            "horizon_days": horizon_days,
            "p5_equity_curve": p5_curve,
            "p50_equity_curve": p50_curve,
            "p95_equity_curve": p95_curve,
            "sample_trajectories": trajectories[:15],
            "metrics": {
                "terminal_wealth_p5": round(terminal_values[p5_idx], 2),
                "terminal_wealth_p50": round(terminal_values[p50_idx], 2),
                "terminal_wealth_p95": round(terminal_values[p95_idx], 2),
                "max_drawdown_p5": round(max_drawdowns[p5_idx] * 100.0, 2),
                "max_drawdown_p50": round(max_drawdowns[p50_idx] * 100.0, 2),
                "max_drawdown_p95": round(max_drawdowns[p95_idx] * 100.0, 2),
                "sharpe_p5": round(sharpe_ratios[p5_idx], 2),
                "sharpe_p50": round(sharpe_ratios[p50_idx], 2),
                "sharpe_p95": round(sharpe_ratios[p95_idx], 2)
            }
        }

    @staticmethod
    def parameter_sensitivity(
        strategy_class: Any,
        bars: List[Dict[str, Any]],
        param_grid: List[Dict[str, Any]],
        friction_levels: List[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Tests a strategy across multiple parameter variations and transaction cost schedules
        to verify alpha stability across regimes.
        """
        if friction_levels is None:
            friction_levels = [0.0, 5.0, 15.0] # basis points

        results = []
        for params in param_grid:
            for bps in friction_levels:
                try:
                    strat = strategy_class(params)
                    engine = BacktestEngine(
                        strategy=strat,
                        bars=bars,
                        commission_bps=bps,
                        slippage_pct=0.001
                    )
                    res = engine.run()
                    results.append({
                        "parameters": params,
                        "commission_bps": bps,
                        "total_return_pct": res["total_return_pct"],
                        "sharpe_ratio": res["sharpe_ratio"],
                        "max_drawdown_pct": res["max_drawdown_pct"],
                        "total_trades": res["total_trades"],
                        "profit_factor": res["profit_factor"]
                    })
                except Exception:
                    continue
        return results
