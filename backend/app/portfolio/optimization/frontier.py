"""
Efficient Frontier & Random Feasible Portfolio Sampling Generator.
"""
from typing import Dict, List, Optional, Any
import numpy as np
from backend.app.portfolio.optimization.optimizer import (
    calculate_portfolio_stats,
    optimize_for_target_return,
)


def get_max_feasible_expected_return(
    expected_returns: np.ndarray,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
) -> float:
    """
    Computes the maximum attainable expected return on the constrained simplex:
        max w^T * mu
        s.t. sum(w) = 1, min_weight <= w_i <= max_weight
    """
    n = len(expected_returns)
    w = np.full(n, min_weight, dtype=float)
    remaining_weight = 1.0 - (n * min_weight)
    
    # Sort indices by expected return descending
    sorted_indices = np.argsort(-expected_returns)
    
    for idx in sorted_indices:
        if remaining_weight <= 1e-9:
            break
        add_w = min(remaining_weight, max_weight - min_weight)
        w[idx] += add_w
        remaining_weight -= add_w
        
    return float(np.dot(w, expected_returns))


def generate_efficient_frontier(
    asset_names: List[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    gmv_return: float,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    frontier_points: int = 50,
    risk_free_rate: float = 0.02,
) -> List[Dict[str, Any]]:
    """
    Generates the Markowitz Efficient Frontier by sweeping target expected returns
    from the Global Minimum Variance portfolio return up to the maximum feasible return.
    
    Returns only successfully converged optimization points.
    """
    n = len(asset_names)
    max_return = get_max_feasible_expected_return(expected_returns, min_weight, max_weight)
    
    if max_return <= gmv_return + 1e-6:
        # Frontier is a single point (or returns are identical)
        target_returns = [gmv_return]
    else:
        target_returns = np.linspace(gmv_return, max_return, frontier_points)
        
    frontier: List[Dict[str, Any]] = []
    
    for target_ret in target_returns:
        opt_w = optimize_for_target_return(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            target_return=float(target_ret),
            min_weight=min_weight,
            max_weight=max_weight,
        )
        
        if opt_w is not None:
            exp_ret, variance, volatility, sharpe = calculate_portfolio_stats(
                opt_w, expected_returns, cov_matrix, risk_free_rate
            )
            weights_dict = {asset_names[i]: float(opt_w[i]) for i in range(n)}
            
            frontier.append({
                "target_return": float(target_ret),
                "expected_return": float(exp_ret),
                "variance": float(variance),
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe),
                "weights": weights_dict,
            })
            
    return frontier


def generate_random_portfolios(
    asset_names: List[str],
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    num_portfolios: int = 5000,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    risk_free_rate: float = 0.02,
    random_seed: int = 42,
) -> List[Dict[str, Any]]:
    """
    Generates a deterministic sample of feasible random portfolios on the constrained simplex.
    
    Every portfolio strictly satisfies:
        sum(w_i) == 1.0
        min_weight <= w_i <= max_weight
    """
    n = len(asset_names)
    rng = np.random.default_rng(random_seed)
    
    collected_weights: List[np.ndarray] = []
    slack = 1.0 - (n * min_weight)
    max_slack = max_weight - min_weight
    
    # If unconstrained standard simplex [0, 1]
    is_standard = abs(min_weight - 0.0) < 1e-6 and abs(max_weight - 1.0) < 1e-6
    
    batch_size = max(num_portfolios * 2, 2000)
    max_attempts = 50
    attempts = 0
    
    while len(collected_weights) < num_portfolios and attempts < max_attempts:
        attempts += 1
        if is_standard:
            # Dirichlet(1, ..., 1) is uniform on simplex
            raw = rng.exponential(scale=1.0, size=(batch_size, n))
            samples = raw / np.sum(raw, axis=1, keepdims=True)
            for row in samples:
                collected_weights.append(row)
                if len(collected_weights) >= num_portfolios:
                    break
        else:
            # Shifted simplex with rejection sampling for upper bound
            raw = rng.exponential(scale=1.0, size=(batch_size, n))
            raw_norm = raw / np.sum(raw, axis=1, keepdims=True)
            # Scaled excess weights
            excess = raw_norm * slack
            # Check upper bound feasibility: excess <= max_slack
            valid_mask = np.all(excess <= max_slack + 1e-7, axis=1)
            valid_excess = excess[valid_mask]
            
            for row in valid_excess:
                full_w = min_weight + row
                full_w = full_w / np.sum(full_w)  # precise normalization
                collected_weights.append(full_w)
                if len(collected_weights) >= num_portfolios:
                    break
                    
    # Fallback if rejection sampling was insufficient under tight bounds
    while len(collected_weights) < num_portfolios:
        # Uniform convex interpolation between random valid points
        if len(collected_weights) >= 2:
            idx1, idx2 = rng.choice(len(collected_weights), size=2, replace=False)
            alpha = rng.uniform(0.0, 1.0)
            interp_w = alpha * collected_weights[idx1] + (1.0 - alpha) * collected_weights[idx2]
            interp_w = interp_w / np.sum(interp_w)
            collected_weights.append(interp_w)
        else:
            # Equal weight default
            collected_weights.append(np.full(n, 1.0 / n, dtype=float))
            
    weights_matrix = np.array(collected_weights[:num_portfolios], dtype=float)
    
    # Vectorized calculation of expected returns, variances, volatilities, and Sharpe ratios
    exp_rets = np.dot(weights_matrix, expected_returns)
    variances = np.sum((weights_matrix @ cov_matrix) * weights_matrix, axis=1)
    variances = np.maximum(0.0, variances)
    volatilities = np.sqrt(variances)
    
    sharpes = np.where(
        volatilities > 1e-12,
        (exp_rets - risk_free_rate) / volatilities,
        0.0,
    )
    
    results: List[Dict[str, Any]] = []
    for i in range(num_portfolios):
        w_dict = {asset_names[j]: float(weights_matrix[i, j]) for j in range(n)}
        results.append({
            "expected_return": float(exp_rets[i]),
            "volatility": float(volatilities[i]),
            "sharpe_ratio": float(sharpes[i]),
            "weights": w_dict,
        })
        
    return results
