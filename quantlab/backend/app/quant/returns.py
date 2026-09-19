import math
from typing import List

class ReturnMetrics:
    @staticmethod
    def simple_returns(prices: List[float]) -> List[float]:
        """
        Calculates arithmetic percentage returns: (P_t - P_{t-1}) / P_{t-1}.
        Strictly chronological without look-ahead bias.
        """
        if len(prices) < 2:
            return [0.0] if prices else []
        returns = [0.0]
        for i in range(1, len(prices)):
            p0 = prices[i - 1]
            p1 = prices[i]
            returns.append((p1 - p0) / p0 if p0 > 0 else 0.0)
        return returns

    @staticmethod
    def log_returns(prices: List[float]) -> List[float]:
        """
        Calculates logarithmic returns: ln(P_t / P_{t-1}).
        """
        if len(prices) < 2:
            return [0.0] if prices else []
        log_rets = [0.0]
        for i in range(1, len(prices)):
            p0 = prices[i - 1]
            p1 = prices[i]
            if p0 > 0 and p1 > 0:
                log_rets.append(math.log(p1 / p0))
            else:
                log_rets.append(0.0)
        return log_rets

    @staticmethod
    def cumulative_return(prices: List[float]) -> float:
        """
        Calculates total cumulative return across the entire price series: (P_end - P_start) / P_start.
        """
        if len(prices) < 2 or prices[0] <= 0:
            return 0.0
        return (prices[-1] - prices[0]) / prices[0]

    @staticmethod
    def cumulative_returns_series(daily_returns: List[float]) -> List[float]:
        """
        Calculates running compounding cumulative return series: Product(1 + r_t) - 1.
        """
        if not daily_returns:
            return []
        cum_series = []
        compounded = 1.0
        for r in daily_returns:
            compounded *= (1.0 + r)
            cum_series.append(round(compounded - 1.0, 6))
        return cum_series

    @staticmethod
    def cagr(start_value: float, end_value: float, num_days: int) -> float:
        """
        Calculates Compounded Annual Growth Rate assuming 252 trading days per year.
        """
        if start_value <= 0 or end_value <= 0 or num_days <= 0:
            return 0.0
        years = num_days / 252.0
        if years == 0:
            return 0.0
        return math.pow(end_value / start_value, 1.0 / years) - 1.0
