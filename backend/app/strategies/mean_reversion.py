"""
Mean Reversion Strategy Module.
Identifies overextended price deviations from a central moving average baseline.
"""
import pandas as pd
import numpy as np

from backend.app.quant.indicators import calculate_sma
from backend.app.strategies.enums import SignalType
from backend.app.strategies.validation import validate_mean_reversion_parameters


def calculate_mean_reversion_signals(
    prices: pd.Series,
    window: int = 20,
    threshold: float = 0.02,
) -> pd.DataFrame:
    """
    Calculates Mean Reversion trading signals using rolling moving average and deviation band.

    Formulas:
        moving_average_t = (1 / window) * sum_{i=0}^{window-1} Price_{t-i}
        deviation_t      = (Price_t - moving_average_t) / moving_average_t

    Signal Logic:
        BUY:  deviation_t <= -threshold (price oversold relative to mean -> reversion upward expected).
        SELL: deviation_t >= +threshold (price overbought relative to mean -> reversion downward expected).
        HOLD: Otherwise (-threshold < deviation_t < threshold, or during the window warm-up period).

    Parameters:
        prices (pd.Series): Chronologically sorted price series (Close).
        window (int): Rolling moving average window in trading days (default: 20).
        threshold (float): Percentage threshold deviation required for signal trigger (default: 0.02).

    Returns:
        pd.DataFrame: DataFrame containing ['close', 'moving_average', 'deviation', 'signal'].
    """
    validate_mean_reversion_parameters(window, threshold)

    if prices.empty:
        return pd.DataFrame(
            columns=["close", "moving_average", "deviation", "signal"],
            index=prices.index,
        )

    moving_avg = calculate_sma(prices, window)

    with np.errstate(divide="ignore", invalid="ignore"):
        deviation = (prices - moving_avg) / moving_avg

    n = len(prices)
    signals = [SignalType.HOLD.value] * n

    dev_arr = deviation.to_numpy()

    for i in range(n):
        val = dev_arr[i]
        if np.isnan(val):
            signals[i] = SignalType.HOLD.value
        elif val <= -threshold:
            signals[i] = SignalType.BUY.value
        elif val >= threshold:
            signals[i] = SignalType.SELL.value
        else:
            signals[i] = SignalType.HOLD.value

    return pd.DataFrame(
        {
            "close": prices,
            "moving_average": moving_avg,
            "deviation": deviation,
            "signal": signals,
        },
        index=prices.index,
    )
