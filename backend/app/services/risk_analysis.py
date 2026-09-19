"""
backend/app/services/risk_analysis.py

Quantitative Risk Analysis Service: Annualized Sharpe Ratio & Maximum Drawdown.
Calculates historical portfolio performance and risk metrics strictly from
cleaned historical market records produced by Step 3 and daily return calculations.

Mathematical Specifications:
1. Annualized Sharpe Ratio:
   Sharpe Ratio = ((mean daily return - daily risk-free rate) / sample std of daily returns) * sqrt(annualization factor)

   Where:
   - mean daily return: Arithmetic mean of daily percentage returns.
   - daily risk-free rate = annual risk-free rate / annualization factor.
   - sample std: Unbiased sample standard deviation of daily percentage returns with Bessel's correction (ddof = 1).
   - annualization factor: Typically 252 trading days for equities, 365 for crypto (default: 252).
   - If valid return count < 2: Sharpe evaluates strictly to None.
   - If sample std is zero (e.g. constant returns): Sharpe evaluates strictly to None.

2. Maximum Drawdown (MDD):
   Running Peak_t = max(Close_0 ... Close_t)
   Drawdown_t = ((Close_t / Running Peak_t) - 1) * 100
   Maximum Drawdown = min(Drawdown_t)

   - Causal Peak Tracking: Running peak at time step t only accesses observations <= t.
   - Zero look-ahead bias guaranteed.
"""

import math
from typing import List, Optional, Tuple
from app.models.schemas import CleanHistoricalPoint, DrawdownPoint, RiskAnalysisSummary
from app.services.risk_metrics import calculate_daily_returns


def calculate_sharpe_ratio(
    returns: List[Optional[float]],
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252,
    precision: Optional[int] = 4
) -> Optional[float]:
    """
    Calculates the annualized Sharpe Ratio from percentage daily returns.

    Formula:
        Daily Excess Return = mean(returns) - (risk_free_rate / annualization_factor)
        Sharpe = (Daily Excess Return / Sample Std Dev) * sqrt(annualization_factor)

    Args:
        returns: List of daily percentage returns (may contain None for t=0).
        risk_free_rate: Annualized risk-free benchmark rate (e.g., 0.0 for 0%, 2.0 for 2.0%).
        annualization_factor: Number of trading periods in a year (default: 252).
        precision: Decimal rounding precision (default: 4, pass None for raw float).

    Returns:
        Annualized Sharpe ratio, or None if undefined (< 2 valid returns or zero standard deviation).

    Raises:
        ValueError: If annualization_factor is not an integer >= 1 or risk_free_rate < 0.
    """
    if not isinstance(annualization_factor, int) or annualization_factor < 1:
        raise ValueError("annualization_factor must be a positive integer greater than or equal to 1.")
    if risk_free_rate < 0.0:
        raise ValueError("risk_free_rate must be a non-negative number.")

    valid_returns = [float(r) for r in returns if r is not None]
    m = len(valid_returns)

    if m < 2:
        return None

    daily_rf = risk_free_rate / float(annualization_factor)
    mean_return = sum(valid_returns) / m

    variance = sum((r - mean_return) ** 2 for r in valid_returns) / (m - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0.0:
        return None

    excess_return = mean_return - daily_rf
    sharpe = (excess_return / std_dev) * math.sqrt(float(annualization_factor))

    return round(sharpe, precision) if precision is not None else sharpe


def calculate_drawdown(
    prices: List[float],
    timestamps: List[str],
    precision: Optional[int] = 4
) -> Tuple[List[DrawdownPoint], Optional[float], Optional[str]]:
    """
    Calculates historical drawdown time series and maximum drawdown from close prices.

    Formulas:
        Running Peak_t = max(Close_0 ... Close_t)
        Drawdown_t = ((Close_t / Running Peak_t) - 1) * 100
        Maximum Drawdown = min(Drawdown_t)

    Args:
        prices: List of chronological closing prices.
        timestamps: List of corresponding ISO-8601 UTC timestamp strings.
        precision: Decimal rounding precision (default: 4).

    Returns:
        Tuple of (List[DrawdownPoint], maximum_drawdown_pct, maximum_drawdown_timestamp).
    """
    n = len(prices)
    if n == 0:
        return [], None, None

    if n == 1:
        single_point = DrawdownPoint(
            timestamp=timestamps[0],
            close=prices[0],
            running_peak=prices[0],
            drawdown_pct=0.0
        )
        return [single_point], 0.0, timestamps[0]

    drawdown_series: List[DrawdownPoint] = []
    running_peak = prices[0]
    min_drawdown = 0.0
    min_drawdown_ts = timestamps[0]

    for t in range(n):
        price = prices[t]
        ts = timestamps[t]

        if price > running_peak:
            running_peak = price

        if running_peak > 0:
            dd_pct = ((price / running_peak) - 1.0) * 100.0
        else:
            dd_pct = 0.0

        rounded_dd = round(dd_pct, precision) if precision is not None else dd_pct
        rounded_peak = round(running_peak, precision) if precision is not None else running_peak

        drawdown_series.append(DrawdownPoint(
            timestamp=ts,
            close=price,
            running_peak=rounded_peak,
            drawdown_pct=rounded_dd
        ))

        if dd_pct < min_drawdown:
            min_drawdown = dd_pct
            min_drawdown_ts = ts

    final_max_dd = round(min_drawdown, precision) if precision is not None else min_drawdown
    return drawdown_series, final_max_dd, min_drawdown_ts


def compute_risk_analysis(
    clean_points: List[CleanHistoricalPoint],
    risk_free_rate: float = 0.0,
    annualization_factor: int = 252
) -> Tuple[RiskAnalysisSummary, List[DrawdownPoint]]:
    """
    Computes annualized Sharpe Ratio and Maximum Drawdown analysis from clean records.

    Args:
        clean_points: Validated historical records from Step 3.
        risk_free_rate: Annual risk-free rate percentage (default: 0.0).
        annualization_factor: Trading periods per year (default: 252).

    Returns:
        Tuple of (RiskAnalysisSummary, List[DrawdownPoint]).
    """
    # Guarantee chronological ascending order
    sorted_points = sorted(clean_points, key=lambda p: p.timestamp)
    prices = [p.close for p in sorted_points]
    timestamps = [p.timestamp for p in sorted_points]

    daily_returns = calculate_daily_returns(prices, precision=None)
    valid_returns = [r for r in daily_returns if r is not None]

    sharpe_ratio = calculate_sharpe_ratio(
        returns=daily_returns,
        risk_free_rate=risk_free_rate,
        annualization_factor=annualization_factor,
        precision=4
    )

    drawdown_series, max_dd_pct, max_dd_ts = calculate_drawdown(
        prices=prices,
        timestamps=timestamps,
        precision=4
    )

    latest_close = prices[-1] if prices else None

    summary = RiskAnalysisSummary(
        risk_free_rate=risk_free_rate,
        annualization_factor=annualization_factor,
        valid_return_count=len(valid_returns),
        sharpe_ratio=sharpe_ratio,
        maximum_drawdown_pct=max_dd_pct,
        maximum_drawdown_timestamp=max_dd_ts,
        latest_close=latest_close
    )

    return summary, drawdown_series


class RiskAnalysisService:
    """Service wrapper for Sharpe ratio and drawdown computations."""
    calculate_sharpe_ratio = staticmethod(calculate_sharpe_ratio)
    calculate_drawdown = staticmethod(calculate_drawdown)
    compute_risk_analysis = staticmethod(compute_risk_analysis)


risk_analysis_service = RiskAnalysisService()
