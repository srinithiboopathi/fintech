"""
Momentum Strategy Module.
Calculates continuous n-period price momentum and generates deterministic zero-line crossing signals.
"""
import pandas as pd
import numpy as np

from backend.app.strategies.enums import SignalType
from backend.app.strategies.validation import validate_momentum_parameters


def calculate_momentum_signals(
    prices: pd.Series,
    lookback: int = 20,
) -> pd.DataFrame:
    """
    Calculates Momentum trading signals based on the rate of price change.

    Formula:
        Momentum_t = (Price_t / Price_{t - lookback}) - 1

    Signal Logic (Zero-Line Crossing Event):
        BUY:  Momentum crosses from <= 0 to > 0 (bullish momentum emergence).
        SELL: Momentum crosses from >= 0 to < 0 (bearish momentum emergence).
        HOLD: Otherwise (maintaining existing state or zero change), and during the lookback warm-up.

    Note on Convention:
        The continuous 'momentum' column indicates the prevailing momentum regime
        (momentum > 0 = positive regime, momentum < 0 = negative regime).
        The 'signal' column records the discrete CROSSING EVENT (BUY/SELL) to prevent
        generating repeated trades on consecutive positive or negative days.

    Parameters:
        prices (pd.Series): Chronologically sorted price series (Close).
        lookback (int): Lookback period in trading intervals (default: 20).

    Returns:
        pd.DataFrame: DataFrame containing ['close', 'momentum', 'signal'].
    """
    validate_momentum_parameters(lookback)

    if prices.empty:
        return pd.DataFrame(
            columns=["close", "momentum", "signal"],
            index=prices.index,
        )

    # Shift prices by lookback
    shifted_prices = prices.shift(lookback)
    
    # Calculate arithmetic percentage change over lookback period
    with np.errstate(divide="ignore", invalid="ignore"):
        momentum_series = (prices / shifted_prices) - 1.0

    n = len(prices)
    signals = [SignalType.HOLD.value] * n

    mom_arr = momentum_series.to_numpy()

    for i in range(lookback, n):
        prev_mom = mom_arr[i - 1]
        curr_mom = mom_arr[i]

        if np.isnan(curr_mom):
            signals[i] = SignalType.HOLD.value
            continue

        # Treat uninitialized/warmup baseline as neutral (0.0)
        prev_val = 0.0 if np.isnan(prev_mom) else prev_mom

        if prev_val <= 0.0 and curr_mom > 0.0:
            signals[i] = SignalType.BUY.value
        elif prev_val >= 0.0 and curr_mom < 0.0:
            signals[i] = SignalType.SELL.value
        else:
            signals[i] = SignalType.HOLD.value


    return pd.DataFrame(
        {
            "close": prices,
            "momentum": momentum_series,
            "signal": signals,
        },
        index=prices.index,
    )
