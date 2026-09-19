"""
Descriptive Statistics and Transition Detection for Market Regimes (Phase 8).
Calculates historical return/volatility metrics per regime and identifies state transition events.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

from backend.app.quant.volatility import get_annualization_factor, calculate_annualized_volatility
from backend.app.quant.sharpe import calculate_sharpe_ratio
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown
from backend.app.regimes.enums import MarketRegime, VolatilityState


def _compute_state_metrics(
    subset_df: pd.DataFrame,
    total_valid_days: int,
    ann_factor: int,
) -> Dict[str, Any]:
    """Computes descriptive summary statistics for a given regime or volatility state subset."""
    obs_count = len(subset_df)
    if obs_count == 0:
        return {
            "observation_count": 0,
            "percentage": 0.0,
            "start_date": None,
            "end_date": None,
            "average_daily_return": None,
            "cumulative_return": None,
            "annualized_volatility": None,
            "sharpe_ratio": None,
            "maximum_drawdown": None,
        }
        
    pct = round(obs_count / max(total_valid_days, 1), 4)
    start_d = str(subset_df["date"].iloc[0])
    end_d = str(subset_df["date"].iloc[-1])
    
    returns = subset_df["daily_return"].dropna()
    avg_daily_ret = round(float(returns.mean()), 6) if not returns.empty else 0.0
    
    # Cumulative return compounded across the subset days
    if not returns.empty:
        compounded_ret = float(np.prod(1.0 + returns) - 1.0)
        cum_ret = round(compounded_ret, 6)
    else:
        cum_ret = 0.0
        
    # Annualized volatility
    ann_vol = calculate_annualized_volatility(returns, annualization_factor=ann_factor)
    ann_vol = round(ann_vol, 6) if ann_vol is not None else None
    
    # Sharpe ratio
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate_annual=0.0, annualization_factor=ann_factor)
    sharpe = round(sharpe, 4) if sharpe is not None else None
    
    # Maximum drawdown on subset cumulative return series
    if not returns.empty:
        wealth_series = (1.0 + returns).cumprod()
        dd_series = calculate_drawdown_series(wealth_series)
        mdd = calculate_max_drawdown(dd_series)
        mdd = round(mdd, 6) if mdd is not None else 0.0
    else:
        mdd = 0.0
        
    return {
        "observation_count": obs_count,
        "percentage": pct,
        "start_date": start_d,
        "end_date": end_d,
        "average_daily_return": avg_daily_ret,
        "cumulative_return": cum_ret,
        "annualized_volatility": ann_vol,
        "sharpe_ratio": sharpe,
        "maximum_drawdown": mdd,
    }


def calculate_regime_summary_statistics(
    classified_df: pd.DataFrame,
    asset: str,
) -> Dict[str, Any]:
    """
    Calculates descriptive historical statistics across trend regimes and volatility states.
    
    Parameters:
        classified_df (pd.DataFrame): DataFrame output from classify_market_regimes.
        asset (str): Asset name for annualization factor determination.
        
    Returns:
        Dict[str, Any]: Dictionary containing statistics for BULL, BEAR, HIGH_VOLATILITY, LOW_VOLATILITY.
    """
    ann_factor = get_annualization_factor(asset)
    
    # Valid classified days
    valid_regimes = classified_df[classified_df["regime"].notna()]
    total_regime_days = len(valid_regimes)
    
    bull_df = valid_regimes[valid_regimes["regime"] == MarketRegime.BULL.value]
    bear_df = valid_regimes[valid_regimes["regime"] == MarketRegime.BEAR.value]
    
    valid_vols = classified_df[classified_df["volatility_state"].notna()]
    total_vol_days = len(valid_vols)
    
    high_vol_df = valid_vols[valid_vols["volatility_state"] == VolatilityState.HIGH_VOLATILITY.value]
    low_vol_df = valid_vols[valid_vols["volatility_state"] == VolatilityState.LOW_VOLATILITY.value]
    
    return {
        "bull": _compute_state_metrics(bull_df, total_regime_days, ann_factor),
        "bear": _compute_state_metrics(bear_df, total_regime_days, ann_factor),
        "high_volatility": _compute_state_metrics(high_vol_df, total_vol_days, ann_factor),
        "low_volatility": _compute_state_metrics(low_vol_df, total_vol_days, ann_factor),
        "total_observations": len(classified_df),
        "classified_trend_observations": total_regime_days,
        "classified_volatility_observations": total_vol_days,
    }


def detect_state_transitions(classified_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identifies chronological changes in primary trend regime and volatility state.
    
    Parameters:
        classified_df (pd.DataFrame): DataFrame output from classify_market_regimes.
        
    Returns:
        List[Dict[str, Any]]: List of state transition events with date, transition_type, from_state, and to_state.
    """
    transitions: List[Dict[str, Any]] = []
    
    prev_regime: Optional[str] = None
    prev_vol_state: Optional[str] = None
    
    for _, row in classified_df.iterrows():
        current_date = str(row["date"])
        current_regime = row.get("regime")
        current_vol_state = row.get("volatility_state")
        
        # Check primary regime transition
        if pd.notna(current_regime) and current_regime is not None:
            if prev_regime is not None and current_regime != prev_regime:
                transitions.append({
                    "date": current_date,
                    "transition_type": "regime",
                    "from_state": prev_regime,
                    "to_state": str(current_regime),
                })
            prev_regime = str(current_regime)
            
        # Check volatility state transition
        if pd.notna(current_vol_state) and current_vol_state is not None:
            if prev_vol_state is not None and current_vol_state != prev_vol_state:
                transitions.append({
                    "date": current_date,
                    "transition_type": "volatility",
                    "from_state": prev_vol_state,
                    "to_state": str(current_vol_state),
                })
            prev_vol_state = str(current_vol_state)
            
    return transitions
