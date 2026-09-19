"""
backend/app/services/indicators.py

Quantitative Indicator Calculation Service.
Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA)
strictly from cleaned historical market data produced by Step 3.

Mathematical Specifications:
1. SMA Formula:
   SMA_t = (1 / n) * sum_{k=0}^{n-1} P_{t-k}
   where n is the period, and P_t is the close price at time t.
   For indices < n - 1, fewer than n observations exist, returning None.

2. EMA Formula:
   Multiplier (Smoothing factor):
       alpha = 2 / (n + 1)
   Initialization (Standard Industry Seed):
       EMA_(n-1) = SMA of the first n closing prices: (1 / n) * sum_{k=0}^{n-1} P_k
       Indices 0 to n - 2 return None.
   Recursive Update (for t >= n):
       EMA_t = (P_t * alpha) + (EMA_(t-1) * (1 - alpha))

3. Zero Look-Ahead Bias:
   At each time step t, only current and historical prices (indices <= t) are accessed.
   Altering any future price at t_future > t strictly leaves indicator values at t unchanged.
"""

from typing import List, Optional, Tuple
from app.models.schemas import CleanHistoricalPoint, IndicatorPoint, IndicatorsSummary

def calculate_sma(
    prices: List[float],
    period: int = 20,
    precision: int = 4
) -> List[Optional[float]]:
    """
    Calculates Simple Moving Average (SMA) over a list of chronological closing prices.

    Args:
        prices: Chronologically ascending list of close prices.
        period: Configurable positive integer window size (n >= 1, default: 20).
        precision: Decimal rounding precision (default: 4).

    Returns:
        List of SMA values with identical length to prices.
        Indices < period - 1 contain None.

    Raises:
        ValueError: If period is not an integer or is less than 1.
    """
    if not isinstance(period, int) or period < 1:
        raise ValueError("Indicator periods must be positive integers greater than or equal to 1.")

    n = len(prices)
    result: List[Optional[float]] = [None] * n

    if period > n:
        return result

    for i in range(period - 1, n):
        window = prices[i - period + 1 : i + 1]
        val = sum(window) / period
        result[i] = round(val, precision) if precision is not None else val

    return result


def calculate_ema(
    prices: List[float],
    period: int = 20,
    precision: int = 4
) -> List[Optional[float]]:
    """
    Calculates Exponential Moving Average (EMA) over a list of chronological closing prices.

    Initialization Method:
        The initial seed value at index (period - 1) is computed as the Simple Moving Average
        of the first 'period' closing prices. All preceding indices (0 to period - 2) return None.
        Subsequent values (t >= period) are updated via:
            EMA_t = (P_t * alpha) + (EMA_(t-1) * (1 - alpha))
        where alpha = 2 / (period + 1).

    Args:
        prices: Chronologically ascending list of close prices.
        period: Configurable positive integer window size (n >= 1, default: 20).
        precision: Decimal rounding precision (default: 4).

    Returns:
        List of EMA values with identical length to prices.
        Indices < period - 1 contain None.

    Raises:
        ValueError: If period is not an integer or is less than 1.
    """
    if not isinstance(period, int) or period < 1:
        raise ValueError("Indicator periods must be positive integers greater than or equal to 1.")

    n = len(prices)
    result: List[Optional[float]] = [None] * n

    if period > n:
        return result

    alpha = 2.0 / (period + 1.0)

    # Initialization: SMA of the first 'period' prices
    initial_sma = sum(prices[:period]) / period
    result[period - 1] = round(initial_sma, precision) if precision is not None else initial_sma

    prev_ema = initial_sma
    for i in range(period, n):
        current_ema = (prices[i] * alpha) + (prev_ema * (1.0 - alpha))
        result[i] = round(current_ema, precision) if precision is not None else current_ema
        prev_ema = current_ema

    return result


def compute_indicators(
    clean_points: List[CleanHistoricalPoint],
    sma_period: int = 20,
    ema_period: int = 20
) -> Tuple[List[IndicatorPoint], IndicatorsSummary]:
    """
    Computes SMA and EMA indicators from cleaned historical market records.

    Args:
        clean_points: List of validated CleanHistoricalPoint instances from Step 3.
        sma_period: Configurable SMA period (default: 20).
        ema_period: Configurable EMA period (default: 20).

    Returns:
        Tuple containing:
        - List[IndicatorPoint]: Chronologically ordered indicator records.
        - IndicatorsSummary: Statistical overview of calculated indicators.

    Raises:
        ValueError: If sma_period or ema_period is not an integer >= 1.
    """
    if not isinstance(sma_period, int) or sma_period < 1:
        raise ValueError("Indicator periods must be positive integers greater than or equal to 1.")
    if not isinstance(ema_period, int) or ema_period < 1:
        raise ValueError("Indicator periods must be positive integers greater than or equal to 1.")

    # Strictly sort by timestamp ascending
    sorted_points = sorted(clean_points, key=lambda p: p.timestamp)
    close_prices = [p.close for p in sorted_points]

    sma_values = calculate_sma(close_prices, sma_period)
    ema_values = calculate_ema(close_prices, ema_period)

    indicator_points: List[IndicatorPoint] = []
    for pt, sma_val, ema_val in zip(sorted_points, sma_values, ema_values):
        indicator_points.append(IndicatorPoint(
            timestamp=pt.timestamp,
            close=pt.close,
            sma=sma_val,
            ema=ema_val
        ))

    valid_smas = [s for s in sma_values if s is not None]
    valid_emas = [e for e in ema_values if e is not None]

    latest_close = sorted_points[-1].close if sorted_points else None
    latest_sma = valid_smas[-1] if valid_smas else None
    latest_ema = valid_emas[-1] if valid_emas else None

    summary = IndicatorsSummary(
        requested_sma_period=sma_period,
        requested_ema_period=ema_period,
        total_records=len(sorted_points),
        valid_sma_count=len(valid_smas),
        valid_ema_count=len(valid_emas),
        latest_close=latest_close,
        latest_sma=latest_sma,
        latest_ema=latest_ema
    )

    return indicator_points, summary


class IndicatorService:
    """Service wrapper for indicator computations."""
    calculate_sma = staticmethod(calculate_sma)
    calculate_ema = staticmethod(calculate_ema)
    compute_indicators = staticmethod(compute_indicators)


indicator_service = IndicatorService()
