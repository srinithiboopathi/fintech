"""
Performance and Risk-Adjusted Analytics Engine for Portfolio Simulation.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from backend.app.quant.volatility import get_annualization_factor, calculate_annualized_volatility
from backend.app.quant.sharpe import calculate_sharpe_ratio
from backend.app.quant.drawdown import calculate_max_drawdown
from backend.app.backtesting.models import TradeRecordInternal, DailyPortfolioState


def calculate_portfolio_performance(
    equity_curve: List[DailyPortfolioState],
    trades: List[TradeRecordInternal],
    initial_capital: float,
    asset: str,
    risk_free_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes comprehensive financial, statistical, and trade performance metrics.
    """
    if not equity_curve:
        return {
            "initial_capital": initial_capital,
            "final_portfolio_value": initial_capital,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "maximum_drawdown": 0.0,
            "number_of_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "net_profit": 0.0,
            "average_trade_return": 0.0,
        }

    final_portfolio_value = equity_curve[-1].portfolio_value
    total_return = (final_portfolio_value / initial_capital) - 1.0

    # Calculate Annualized Return (CAGR)
    start_date_str = equity_curve[0].date
    end_date_str = equity_curve[-1].date
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

    # Extract daily returns
    daily_returns_list = [pt.daily_return for pt in equity_curve if pt.daily_return is not None]
    daily_ret_series = pd.Series(daily_returns_list, dtype=float)

    ann_factor = get_annualization_factor(asset)
    ann_vol = calculate_annualized_volatility(daily_ret_series, annualization_factor=ann_factor)
    sharpe = calculate_sharpe_ratio(daily_ret_series, risk_free_rate_annual=risk_free_rate, annualization_factor=ann_factor)

    # Maximum Drawdown from equity curve
    dd_list = [pt.drawdown for pt in equity_curve if pt.drawdown is not None]
    mdd = min(dd_list) if dd_list else 0.0
    if mdd > 0.0:
        mdd = 0.0

    # Trade Statistics
    num_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.net_pnl > 0.0)
    losing_trades = sum(1 for t in trades if t.net_pnl < 0.0)
    win_rate = (winning_trades / num_trades) if num_trades > 0 else 0.0

    gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0.0)
    gross_loss = sum(abs(t.net_pnl) for t in trades if t.net_pnl < 0.0)
    net_profit = sum(t.net_pnl for t in trades)

    avg_trade_return = (sum(t.return_pct for t in trades) / num_trades) if num_trades > 0 else 0.0

    return {
        "initial_capital": round(initial_capital, 2),
        "final_portfolio_value": round(final_portfolio_value, 2),
        "total_return": round(total_return, 6),
        "annualized_return": round(annualized_return, 6) if not np.isnan(annualized_return) else 0.0,
        "annualized_volatility": round(ann_vol, 6) if ann_vol is not None and not np.isnan(ann_vol) else 0.0,
        "sharpe_ratio": round(sharpe, 6) if sharpe is not None and not np.isnan(sharpe) else 0.0,
        "maximum_drawdown": round(mdd, 6),
        "number_of_trades": num_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 4),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "net_profit": round(net_profit, 2),
        "average_trade_return": round(avg_trade_return, 6),
    }
