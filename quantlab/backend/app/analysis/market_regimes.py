import math
from typing import List, Dict, Any
from app.quant.indicators import QuantIndicators
from app.quant.volatility import VolatilityMetrics

class MarketRegimeClassifier:
    """
    4-State Market Regime Model:
    1. Bull Trend (Strong upward momentum, low-to-moderate volatility)
    2. Bear Trend (Downward slope, elevated volatility)
    3. Volatile Choppy (High realized volatility, mean-reverting / ranging)
    4. Low-Vol Consolidation (Tight sideways range, low volatility)
    """

    @staticmethod
    def classify_series(bars: List[Dict[str, Any]], lookback: int = 20) -> List[Dict[str, Any]]:
        prices = [b["close"] for b in bars]
        sma_50 = QuantIndicators.sma(prices, 50)
        
        # Calculate daily returns
        rets = [0.0]
        for i in range(1, len(prices)):
            rets.append((prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] > 0 else 0.0)

        regimes = []
        for i in range(len(bars)):
            bar = bars[i]
            d = bar["date"]
            price = prices[i]

            if i < lookback:
                regimes.append({
                    "date": d,
                    "regime": "Consolidation",
                    "volatility_rank": "Normal",
                    "trend_direction": "Neutral",
                    "confidence": 0.70
                })
                continue

            sub_rets = rets[i - lookback + 1 : i + 1]
            local_vol = VolatilityMetrics.annualized_volatility(sub_rets)
            ma_val = sma_50[i] if sma_50[i] is not None else price
            
            # Trend slope (20-day return)
            period_return = (price - prices[i - lookback]) / prices[i - lookback]

            if period_return > 0.05 and local_vol <= 0.35:
                regime_name = "Bull Trend"
                trend_dir = "Bullish"
                confidence = 0.88
            elif period_return < -0.05 and local_vol > 0.25:
                regime_name = "Bear Trend"
                trend_dir = "Bearish"
                confidence = 0.85
            elif local_vol > 0.40:
                regime_name = "Volatile Choppy"
                trend_dir = "High Dispersion"
                confidence = 0.82
            else:
                regime_name = "Consolidation"
                trend_dir = "Sideways"
                confidence = 0.78

            regimes.append({
                "date": d,
                "regime": regime_name,
                "volatility_rank": "High" if local_vol > 0.35 else ("Low" if local_vol < 0.18 else "Moderate"),
                "trend_direction": trend_dir,
                "realized_volatility": round(local_vol * 100.0, 2),
                "confidence": confidence
            })

        return regimes
