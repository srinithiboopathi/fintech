"""
Portfolio Risk Contribution & Euler Volatility Decomposition Engine.
"""
from typing import Dict, List, Any
import numpy as np
import pandas as pd


def calculate_portfolio_risk_contributions(
    aligned_returns_df: pd.DataFrame,
    weights: Dict[str, float],
    annualization_factor: int = 252,
) -> Dict[str, Any]:
    """
    Computes covariance-based Euler risk decomposition for the portfolio.
    
    Mathematical Framework:
    - Annualized Covariance Matrix: Sigma = 252 * Cov(R)
    - Portfolio Variance: sigma_p^2 = w^T * Sigma * w
    - Portfolio Volatility: sigma_p = sqrt(w^T * Sigma * w)
    - Marginal Contribution to Risk (MCR): MCR_i = (Sigma * w)_i / sigma_p
    - Component Contribution to Risk (CCR): CCR_i = w_i * MCR_i = w_i * (Sigma * w)_i / sigma_p
      (Euler's Theorem: sum(CCR_i) = sigma_p)
    - Percentage Contribution to Risk (%CR): %CR_i = CCR_i / sigma_p
      (sum(%CR_i) = 100%)
      
    Returns:
        Dict with portfolio_volatility, covariance_matrix, and list of asset risk contributions.
    """
    assets = [a for a in weights.keys() if a in aligned_returns_df.columns]
    if not assets or len(aligned_returns_df) < 2:
        return {
            "portfolio_volatility": 0.0,
            "covariance_matrix": {},
            "contributions": [],
        }

    # Extract return matrix and weights vector in aligned order
    ret_matrix = aligned_returns_df[assets]
    w_vec = np.array([weights[a] for a in assets], dtype=float)

    # Sample daily covariance matrix (ddof=1)
    daily_cov = ret_matrix.cov().values
    annual_cov = daily_cov * annualization_factor

    # Portfolio Variance & Volatility
    port_variance = float(np.dot(w_vec, np.dot(annual_cov, w_vec)))
    port_variance = max(0.0, port_variance)
    port_volatility = float(np.sqrt(port_variance))

    contributions: List[Dict[str, Any]] = []

    if port_volatility > 1e-12:
        # Sigma * w
        cov_w = np.dot(annual_cov, w_vec)
        # Marginal Contribution to Risk: MCR = (Sigma * w) / sigma_p
        mcr = cov_w / port_volatility
        # Component Contribution to Risk: CCR = w * MCR
        ccr = w_vec * mcr
        # Percentage Contribution to Risk: %CR = CCR / sigma_p
        pct_cr = ccr / port_volatility

        for idx, asset in enumerate(assets):
            # Asset individual annualized volatility
            asset_daily_std = float(ret_matrix[asset].std(ddof=1))
            asset_ann_vol = float(asset_daily_std * np.sqrt(annualization_factor))

            contributions.append({
                "asset": asset,
                "weight": float(w_vec[idx]),
                "annualized_volatility": float(asset_ann_vol),
                "marginal_risk_contribution": float(mcr[idx]),
                "component_risk_contribution": float(ccr[idx]),
                "percentage_risk_contribution": float(pct_cr[idx]),
            })
    else:
        for idx, asset in enumerate(assets):
            contributions.append({
                "asset": asset,
                "weight": float(w_vec[idx]),
                "annualized_volatility": 0.0,
                "marginal_risk_contribution": 0.0,
                "component_risk_contribution": 0.0,
                "percentage_risk_contribution": 0.0,
            })

    # Format covariance matrix for reporting
    cov_dict = {}
    for i, a1 in enumerate(assets):
        cov_dict[a1] = {}
        for j, a2 in enumerate(assets):
            cov_dict[a1][a2] = float(annual_cov[i, j])

    return {
        "portfolio_volatility": float(port_volatility),
        "covariance_matrix": cov_dict,
        "contributions": contributions,
    }
