"""
Portfolio Optimization Engine using Markowitz Modern Portfolio Theory (MPT).
"""
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy.optimize import minimize
from fastapi import HTTPException, status


def calculate_portfolio_stats(
    weights: np.ndarray,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float = 0.02,
) -> Tuple[float, float, float, float]:
    """
    Computes (expected_return, variance, volatility, sharpe_ratio) for given weights.
    
    Formula:
        mu_p = w^T * mu
        var_p = w^T * Sigma * w
        vol_p = sqrt(var_p)
        sharpe = (mu_p - rf) / vol_p
    """
    exp_ret = float(np.dot(weights, expected_returns))
    variance = float(np.dot(weights, np.dot(cov_matrix, weights)))
    variance = max(0.0, variance)
    volatility = float(np.sqrt(variance))
    
    if volatility > 1e-12:
        sharpe = float((exp_ret - risk_free_rate) / volatility)
    else:
        sharpe = 0.0
        
    return exp_ret, variance, volatility, sharpe


def optimize_equal_weight(
    asset_names: List[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Evaluates the Equal-Weight (1/N) benchmark portfolio.
    Enforces that 1/N must satisfy the provided min/max bounds.
    """
    n = len(asset_names)
    eq_w = 1.0 / n
    
    # Check if 1/N is feasible under min_weight and max_weight
    if eq_w < min_weight - 1e-6 or eq_w > max_weight + 1e-6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Equal-weight allocation ({eq_w * 100:.2f}%) is outside the specified weight constraints "
                f"[{min_weight * 100:.1f}%, {max_weight * 100:.1f}%]."
            ),
        )
        
    w_vec = np.full(n, eq_w, dtype=float)
    exp_ret, variance, volatility, sharpe = calculate_portfolio_stats(
        w_vec, expected_returns, cov_matrix, risk_free_rate
    )
    
    weights_dict = {asset_names[i]: float(w_vec[i]) for i in range(n)}
    
    return {
        "portfolio_type": "Equal Weight",
        "weights": weights_dict,
        "expected_return": float(exp_ret),
        "variance": float(variance),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
    }


def optimize_min_volatility(
    asset_names: List[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Solves for the Global Minimum Variance (GMV) portfolio:
        min w^T * Sigma * w
        s.t. sum(w) = 1, min_weight <= w_i <= max_weight
    """
    n = len(asset_names)
    
    def objective(w: np.ndarray) -> float:
        return float(np.dot(w, np.dot(cov_matrix, w)))
        
    bounds = tuple((float(min_weight), float(max_weight)) for _ in range(n))
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}]
    
    # Initial guess: equal weights or clipped uniform
    init_w = np.full(n, 1.0 / n, dtype=float)
    init_w = np.clip(init_w, min_weight, max_weight)
    init_w = init_w / np.sum(init_w)
    
    result = minimize(
        objective,
        init_w,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
    )
    
    if not result.success and result.fun is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Minimum volatility optimization solver failed: {result.message}",
        )
        
    raw_w = np.clip(result.x, min_weight, max_weight)
    norm_w = raw_w / np.sum(raw_w)
    
    exp_ret, variance, volatility, sharpe = calculate_portfolio_stats(
        norm_w, expected_returns, cov_matrix, risk_free_rate
    )
    
    weights_dict = {asset_names[i]: float(norm_w[i]) for i in range(n)}
    
    return {
        "portfolio_type": "Minimum Volatility",
        "weights": weights_dict,
        "expected_return": float(exp_ret),
        "variance": float(variance),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
    }


def optimize_max_sharpe(
    asset_names: List[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.02,
) -> Dict[str, Any]:
    """
    Solves for the Maximum Sharpe Ratio (Tangency) portfolio:
        max (w^T * mu - rf) / sqrt(w^T * Sigma * w)
        equivalent to min -(w^T * mu - rf) / (sqrt(w^T * Sigma * w) + eps)
        s.t. sum(w) = 1, min_weight <= w_i <= max_weight
    """
    n = len(asset_names)
    
    def neg_sharpe(w: np.ndarray) -> float:
        ret = np.dot(w, expected_returns)
        var = np.dot(w, np.dot(cov_matrix, w))
        vol = np.sqrt(max(0.0, var))
        if vol < 1e-12:
            return 0.0
        return float(-(ret - risk_free_rate) / vol)
        
    bounds = tuple((float(min_weight), float(max_weight)) for _ in range(n))
    constraints = [{"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}]
    
    # Try multiple starting points for robustness
    init_points = [
        np.full(n, 1.0 / n, dtype=float),
    ]
    # Add GMV-like starting point
    for i in range(n):
        point = np.full(n, min_weight, dtype=float)
        point[i] = max_weight
        if np.sum(point) > 0:
            point = point / np.sum(point)
            init_points.append(point)
            
    best_result = None
    best_fun = float("inf")
    
    for init_w in init_points:
        init_w = np.clip(init_w, min_weight, max_weight)
        if np.sum(init_w) > 0:
            init_w = init_w / np.sum(init_w)
        else:
            continue
            
        res = minimize(
            neg_sharpe,
            init_w,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
        if res.success and res.fun < best_fun:
            best_fun = res.fun
            best_result = res
            
    if best_result is None or best_result.x is None:
        # Fallback to single solve if multi-start had convergence flag issues
        init_w = np.full(n, 1.0 / n, dtype=float)
        init_w = np.clip(init_w, min_weight, max_weight)
        init_w = init_w / np.sum(init_w)
        best_result = minimize(
            neg_sharpe,
            init_w,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-9, "maxiter": 1000},
        )
        
    raw_w = np.clip(best_result.x, min_weight, max_weight)
    norm_w = raw_w / np.sum(raw_w)
    
    exp_ret, variance, volatility, sharpe = calculate_portfolio_stats(
        norm_w, expected_returns, cov_matrix, risk_free_rate
    )
    
    weights_dict = {asset_names[i]: float(norm_w[i]) for i in range(n)}
    
    return {
        "portfolio_type": "Maximum Sharpe",
        "weights": weights_dict,
        "expected_return": float(exp_ret),
        "variance": float(variance),
        "volatility": float(volatility),
        "sharpe_ratio": float(sharpe),
    }


def optimize_for_target_return(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    target_return: float,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> Optional[np.ndarray]:
    """
    Solves for the minimum variance portfolio achieving a specific target expected return:
        min w^T * Sigma * w
        s.t. sum(w) = 1, w^T * mu = target_return, min_weight <= w_i <= max_weight
    
    Returns optimal weight vector if successful, else None.
    """
    n = len(expected_returns)
    
    def objective(w: np.ndarray) -> float:
        return float(np.dot(w, np.dot(cov_matrix, w)))
        
    bounds = tuple((float(min_weight), float(max_weight)) for _ in range(n))
    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {"type": "eq", "fun": lambda w: float(np.dot(w, expected_returns) - target_return)},
    ]
    
    init_w = np.full(n, 1.0 / n, dtype=float)
    init_w = np.clip(init_w, min_weight, max_weight)
    init_w = init_w / np.sum(init_w)
    
    res = minimize(
        objective,
        init_w,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"ftol": 1e-10, "maxiter": 1000},
    )
    
    if res.success and res.x is not None:
        w_res = np.clip(res.x, min_weight, max_weight)
        w_norm = w_res / np.sum(w_res)
        # Check target return tolerance
        achieved_ret = np.dot(w_norm, expected_returns)
        if abs(achieved_ret - target_return) < 1e-3:
            return w_norm
            
    return None
