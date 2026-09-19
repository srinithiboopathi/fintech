import math
from typing import List, Dict, Any

class DataNormalizer:
    @staticmethod
    def compute_percentage_returns(prices: List[float]) -> List[float]:
        if len(prices) < 2:
            return []
        rets = [0.0]
        for i in range(1, len(prices)):
            p0 = prices[i - 1]
            p1 = prices[i]
            rets.append((p1 - p0) / p0 if p0 > 0 else 0.0)
        return rets

    @staticmethod
    def compute_log_returns(prices: List[float]) -> List[float]:
        if len(prices) < 2:
            return []
        log_rets = [0.0]
        for i in range(1, len(prices)):
            p_prev = prices[i - 1]
            p_curr = prices[i]
            if p_prev > 0 and p_curr > 0:
                log_rets.append(math.log(p_curr / p_prev))
            else:
                log_rets.append(0.0)
        return log_rets

    @staticmethod
    def z_score_normalize(series: List[float]) -> List[float]:
        if not series:
            return []
        mean = sum(series) / len(series)
        variance = sum((x - mean) ** 2 for x in series) / len(series)
        std = math.sqrt(variance) if variance > 0 else 1.0
        return [round((x - mean) / std, 6) for x in series]

    @staticmethod
    def min_max_scale(series: List[float], min_val: float = 0.0, max_val: float = 1.0) -> List[float]:
        if not series:
            return []
        s_min = min(series)
        s_max = max(series)
        if s_max == s_min:
            return [min_val for _ in series]
        return [round(min_val + (x - s_min) / (s_max - s_min) * (max_val - min_val), 6) for x in series]
