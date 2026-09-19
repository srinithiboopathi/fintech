import math
from typing import List, Optional
from app.quant.volatility import VolatilityMetrics

class RollingMetrics:
    @staticmethod
    def rolling_returns(daily_returns: List[float], window: int = 30) -> List[Optional[float]]:
        """
        Computes rolling cumulative arithmetic return over a sliding window: Product(1+r) - 1.
        """
        result = [None] * len(daily_returns)
        if len(daily_returns) < window or window <= 0:
            return result

        for i in range(window - 1, len(daily_returns)):
            sub_series = daily_returns[i - window + 1 : i + 1]
            compounded = 1.0
            for r in sub_series:
                compounded *= (1.0 + r)
            result[i] = round(compounded - 1.0, 6)
        return result

    @staticmethod
    def rolling_volatility(daily_returns: List[float], window: int = 30, trading_days: int = 252) -> List[Optional[float]]:
        """
        Computes rolling annualized volatility over a sliding window.
        """
        result = [None] * len(daily_returns)
        if len(daily_returns) < window or window <= 0:
            return result

        for i in range(window - 1, len(daily_returns)):
            sub_series = daily_returns[i - window + 1 : i + 1]
            vol = VolatilityMetrics.annualized_volatility(sub_series, trading_days)
            result[i] = round(vol, 4)
        return result

    @staticmethod
    def rolling_sharpe(daily_returns: List[float], window: int = 60, risk_free_rate: float = 0.035) -> List[Optional[float]]:
        """
        Computes rolling annualized Sharpe Ratio over a sliding window.
        """
        result = [None] * len(daily_returns)
        if len(daily_returns) < window or window <= 0:
            return result

        for i in range(window - 1, len(daily_returns)):
            sub_series = daily_returns[i - window + 1 : i + 1]
            ann_vol = VolatilityMetrics.annualized_volatility(sub_series)
            if ann_vol > 0:
                ann_ret = (sum(sub_series) / window) * 252.0
                sharpe = (ann_ret - risk_free_rate) / ann_vol
                result[i] = round(sharpe, 2)
            else:
                result[i] = 0.0
        return result

    @staticmethod
    def rolling_drawdown(equity_curve: List[float], window: int = 60) -> List[Optional[float]]:
        """
        Computes rolling maximum drawdown within the preceding N bars.
        """
        result = [None] * len(equity_curve)
        if len(equity_curve) < window or window <= 0:
            return result

        for i in range(window - 1, len(equity_curve)):
            sub_series = equity_curve[i - window + 1 : i + 1]
            peak = sub_series[0]
            max_dd = 0.0
            for val in sub_series:
                if val > peak:
                    peak = val
                dd = (val - peak) / peak if peak > 0 else 0.0
                if dd < max_dd:
                    max_dd = dd
            result[i] = round(abs(max_dd), 4)
        return result
