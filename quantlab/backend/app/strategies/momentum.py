from typing import List, Dict, Any
from app.strategies.base import BaseStrategy
from app.quant.indicators import QuantIndicators

class MomentumBreakoutStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any] = None):
        default = {"lookback": 20, "rsi_filter": 50.0}
        if params:
            default.update(params)
        super().__init__("Donchian Momentum Breakout", default)

    def generate_signals(self, bars: List[Dict[str, Any]]) -> List[int]:
        prices = [b["close"] for b in bars]
        lookback = int(self.params.get("lookback", 20))
        rsi_threshold = float(self.params.get("rsi_filter", 50.0))

        rsi_vals = QuantIndicators.rsi(prices, 14)
        signals = [0] * len(bars)

        for i in range(lookback, len(bars)):
            recent_highs = [bars[j]["high"] for j in range(i - lookback, i)]
            prev_channel_high = max(recent_highs) if recent_highs else bars[i]["close"]
            
            rsi_ok = rsi_vals[i] is not None and rsi_vals[i] > rsi_threshold
            if bars[i]["close"] > prev_channel_high and rsi_ok:
                signals[i] = 1
            else:
                signals[i] = signals[i - 1] if signals[i - 1] == 1 and bars[i]["close"] > (prev_channel_high * 0.95) else 0

        return signals
