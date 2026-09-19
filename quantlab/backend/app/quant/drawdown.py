from typing import List, Tuple, Dict, Any

class DrawdownAnalysis:
    @staticmethod
    def calculate_drawdowns(equity_curve: List[float]) -> Tuple[List[float], float, int]:
        """
        Returns:
            (underwater_series, max_drawdown_pct, max_drawdown_duration_bars)
        """
        if not equity_curve:
            return [], 0.0, 0

        underwater = []
        peak = equity_curve[0]
        max_dd = 0.0
        current_dd_len = 0
        max_dd_len = 0

        for val in equity_curve:
            if val > peak:
                peak = val
                current_dd_len = 0
            else:
                current_dd_len += 1
                if current_dd_len > max_dd_len:
                    max_dd_len = current_dd_len

            dd = (val - peak) / peak if peak > 0 else 0.0
            underwater.append(round(dd, 4))
            if dd < max_dd:
                max_dd = dd

        return underwater, abs(max_dd), max_dd_len

    @staticmethod
    def get_drawdown_details(dates: List[str], prices: List[float]) -> Dict[str, Any]:
        """
        Detailed breakdown: peak date, trough date, max drawdown percentage, and recovery status.
        """
        if not prices:
            return {"max_drawdown": 0.0, "peak_date": "", "trough_date": "", "duration_days": 0}

        peak = prices[0]
        peak_idx = 0
        max_dd = 0.0
        trough_idx = 0
        best_peak_idx = 0

        for i, val in enumerate(prices):
            if val > peak:
                peak = val
                peak_idx = i
            else:
                dd = (val - peak) / peak
                if dd < max_dd:
                    max_dd = dd
                    trough_idx = i
                    best_peak_idx = peak_idx

        return {
            "max_drawdown_pct": round(abs(max_dd) * 100.0, 2),
            "peak_date": dates[best_peak_idx] if best_peak_idx < len(dates) else "",
            "trough_date": dates[trough_idx] if trough_idx < len(dates) else "",
            "duration_days": max(0, trough_idx - best_peak_idx)
        }
