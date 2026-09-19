from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter(prefix="/strategies", tags=["Strategies"])

PRESET_STRATEGIES = [
    {
        "id": "sma_crossover",
        "name": "Dual SMA Golden Cross",
        "category": "Trend Following",
        "description": "Momentum crossover tracking short-term vs long-term moving averages.",
        "parameters": {
            "fast_period": {"type": "int", "default": 20, "min": 5, "max": 100, "label": "Fast SMA Period"},
            "slow_period": {"type": "int", "default": 50, "min": 20, "max": 200, "label": "Slow SMA Period"},
            "stop_loss_pct": {"type": "float", "default": 0.05, "min": 0.01, "max": 0.30, "label": "Stop Loss (%)"},
            "take_profit_pct": {"type": "float", "default": 0.15, "min": 0.02, "max": 0.80, "label": "Take Profit (%)"}
        }
    },
    {
        "id": "ema_trend",
        "name": "Triple EMA Trend Ribbon",
        "category": "Trend Following",
        "description": "Multi-timeframe exponential moving average trend-following model.",
        "parameters": {
            "fast_ema": {"type": "int", "default": 9, "min": 3, "max": 50, "label": "Fast EMA"},
            "mid_ema": {"type": "int", "default": 21, "min": 10, "max": 100, "label": "Mid EMA"},
            "slow_ema": {"type": "int", "default": 55, "min": 30, "max": 200, "label": "Slow EMA"},
            "stop_loss_pct": {"type": "float", "default": 0.04, "min": 0.01, "max": 0.20, "label": "Stop Loss (%)"}
        }
    },
    {
        "id": "mean_reversion",
        "name": "Bollinger Bands Mean Reversion",
        "category": "Mean Reversion",
        "description": "Statistical mean-reversion buying oversold dips at the 2.0σ Lower Bollinger Band.",
        "parameters": {
            "bb_period": {"type": "int", "default": 20, "min": 10, "max": 50, "label": "BB Period"},
            "bb_std": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.5, "label": "Standard Deviations"},
            "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 30, "label": "RSI Period"},
            "rsi_oversold": {"type": "float", "default": 35.0, "min": 10.0, "max": 45.0, "label": "RSI Oversold Level"},
            "rsi_overbought": {"type": "float", "default": 70.0, "min": 55.0, "max": 90.0, "label": "RSI Overbought Level"}
        }
    },
    {
        "id": "momentum",
        "name": "Donchian Momentum Breakout",
        "category": "Breakout",
        "description": "Donchian high breakout model coupled with RSI momentum validation.",
        "parameters": {
            "lookback": {"type": "int", "default": 20, "min": 5, "max": 60, "label": "Channel Lookback"},
            "rsi_filter": {"type": "float", "default": 50.0, "min": 30.0, "max": 70.0, "label": "RSI Minimum Filter"}
        }
    }
]

@router.get("", response_model=List[Dict[str, Any]])
def list_strategies():
    return PRESET_STRATEGIES
