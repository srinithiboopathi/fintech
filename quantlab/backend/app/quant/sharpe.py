import math
from typing import List
from app.quant.volatility import VolatilityMetrics

class RiskAdjustedMetrics:
    @staticmethod
    def sharpe_ratio(daily_returns: List[float], risk_free_rate: float = 0.035, trading_days: int = 252) -> float:
        """
        Calculates annualized Sharpe Ratio: (Annualized Return - Rf) / Annualized Volatility.
        """
        if len(daily_returns) < 2:
            return 0.0
        ann_vol = VolatilityMetrics.annualized_volatility(daily_returns, trading_days)
        if ann_vol == 0:
            return 0.0
        ann_return = (sum(daily_returns) / len(daily_returns)) * trading_days
        return (ann_return - risk_free_rate) / ann_vol

    @staticmethod
    def sortino_ratio(daily_returns: List[float], risk_free_rate: float = 0.035, trading_days: int = 252) -> float:
        """
        Calculates annualized Sortino Ratio penalizing only downside volatility.
        """
        if len(daily_returns) < 2:
            return 0.0
        downside_vol = VolatilityMetrics.downside_volatility(daily_returns, target_return=0.0, trading_days=trading_days)
        if downside_vol == 0:
            return 0.0
        ann_return = (sum(daily_returns) / len(daily_returns)) * trading_days
        return (ann_return - risk_free_rate) / downside_vol

    @staticmethod
    def calmar_ratio(cagr: float, max_drawdown: float) -> float:
        """
        Calculates Calmar Ratio: CAGR / |Max Drawdown|.
        """
        if max_drawdown == 0:
            return 0.0
        return abs(cagr) / abs(max_drawdown)

    @staticmethod
    def omega_ratio(daily_returns: List[float], threshold: float = 0.0) -> float:
        """
        Calculates Omega Ratio: Probability weighted gains over losses.
        """
        gains = [r - threshold for r in daily_returns if r > threshold]
        losses = [threshold - r for r in daily_returns if r < threshold]
        sum_losses = sum(losses)
        if sum_losses == 0:
            return 10.0 if gains else 1.0
        return sum(gains) / sum_losses
