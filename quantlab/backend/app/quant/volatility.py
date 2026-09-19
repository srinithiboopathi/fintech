import math
from typing import List

class VolatilityMetrics:
    @staticmethod
    def annualized_volatility(daily_returns: List[float], trading_days: int = 252) -> float:
        """
        Calculates annualized sample volatility: std(daily_returns) * sqrt(trading_days).
        """
        if len(daily_returns) < 2:
            return 0.0
        mean = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_std = math.sqrt(variance)
        return daily_std * math.sqrt(trading_days)

    @staticmethod
    def downside_volatility(daily_returns: List[float], target_return: float = 0.0, trading_days: int = 252) -> float:
        """
        Calculates semi-deviation (downside risk) below target threshold.
        """
        downside_diffs = [min(0.0, r - target_return) ** 2 for r in daily_returns]
        if not downside_diffs:
            return 0.0
        downside_var = sum(downside_diffs) / len(downside_diffs)
        return math.sqrt(downside_var) * math.sqrt(trading_days)

    @staticmethod
    def value_at_risk_historical(daily_returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculates historical 1-day Value at Risk (VaR) at specified confidence level.
        """
        if not daily_returns:
            return 0.0
        sorted_rets = sorted(daily_returns)
        index = int((1.0 - confidence_level) * len(sorted_rets))
        return abs(sorted_rets[min(index, len(sorted_rets) - 1)])

    @staticmethod
    def conditional_var_historical(daily_returns: List[float], confidence_level: float = 0.95) -> float:
        """
        Calculates historical Expected Shortfall / Conditional VaR (CVaR).
        """
        if not daily_returns:
            return 0.0
        sorted_rets = sorted(daily_returns)
        cutoff_idx = max(1, int((1.0 - confidence_level) * len(sorted_rets)))
        tail_losses = sorted_rets[:cutoff_idx]
        return abs(sum(tail_losses) / len(tail_losses))
