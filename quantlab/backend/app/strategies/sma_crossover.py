from typing import List, Dict, Any
from app.strategies.base import BaseStrategy
from app.quant.indicators import QuantIndicators

class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any] = None):
        default = {"fast_period": 20, "slow_period": 50}
        if params:
            default.update(params)
        super().__init__("Dual SMA Crossover", default)

    def generate_signals(self, bars: List[Dict[str, Any]]) -> List[int]:
        prices = [b["close"] for b in bars]
        fast_p = int(self.params.get("fast_period", 20))
        slow_p = int(self.params.get("slow_period", 50))

        sma_fast = QuantIndicators.sma(prices, fast_p)
        sma_slow = QuantIndicators.sma(prices, slow_p)

        signals = [0] * len(bars)
        for i in range(len(bars)):
            if sma_fast[i] is not None and sma_slow[i] is not None:
                if sma_fast[i] > sma_slow[i]:
                    signals[i] = 1 # Bullish regime -> Long
                else:
                    signals[i] = 0 # Flat
        return signals
