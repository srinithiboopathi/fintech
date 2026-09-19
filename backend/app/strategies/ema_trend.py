"""
Exponential Moving Average (EMA) Trend Strategy Module.
Generates deterministic crossing-event signals based on Short and Long EMA interaction.
"""
import pandas as pd
import numpy as np

from backend.app.quant.indicators import calculate_ema
from backend.app.strategies.enums import SignalType
from backend.app.strategies.validation import validate_ema_parameters


def calculate_ema_trend_signals(
    prices: pd.Series,
    short_period: int = 20,
    long_period: int = 50,
) -> pd.DataFrame:
    """
    Calculates EMA Trend trading signals.

    Logic:
        BUY:  short EMA crosses from <= long EMA to > long EMA.
        SELL: short EMA crosses from >= long EMA to < long EMA.
        HOLD: Otherwise (including the warm-up period of long_period rows).

    A BUY or SELL signal represents a discrete CROSSING EVENT, not a continuous state.

    Parameters:
        prices (pd.Series): Chronologically sorted price series (Close).
        short_period (int): Lookback span for the short EMA (default: 20).
        long_period (int): Lookback span for the long EMA (default: 50).

    Returns:
        pd.DataFrame: DataFrame containing ['close', 'short_ema', 'long_ema', 'signal'].
    """
    validate_ema_parameters(short_period, long_period)

    if prices.empty:
        return pd.DataFrame(
            columns=["close", "short_ema", "long_ema", "signal"],
            index=prices.index,
        )

    short_ema = calculate_ema(prices, short_period)
    long_ema = calculate_ema(prices, long_period)

    n = len(prices)
    signals = [SignalType.HOLD.value] * n

    short_arr = short_ema.to_numpy()
    long_arr = long_ema.to_numpy()

    # EMA requires long_period bars for reliable initialization
    warmup_cutoff = long_period

    for i in range(1, n):
        # Enforce warmup: no signals prior to accumulating long_period observations
        if i < warmup_cutoff:
            signals[i] = SignalType.HOLD.value
            continue

        prev_short = short_arr[i - 1]
        prev_long = long_arr[i - 1]
        curr_short = short_arr[i]
        curr_long = long_arr[i]

        if (
            np.isnan(prev_short)
            or np.isnan(prev_long)
            or np.isnan(curr_short)
            or np.isnan(curr_long)
        ):
            signals[i] = SignalType.HOLD.value
            continue

        # Crossing event evaluation
        if prev_short <= prev_long and curr_short > curr_long:
            signals[i] = SignalType.BUY.value
        elif prev_short >= prev_long and curr_short < curr_long:
            signals[i] = SignalType.SELL.value
        else:
            signals[i] = SignalType.HOLD.value

    return pd.DataFrame(
        {
            "close": prices,
            "short_ema": short_ema,
            "long_ema": long_ema,
            "signal": signals,
        },
        index=prices.index,
    )
