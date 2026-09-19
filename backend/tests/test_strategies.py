"""
Deterministic unit tests for QuantLab Strategy Module (SMA Crossover & EMA Trend).
"""

import numpy as np
import pandas as pd
import pytest

from backend.app.strategies.sma_crossover import SMACrossoverStrategy
from backend.app.strategies.ema_trend import EMATrendStrategy


class TestSMACrossoverStrategy:
    def test_sma_crossover_signals_and_lookahead_prevention(self):
        # Construct deterministic price series:
        # Day 0-4: Flat 10.0 -> SMA(2) = 10.0, SMA(4) = 10.0
        # Day 5: 20.0 -> SMA(2) = (10+20)/2 = 15.0, SMA(4) = (10+10+10+20)/4 = 12.5 -> Fast > Slow!
        # Because look-ahead bias must be avoided, day 5's signal MUST affect Day 6!
        # Day 6 position must be 1, but Day 5 position must STILL be 0.
        prices = [10.0, 10.0, 10.0, 10.0, 10.0, 20.0, 20.0, 5.0, 5.0, 5.0]
        df = pd.DataFrame({"Close": prices})

        strategy = SMACrossoverStrategy(fast_window=2, slow_window=4)
        signals = strategy.generate_signals(df)

        # Before day 5, fast is not strictly greater than slow or insufficient window -> 0
        assert signals.iloc[4] == 0
        # On day 5, fast crosses above slow, but position on day 5 must remain 0 (no lookahead!)
        assert signals.iloc[5] == 0
        # On day 6, the signal takes effect -> 1 (long)
        assert signals.iloc[6] == 1
        assert signals.iloc[7] == 1

    def test_invalid_parameters_raise(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            SMACrossoverStrategy(fast_window=0, slow_window=10)
        with pytest.raises(ValueError, match="strictly greater"):
            SMACrossoverStrategy(fast_window=10, slow_window=5)
        with pytest.raises(ValueError, match="strictly greater"):
            SMACrossoverStrategy(fast_window=10, slow_window=10)

    def test_empty_and_insufficient_data(self):
        empty_df = pd.DataFrame(columns=["Close"])
        strat = SMACrossoverStrategy(fast_window=5, slow_window=10)
        assert strat.generate_signals(empty_df).empty

        short_df = pd.DataFrame({"Close": [10.0, 11.0, 12.0]})
        signals = strat.generate_signals(short_df)
        assert len(signals) == 3
        assert (signals == 0).all()


class TestEMATrendStrategy:
    def test_ema_trend_signals_and_lookahead_prevention(self):
        # Construct prices: flat at 10.0, then spikes on day 3 to 20.0
        # EMA(3) at day 3 will be around 15.0 < 20.0 -> raw signal = 1
        # Position at day 3 must be 0, position at day 4 must be 1.
        prices = [10.0, 10.0, 10.0, 20.0, 20.0, 5.0, 5.0]
        df = pd.DataFrame({"Close": prices})

        strategy = EMATrendStrategy(ema_window=3)
        signals = strategy.generate_signals(df)

        # Day 3: price spikes, but executed position on day 3 is 0 (no lookahead)
        assert signals.iloc[3] == 0
        # Day 4: position reflects day 3 signal -> 1
        assert signals.iloc[4] == 1

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            EMATrendStrategy(ema_window=0)

    def test_empty_and_insufficient_data(self):
        empty_df = pd.DataFrame(columns=["Close"])
        strat = EMATrendStrategy(ema_window=5)
        assert strat.generate_signals(empty_df).empty

        short_df = pd.DataFrame({"Close": [1.0, 2.0]})
        assert (strat.generate_signals(short_df) == 0).all()
