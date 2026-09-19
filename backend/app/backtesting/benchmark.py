"""
Buy-and-Hold Benchmark Engine and Strategy Comparative Analytics.
"""
from typing import List, Dict, Any
from datetime import datetime
import numpy as np
import pandas as pd

from backend.app.quant.volatility import get_annualization_factor, calculate_annualized_volatility
from backend.app.quant.sharpe import calculate_sharpe_ratio
from backend.app.backtesting.models import DailyPortfolioState


def calculate_buy_and_hold_benchmark(
    df: pd.DataFrame,
    initial_capital: float,
    transaction_cost: float,
    asset: str,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Simulates a Buy-and-Hold benchmark investing 100% of capital at the initial open.

    Parameters:
        df (pd.DataFrame): Chronologically sorted market data with ['date', 'open', 'close'].
        initial_capital (float): Starting portfolio capital in USD.
        transaction_cost (float): Fractional fee applied on initial buy (e.g. 0.001).
        asset (str): Canonical asset identifier.
        risk_free_rate (float): Annualized risk-free rate.

    Returns:
        Dict containing benchmark performance summary and equity curve.
    """
    if df.empty:
        return {
            "initial_capital": initial_capital,
            "final_value": initial_capital,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "maximum_drawdown": 0.0,
            "equity_curve": [],
        }

    first_open = float(df["open"].iloc[0])
    if first_open <= 0:
        first_open = float(df["close"].iloc[0])

    effective_price = first_open * (1.0 + transaction_cost)
    quantity = initial_capital / effective_price
    cost = quantity * first_open * transaction_cost
    cash = initial_capital - (quantity * first_open + cost)

    curve: List[DailyPortfolioState] = []
    running_peak = -np.inf
    prev_val = initial_capital

    for i in range(len(df)):
        d = str(df["date"].iloc[i])
        close_price = float(df["close"].iloc[i])
        pos_val = quantity * close_price
        port_val = cash + pos_val

        running_peak = max(running_peak, port_val)
        dd = (port_val / running_peak) - 1.0 if running_peak > 0 else 0.0
        if dd > 0.0:
            dd = 0.0

        daily_ret = (port_val / prev_val) - 1.0 if i > 0 else 0.0
        cum_ret = (port_val / initial_capital) - 1.0

        curve.append(DailyPortfolioState(
            date=d,
            cash=cash,
            position_quantity=quantity,
            position_value=pos_val,
            portfolio_value=port_val,
            daily_return=daily_ret,
            cumulative_return=cum_ret,
            drawdown=dd,
        ))
        prev_val = port_val

    final_value = curve[-1].portfolio_value
    total_return = (final_value / initial_capital) - 1.0

    # Annualized Return (CAGR)
    start_date_str = str(df["date"].iloc[0])
    end_date_str = str(df["date"].iloc[-1])
    annualized_return = 0.0

    try:
        d_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        d_end = datetime.strptime(end_date_str, "%Y-%m-%d")
        cal_days = (d_end - d_start).days
        if cal_days > 0:
            years = cal_days / 365.25
            if 1.0 + total_return > 0:
                annualized_return = ((1.0 + total_return) ** (1.0 / years)) - 1.0
            else:
                annualized_return = -1.0
        else:
            annualized_return = total_return
    except Exception:
        annualized_return = total_return

    # Volatility and Sharpe
    daily_returns_list = [pt.daily_return for pt in curve if pt.daily_return is not None]
    daily_ret_series = pd.Series(daily_returns_list, dtype=float)

    ann_factor = get_annualization_factor(asset)
    ann_vol = calculate_annualized_volatility(daily_ret_series, annualization_factor=ann_factor)
    sharpe = calculate_sharpe_ratio(daily_ret_series, risk_free_rate_annual=risk_free_rate, annualization_factor=ann_factor)

    dd_list = [pt.drawdown for pt in curve if pt.drawdown is not None]
    mdd = min(dd_list) if dd_list else 0.0
    if mdd > 0.0:
        mdd = 0.0

    return {
        "initial_capital": round(initial_capital, 2),
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 6),
        "annualized_return": round(annualized_return, 6) if not np.isnan(annualized_return) else 0.0,
        "annualized_volatility": round(ann_vol, 6) if ann_vol is not None and not np.isnan(ann_vol) else 0.0,
        "sharpe_ratio": round(sharpe, 6) if sharpe is not None and not np.isnan(sharpe) else 0.0,
        "maximum_drawdown": round(mdd, 6),
        "equity_curve": curve,
    }


def calculate_strategy_comparison(
    strategy_perf: Dict[str, Any],
    benchmark_perf: Dict[str, Any],
) -> Dict[str, float]:
    """Computes arithmetic differential metrics between strategy and benchmark."""
    return {
        "return_difference": round(strategy_perf["total_return"] - benchmark_perf["total_return"], 6),
        "annualized_return_difference": round(strategy_perf["annualized_return"] - benchmark_perf["annualized_return"], 6),
        "volatility_difference": round(strategy_perf["annualized_volatility"] - benchmark_perf["annualized_volatility"], 6),
        "sharpe_difference": round(strategy_perf["sharpe_ratio"] - benchmark_perf["sharpe_ratio"], 6),
        "mdd_difference": round(strategy_perf["maximum_drawdown"] - benchmark_perf["maximum_drawdown"], 6),
    }
