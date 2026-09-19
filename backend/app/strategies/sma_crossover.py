"""
Simple Moving Average (SMA) Crossover Strategy Module.
Generates deterministic crossing-event signals based on Fast and Slow SMA interaction.
"""
import pandas as pd
import numpy as np

from backend.app.quant.indicators import calculate_sma
from backend.app.strategies.enums import SignalType
from backend.app.strategies.validation import validate_sma_parameters


def calculate_sma_crossover_signals(
    prices: pd.Series,
    fast_period: int = 20,
    slow_period: int = 50,
) -> pd.DataFrame:
    """
    Calculates SMA Crossover trading signals.

    Logic:
        BUY:  fast SMA crosses from <= slow SMA to > slow SMA.
        SELL: fast SMA crosses from >= slow SMA to < slow SMA.
        HOLD: Otherwise (including warm-up periods where SMA values are not yet fully formed).

    A BUY or SELL signal represents a discrete CROSSING EVENT, not a continuous state.

    Parameters:
        prices (pd.Series): Chronologically sorted price series (Close).
        fast_period (int): Lookback period for the fast SMA (default: 20).
        slow_period (int): Lookback period for the slow SMA (default: 50).

    Returns:
        pd.DataFrame: DataFrame containing ['close', 'fast_sma', 'slow_sma', 'signal'].
    """
    validate_sma_parameters(fast_period, slow_period)

    if prices.empty:
        return pd.DataFrame(
            columns=["close", "fast_sma", "slow_sma", "signal"],
            index=prices.index,
        )

    fast_sma = calculate_sma(prices, fast_period)
    slow_sma = calculate_sma(prices, slow_period)

    n = len(prices)
    signals = [SignalType.HOLD.value] * n

    # Convert to numpy for high-performance deterministic iteration
    fast_arr = fast_sma.to_numpy()
    slow_arr = slow_sma.to_numpy()

    for i in range(1, n):
        prev_fast = fast_arr[i - 1]
        prev_slow = slow_arr[i - 1]
        curr_fast = fast_arr[i]
        curr_slow = slow_arr[i]

        # Warm-up check: both previous and current values must be valid non-NaN numbers
        if (
            np.isnan(prev_fast)
            or np.isnan(prev_slow)
            or np.isnan(curr_fast)
            or np.isnan(curr_slow)
        ):
            signals[i] = SignalType.HOLD.value
            continue

        # Crossing event evaluation
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            signals[i] = SignalType.BUY.value
        elif prev_fast >= prev_slow and curr_fast < curr_slow:
            signals[i] = SignalType.SELL.value
        else:
            signals[i] = SignalType.HOLD.value

    return pd.DataFrame(
        {
            "close": prices,
            "fast_sma": fast_sma,
            "slow_sma": slow_sma,
            "signal": signals,
        },
        index=prices.index,
    )
