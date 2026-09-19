import math
from typing import List, Dict, Any
from app.quant.volatility import VolatilityMetrics

class BenchmarkAnalysis:
    @staticmethod
    def calculate_alpha_beta(
        portfolio_returns: List[float],
        benchmark_returns: List[float],
        risk_free_rate: float = 0.035
    ) -> Dict[str, float]:
        n = min(len(portfolio_returns), len(benchmark_returns))
        if n < 2:
            return {"beta": 1.0, "alpha": 0.0, "r_squared": 0.0, "information_ratio": 0.0}

        rp = portfolio_returns[:n]
        rb = benchmark_returns[:n]

        mean_p = sum(rp) / n
        mean_b = sum(rb) / n

        cov = sum((rp[i] - mean_p) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
        var_b = sum((rb[i] - mean_b) ** 2 for i in range(n)) / (n - 1)

        beta = cov / var_b if var_b > 0 else 1.0

        ann_rp = mean_p * 252.0
        ann_rb = mean_b * 252.0
        alpha = ann_rp - (risk_free_rate + beta * (ann_rb - risk_free_rate))

        # Tracking error & Information ratio
        diff_rets = [rp[i] - rb[i] for i in range(n)]
        tracking_error = VolatilityMetrics.annualized_volatility(diff_rets)
        info_ratio = (ann_rp - ann_rb) / tracking_error if tracking_error > 0 else 0.0

        return {
            "beta": round(beta, 3),
            "alpha": round(alpha * 100.0, 2), # percentage
            "tracking_error": round(tracking_error * 100.0, 2),
            "information_ratio": round(info_ratio, 2)
        }
