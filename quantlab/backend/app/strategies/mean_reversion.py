from typing import List, Dict, Any
from app.strategies.base import BaseStrategy
from app.quant.indicators import QuantIndicators

class MeanReversionStrategy(BaseStrategy):
    def __init__(self, params: Dict[str, Any] = None):
        default = {
            "bb_period": 20,
            "bb_std": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 35.0,
            "rsi_overbought": 70.0
        }
        if params:
            default.update(params)
        super().__init__("Bollinger Bands & RSI Mean Reversion", default)

    def generate_signals(self, bars: List[Dict[str, Any]]) -> List[int]:
        prices = [b["close"] for b in bars]
        bb_period = int(self.params.get("bb_period", 20))
        bb_std = float(self.params.get("bb_std", 2.0))
        rsi_p = int(self.params.get("rsi_period", 14))
        rsi_os = float(self.params.get("rsi_oversold", 35.0))
        rsi_ob = float(self.params.get("rsi_overbought", 70.0))

        bb = QuantIndicators.bollinger_bands(prices, bb_period, bb_std)
        rsi_vals = QuantIndicators.rsi(prices, rsi_p)

        signals = [0] * len(bars)
        in_position = False

        for i in range(len(bars)):
            lower = bb["lower"][i]
            middle = bb["middle"][i]
            rsi = rsi_vals[i]

            if lower is not None and rsi is not None:
                # Buy when price dips near lower band & RSI oversold
                if not in_position and (prices[i] <= lower * 1.01 or rsi < rsi_os):
                    in_position = True
                # Exit when reverting to midline or RSI overbought
                elif in_position and (prices[i] >= middle or rsi > rsi_ob):
                    in_position = False

            signals[i] = 1 if in_position else 0

        return signals
