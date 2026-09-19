import pytest
from app.strategies.sma_crossover import SMACrossoverStrategy
from app.strategies.ema_trend import EMATrendStrategy
from app.strategies.momentum import MomentumBreakoutStrategy
from app.strategies.mean_reversion import MeanReversionStrategy

def generate_sample_bars(n=100, trend="up"):
    bars = []
    base_price = 100.0
    for i in range(n):
        if trend == "up":
            p = base_price + (i * 1.5)
        elif trend == "down":
            p = max(10.0, base_price - (i * 1.5))
        else: # oscillatory
            p = base_price + (10.0 if i % 4 in [0, 1] else -10.0)
        
        bars.append({
            "date": f"2023-01-{i+1:03d}",
            "symbol": "TEST",
            "open": p - 0.5,
            "high": p + 1.0,
            "low": p - 1.0,
            "close": p,
            "adj_close": p,
            "volume": 500000,
            "daily_return": 0.01 if trend == "up" else -0.01
        })
    return bars

def test_sma_crossover_strategy():
    bars = generate_sample_bars(60, trend="up")
    strat = SMACrossoverStrategy({"fast_period": 10, "slow_period": 25})
    signals = strat.generate_signals(bars)
    actions = strat.generate_signal_actions(bars)
    
    assert len(signals) == 60
    assert len(actions) == 60
    assert signals[-1] == 1 # In steady uptrend, fast SMA > slow SMA -> Long
    assert all(act in ["BUY", "SELL", "HOLD"] for act in actions)

def test_ema_trend_strategy():
    bars = generate_sample_bars(80, trend="up")
    strat = EMATrendStrategy({"fast_ema": 9, "mid_ema": 21, "slow_ema": 50})
    signals = strat.generate_signals(bars)
    actions = strat.generate_signal_actions(bars)
    
    assert len(signals) == 80
    assert len(actions) == 80
    assert signals[-1] == 1
    assert "BUY" in actions or "HOLD" in actions

def test_momentum_breakout_strategy():
    bars = generate_sample_bars(50, trend="up")
    strat = MomentumBreakoutStrategy({"lookback": 20, "rsi_filter": 50.0})
    signals = strat.generate_signals(bars)
    actions = strat.generate_signal_actions(bars)
    
    assert len(signals) == 50
    assert len(actions) == 50
    assert all(s in [-1, 0, 1] for s in signals)

def test_mean_reversion_strategy():
    bars = generate_sample_bars(60, trend="oscillate")
    strat = MeanReversionStrategy({"bb_period": 20, "bb_std": 2.0, "rsi_period": 14})
    signals = strat.generate_signals(bars)
    actions = strat.generate_signal_actions(bars)
    
    assert len(signals) == 60
    assert len(actions) == 60
    assert all(s in [-1, 0, 1] for s in signals)
    assert all(act in ["BUY", "SELL", "HOLD"] for act in actions)
