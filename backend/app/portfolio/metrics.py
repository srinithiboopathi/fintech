"""
Portfolio Performance and Metric Calculation Engine.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from backend.app.quant.volatility import get_annualization_factor
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown


def calculate_portfolio_daily_returns(
    aligned_returns_df: pd.DataFrame,
    weights: Dict[str, float],
) -> pd.Series:
    """
    Computes portfolio daily returns as the linear weighted sum of asset daily returns.
    
    Formula:
        r_{p,t} = sum(w_i * r_{i,t})
    """
    portfolio_returns = pd.Series(0.0, index=aligned_returns_df.index, dtype=float)
    for asset, weight in weights.items():
        if asset in aligned_returns_df.columns:
            portfolio_returns += aligned_returns_df[asset] * float(weight)
    return portfolio_returns


def calculate_portfolio_cumulative_returns(
    portfolio_daily_returns: pd.Series,
) -> pd.Series:
    """
    Computes cumulative portfolio growth curve from daily returns.
    
    Formula:
        C_{p,t} = prod_{tau=1}^t (1 + r_{p,tau}) - 1
    """
    return (1.0 + portfolio_daily_returns).cumprod() - 1.0


def calculate_portfolio_value_series(
    cumulative_returns: pd.Series,
    initial_capital: float,
) -> pd.Series:
    """
    Computes the dollar portfolio equity value over time.
    
    Formula:
        V_t = V_0 * (1 + C_{p,t})
    """
    return initial_capital * (1.0 + cumulative_returns)


def calculate_portfolio_performance_summary(
    portfolio_daily_returns: pd.Series,
    cumulative_returns: pd.Series,
    initial_capital: float,
    risk_free_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Computes institutional performance metrics for the portfolio.
    
    - Total Return
    - CAGR (Annualized Return)
    - Annualized Volatility (252 trading days factor)
    - Sharpe Ratio
    - Maximum Drawdown
    """
    n_obs = len(portfolio_daily_returns)
    if n_obs == 0:
        return {
            "initial_capital": initial_capital,
            "final_value": initial_capital,
            "total_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "maximum_drawdown": 0.0,
            "observations": 0,
        }

    total_return = float(cumulative_returns.iloc[-1]) if n_obs > 0 else 0.0
    final_value = float(initial_capital * (1.0 + total_return))

    ann_factor = get_annualization_factor("daily")  # 252

    # CAGR: (1 + Total_Return)^(252 / N) - 1
    if n_obs > 0 and (1.0 + total_return) > 0:
        annualized_return = float((1.0 + total_return) ** (ann_factor / n_obs) - 1.0)
    else:
        annualized_return = -1.0 if total_return <= -1.0 else 0.0

    # Annualized Volatility: std(daily_returns) * sqrt(252)
    daily_std = float(portfolio_daily_returns.std(ddof=1)) if n_obs > 1 else 0.0
    annualized_volatility = float(daily_std * np.sqrt(ann_factor)) if not np.isnan(daily_std) else 0.0

    # Sharpe Ratio: (CAGR - r_f) / Annualized_Vol
    if annualized_volatility > 1e-12:
        sharpe_ratio = float((annualized_return - risk_free_rate) / annualized_volatility)
    else:
        sharpe_ratio = 0.0

    # Drawdown Series & Maximum Drawdown
    # Convert cumulative return to price-like index (starting at 1.0)
    wealth_index = 1.0 + cumulative_returns
    drawdown_series = calculate_drawdown_series(wealth_index)
    max_drawdown = calculate_max_drawdown(drawdown_series)

    return {
        "initial_capital": round(initial_capital, 2),
        "final_value": round(final_value, 2),
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "annualized_volatility": float(annualized_volatility),
        "sharpe_ratio": float(sharpe_ratio),
        "maximum_drawdown": float(max_drawdown),
        "observations": int(n_obs),
        "drawdown_series": drawdown_series,
    }


def calculate_performance_contributions(
    aligned_returns_df: pd.DataFrame,
    weights: Dict[str, float],
) -> List[Dict[str, Any]]:
    """
    Calculates how each individual asset contributed to overall portfolio performance.
    
    Metrics per asset:
    - Weight: w_i
    - Asset Total Return: R_i = prod(1 + r_{i,t}) - 1
    - Weighted Return Contribution: w_i * R_i
    - Percentage Contribution: (w_i * R_i) / sum(w_j * R_j)
    """
    contributions = []
    total_weighted_sum = 0.0

    raw_contributions = {}
    for asset, weight in weights.items():
        if asset in aligned_returns_df.columns:
            asset_ret_series = aligned_returns_df[asset]
            asset_total_ret = float((1.0 + asset_ret_series).prod() - 1.0)
            weighted_contrib = float(weight * asset_total_ret)
            raw_contributions[asset] = {
                "weight": float(weight),
                "total_return": asset_total_ret,
                "weighted_contribution": weighted_contrib,
            }
            total_weighted_sum += weighted_contrib

    for asset, data in raw_contributions.items():
        contrib_pct = None
        if abs(total_weighted_sum) > 1e-12:
            contrib_pct = float(data["weighted_contribution"] / total_weighted_sum)

        contributions.append({
            "asset": asset,
            "weight": data["weight"],
            "total_return": data["total_return"],
            "weighted_contribution": data["weighted_contribution"],
            "contribution_percentage": contrib_pct,
        })

    return contributions
