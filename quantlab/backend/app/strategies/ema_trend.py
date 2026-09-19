from typing import List, Dict, Any
from app.strategies.base import BaseStrategy
from app.quant.indicators import QuantIndicators

class EMATrendStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any] = None):
        default = {"fast_ema": 9, "mid_ema": 21, "slow_ema": 55}
        if params:
            default.update(params)
        super().__init__("Triple EMA Trend Ribbon", default)

    def generate_signals(self, bars: List[Dict[str, Any]]) -> List[int]:
        prices = [b["close"] for b in bars]
        f_p = int(self.params.get("fast_ema", 9))
        m_p = int(self.params.get("mid_ema", 21))
        s_p = int(self.params.get("slow_ema", 55))

        ema_f = QuantIndicators.ema(prices, f_p)
        ema_m = QuantIndicators.ema(prices, m_p)
        ema_s = QuantIndicators.ema(prices, s_p)

        signals = [0] * len(bars)
        for i in range(len(bars)):
            if ema_f[i] is not None and ema_m[i] is not None and ema_s[i] is not None:
                # Strong upward alignment
                if ema_f[i] > ema_m[i] > ema_s[i]:
                    signals[i] = 1
                else:
                    signals[i] = 0
        return signals
