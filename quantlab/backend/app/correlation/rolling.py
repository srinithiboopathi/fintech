from typing import List, Dict, Any
from app.correlation.matrix import CorrelationMatrix

class RollingCorrelation:
    @staticmethod
    def calculate_rolling(
        dates: List[str],
        returns_x: List[float],
        returns_y: List[float],
        window: int = 30
    ) -> List[Dict[str, Any]]:
        n = min(len(dates), len(returns_x), len(returns_y))
        result = []

        for i in range(window - 1, n):
            sub_x = returns_x[i - window + 1 : i + 1]
            sub_y = returns_y[i - window + 1 : i + 1]
            corr = CorrelationMatrix.pearson_correlation(sub_x, sub_y)
            result.append({
                "date": dates[i],
                "correlation": corr
            })
        return result
