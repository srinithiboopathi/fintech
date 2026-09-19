"""
Descriptive Range and Summary Aggregator for Robustness Results.
"""
from typing import List, Dict, Any
from backend.app.robustness.models import RobustnessResult


def summarize_robustness_results(
    results: List[RobustnessResult],
    transaction_costs: List[float],
    periods: List[Dict[str, Any]],
    parameter_grid: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes objective descriptive metric ranges across all tested configurations.
    Does NOT rank, score, or declare 'best' parameters.
    """
    if not results:
        return {
            "total_configurations": 0,
            "parameter_ranges": parameter_grid,
            "transaction_costs": transaction_costs,
            "periods_tested": periods,
            "metrics_ranges": {
                "return_range": {"min": 0.0, "max": 0.0},
                "sharpe_range": {"min": 0.0, "max": 0.0},
                "drawdown_range": {"min": 0.0, "max": 0.0},
                "trades_range": {"min": 0, "max": 0},
                "win_rate_range": {"min": 0.0, "max": 0.0},
            },
        }

    returns = [r.total_return for r in results]
    sharpes = [r.sharpe_ratio for r in results]
    drawdowns = [r.maximum_drawdown for r in results]
    trades = [r.number_of_trades for r in results]
    win_rates = [r.win_rate for r in results]

    return {
        "total_configurations": len(results),
        "parameter_ranges": parameter_grid,
        "transaction_costs": sorted(list(set(transaction_costs))),
        "periods_tested": periods,
        "metrics_ranges": {
            "return_range": {
                "min": round(min(returns), 6),
                "max": round(max(returns), 6),
            },
            "sharpe_range": {
                "min": round(min(sharpes), 6),
                "max": round(max(sharpes), 6),
            },
            "drawdown_range": {
                "min": round(min(drawdowns), 6),
                "max": round(max(drawdowns), 6),
            },
            "trades_range": {
                "min": min(trades),
                "max": max(trades),
            },
            "win_rate_range": {
                "min": round(min(win_rates), 4),
                "max": round(max(win_rates), 4),
            },
        },
    }
