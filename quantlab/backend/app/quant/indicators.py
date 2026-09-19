import math
from typing import List, Dict, Optional, Any

class QuantIndicators:
    @staticmethod
    def sma(values: List[float], period: int) -> List[Optional[float]]:
        result = [None] * len(values)
        if len(values) < period or period <= 0:
            return result
        
        current_sum = sum(values[:period])
        result[period - 1] = current_sum / period
        for i in range(period, len(values)):
            current_sum += values[i] - values[i - period]
            result[i] = round(current_sum / period, 4)
        return result

    @staticmethod
    def ema(values: List[float], period: int) -> List[Optional[float]]:
        result = [None] * len(values)
        if len(values) < period or period <= 0:
            return result
        
        multiplier = 2.0 / (period + 1.0)
        # Initialize EMA with SMA of first 'period' elements
        initial_sma = sum(values[:period]) / period
        result[period - 1] = initial_sma
        
        prev_ema = initial_sma
        for i in range(period, len(values)):
            curr_ema = (values[i] - prev_ema) * multiplier + prev_ema
            result[i] = round(curr_ema, 4)
            prev_ema = curr_ema
        return result

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        result = [None] * len(prices)
        if len(prices) <= period:
            return result

        gains = []
        losses = []
        for i in range(1, len(prices)):
            delta = prices[i] - prices[i - 1]
            if delta >= 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(delta))

        if len(gains) < period:
            return result

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            result[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[period] = round(100.0 - (100.0 / (1.0 + rs)), 2)

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

            if avg_loss == 0:
                rsi_val = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_val = 100.0 - (100.0 / (1.0 + rs))
            result[i + 1] = round(rsi_val, 2)

        return result

    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, List[Optional[float]]]:
        sma_vals = QuantIndicators.sma(prices, period)
        upper = [None] * len(prices)
        middle = sma_vals
        lower = [None] * len(prices)

        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1 : i + 1]
            mean = sum(window) / period
            variance = sum((x - mean) ** 2 for x in window) / period
            std_dev = math.sqrt(variance)
            upper[i] = round(mean + num_std * std_dev, 4)
            lower[i] = round(mean - num_std * std_dev, 4)

        return {"upper": upper, "middle": middle, "lower": lower}

    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal_p: int = 9) -> Dict[str, List[Optional[float]]]:
        ema_fast = QuantIndicators.ema(prices, fast)
        ema_slow = QuantIndicators.ema(prices, slow)
        
        macd_line = [None] * len(prices)
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line[i] = round(ema_fast[i] - ema_slow[i], 4)

        valid_macd_indices = [i for i, v in enumerate(macd_line) if v is not None]
        signal_line = [None] * len(prices)
        hist = [None] * len(prices)

        if len(valid_macd_indices) >= signal_p:
            valid_macd_values = [macd_line[i] for i in valid_macd_indices]
            computed_signal = QuantIndicators.ema(valid_macd_values, signal_p)
            for idx_in_valid, orig_idx in enumerate(valid_macd_indices):
                sig = computed_signal[idx_in_valid]
                signal_line[orig_idx] = sig
                if sig is not None and macd_line[orig_idx] is not None:
                    hist[orig_idx] = round(macd_line[orig_idx] - sig, 4)

        return {"macd": macd_line, "signal": signal_line, "hist": hist}

    @staticmethod
    def atr(bars: List[Dict[str, Any]], period: int = 14) -> List[Optional[float]]:
        result = [None] * len(bars)
        if len(bars) <= period:
            return result

        tr_list = [bars[0]["high"] - bars[0]["low"]]
        for i in range(1, len(bars)):
            h = bars[i]["high"]
            l = bars[i]["low"]
            prev_c = bars[i - 1]["close"]
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)

        initial_atr = sum(tr_list[:period]) / period
        result[period - 1] = round(initial_atr, 4)

        prev_atr = initial_atr
        for i in range(period, len(tr_list)):
            curr_atr = (prev_atr * (period - 1) + tr_list[i]) / period
            result[i] = round(curr_atr, 4)
            prev_atr = curr_atr

        return result
