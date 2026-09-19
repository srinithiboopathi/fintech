"""
backend/app/services/risk_metrics.py

Quantitative Risk Metrics Engine: Daily Returns & Rolling Volatility.
Calculates historical percentage returns and rolling sample standard deviation
strictly from cleaned historical market records produced by Step 3.

Mathematical Specifications:
1. Daily Percentage Return:
   Return_t = ((Close_t / Close_(t-1)) - 1) * 100
   where Close_t is the closing price at time t.
   For t = 0 (first observation), no previous close exists, returning None.

2. Rolling Volatility (Sample Standard Deviation, ddof=1):
   Volatility_t = std(Return_(t-n+1) ... Return_t)
   where n is the volatility window (observations) and:
       std = sqrt( (1 / (n - 1)) * sum_{i=1}^n (r_i - mean(r))^2 )
   - Non-annualized rolling daily volatility expressed in percentage points.
   - Period = 1: Sample variance with 1 observation is mathematically undefined
     (division by n - 1 = 0). Evaluates strictly to None.
   - Insufficient return observations: When fewer than n valid return observations
     exist, evaluates strictly to None.

3. Zero Look-Ahead Bias:
   At each time step t, calculations depend solely on data points at indices <= t.
   Altering any future price at t_future > t strictly leaves past returns and
   volatility values unchanged.
"""

import math
from typing import List, Optional, Tuple
from app.models.schemas import CleanHistoricalPoint, RiskMetricPoint, RiskMetricsSummary

def calculate_daily_returns(
    prices: List[float],
    precision: Optional[int] = 4
) -> List[Optional[float]]:
    """
    Calculates percentage daily returns from a sequence of chronological close prices.

    Formula:
        Return_t = ((Close_t / Close_(t-1)) - 1) * 100

    Args:
        prices: List of chronological closing prices (oldest to newest).
        precision: Decimal rounding precision (default: 4, pass None for raw float).

    Returns:
        List of percentage returns matching len(prices).
        Index 0 is strictly None (no prior close).
    """
    n = len(prices)
    if n == 0:
        return []

    returns: List[Optional[float]] = [None] * n

    for i in range(1, n):
        prev_p = prices[i - 1]
        curr_p = prices[i]
        if prev_p <= 0:
            returns[i] = None
            continue
        ret_val = ((curr_p - prev_p) / prev_p) * 100.0
        returns[i] = round(ret_val, precision) if precision is not None else ret_val

    return returns



def calculate_rolling_volatility(
    returns: List[Optional[float]],
    period: int = 20,
    precision: Optional[int] = 4
) -> List[Optional[float]]:
    """
    Calculates rolling sample standard deviation (ddof=1) of percentage returns.

    Requirements:
        - Uses sample standard deviation (ddof=1): sqrt(sum((x - mean)^2) / (n - 1)).
        - Not annualized (daily percentage-point volatility).
        - Requires 'period' valid (non-None) return observations in window.
        - When period = 1, sample std with 1 observation is mathematically undefined
          (division by zero, ddof=1). Returns None rather than inventing a value.
        - When observations < period, returns None.

    Args:
        returns: Chronologically ordered list of daily percentage returns.
        period: Configurable window size (n >= 1, default: 20).
        precision: Decimal rounding precision (default: 4, pass None for raw float).

    Returns:
        List of rolling volatility values matching len(returns).

    Raises:
        ValueError: If period is not an integer >= 1.
    """
    if not isinstance(period, int) or period < 1:
        raise ValueError("Volatility period must be a positive integer greater than or equal to 1.")

    n = len(returns)
    volatility: List[Optional[float]] = [None] * n

    # Period = 1 is mathematically undefined for sample standard deviation (ddof=1, n-1=0)
    if period < 2:
        return volatility

    if period > n:
        return volatility

    for i in range(period - 1, n):
        # Extract window of length `period` ending at index `i`
        window = returns[i - period + 1 : i + 1]
        
        # If any value in the window is None, cannot calculate
        if any(r is None for r in window):
            volatility[i] = None
            continue

        clean_window = [float(r) for r in window] # type: ignore
        m = len(clean_window)
        mean = sum(clean_window) / m
        variance = sum((x - mean) ** 2 for x in clean_window) / (m - 1)
        std_dev = math.sqrt(variance)
        volatility[i] = round(std_dev, precision) if precision is not None else std_dev

    return volatility


def compute_risk_metrics(
    clean_points: List[CleanHistoricalPoint],
    volatility_period: int = 20
) -> Tuple[List[RiskMetricPoint], RiskMetricsSummary]:
    """
    Computes daily percentage returns and rolling volatility from cleaned Step 3 records.

    Args:
        clean_points: Validated historical records from Step 3.
        volatility_period: Configurable volatility window (default: 20).

    Returns:
        Tuple of (List[RiskMetricPoint], RiskMetricsSummary).

    Raises:
        ValueError: If volatility_period is not an integer >= 1.
    """
    if not isinstance(volatility_period, int) or volatility_period < 1:
        raise ValueError("Volatility period must be a positive integer greater than or equal to 1.")

    # Guarantee chronological ascending order
    sorted_points = sorted(clean_points, key=lambda p: p.timestamp)
    close_prices = [p.close for p in sorted_points]

    daily_returns = calculate_daily_returns(close_prices, precision=4)
    rolling_vols = calculate_rolling_volatility(daily_returns, period=volatility_period, precision=4)

    metric_points: List[RiskMetricPoint] = []
    for pt, ret_val, vol_val in zip(sorted_points, daily_returns, rolling_vols):
        metric_points.append(RiskMetricPoint(
            timestamp=pt.timestamp,
            close=pt.close,
            return_pct=ret_val,
            volatility=vol_val
        ))

    valid_returns = [r for r in daily_returns if r is not None]
    valid_volatilities = [v for v in rolling_vols if v is not None]

    latest_close = sorted_points[-1].close if sorted_points else None
    latest_return = valid_returns[-1] if valid_returns else None
    latest_volatility = valid_volatilities[-1] if valid_volatilities else None

    summary = RiskMetricsSummary(
        volatility_period=volatility_period,
        total_records=len(sorted_points),
        valid_return_count=len(valid_returns),
        valid_volatility_count=len(valid_volatilities),
        latest_close=latest_close,
        latest_return=latest_return,
        latest_volatility=latest_volatility
    )

    return metric_points, summary


class RiskMetricsService:
    """Service wrapper for return and volatility computations."""
    calculate_daily_returns = staticmethod(calculate_daily_returns)
    calculate_rolling_volatility = staticmethod(calculate_rolling_volatility)
    compute_risk_metrics = staticmethod(compute_risk_metrics)


risk_metrics_service = RiskMetricsService()
