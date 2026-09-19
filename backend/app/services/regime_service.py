"""
Market Regime Service Layer for QUANTLAB (Phase 8).
Coordinates quantitative regime classification, descriptive statistics, and state transitions.
"""
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from backend.app.services.market_service import market_service
from backend.app.regimes.enums import ThresholdMode
from backend.app.regimes.validation import validate_regime_parameters
from backend.app.regimes.classification import classify_market_regimes
from backend.app.regimes.statistics import (
    calculate_regime_summary_statistics,
    detect_state_transitions,
)


def _clean_nan(val: Any) -> Optional[float]:
    """Converts NaN / Inf values to None for clean JSON serialization."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    return val


class RegimeService:
    """Service layer orchestrating market regime analysis and volatility state classification."""

    def __init__(self):
        self.market_service = market_service

    def _get_sorted_asset_data(self, asset: str) -> Tuple[pd.DataFrame, str]:
        """Loads and returns sorted historical dataset for asset."""
        canonical = self.market_service.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(f"Asset '{asset}' is not recognized. Supported assets: Gold, Bitcoin, NVIDIA.")
            
        df = self.market_service._get_dataset(canonical)
        sorted_df = df.sort_values("date", ascending=True).reset_index(drop=True)
        return sorted_df, canonical

    def get_regime_analysis(
        self,
        asset: str,
        trend_window: int = 50,
        volatility_window: int = 20,
        threshold_mode: str = ThresholdMode.HISTORICAL_DESCRIPTIVE.value,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes regime analysis for the specified asset.
        
        Indicators and volatility thresholds are computed on the full dataset first,
        and then filtered to the requested start_date / end_date range.
        """
        validate_regime_parameters(
            trend_window=trend_window,
            volatility_window=volatility_window,
            threshold_mode=threshold_mode,
        )
        
        df, canonical = self._get_sorted_asset_data(asset)
        
        # Classify on full history then filter
        classified_df = classify_market_regimes(
            df=df,
            asset=canonical,
            trend_window=trend_window,
            volatility_window=volatility_window,
            threshold_mode=threshold_mode,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Calculate summary statistics and transitions on the filtered view
        summary_stats = calculate_regime_summary_statistics(classified_df, asset=canonical)
        transitions = detect_state_transitions(classified_df)
        
        # Format daily records
        data_records = []
        for row in classified_df.itertuples(index=False):
            data_records.append({
                "date": str(row.date),
                "asset": canonical,
                "close": float(row.close),
                "trend_value": _clean_nan(row.trend_value),
                "trend_window": int(row.trend_window),
                "rolling_volatility": _clean_nan(row.rolling_volatility),
                "volatility_window": int(row.volatility_window),
                "volatility_threshold": _clean_nan(row.volatility_threshold),
                "regime": row.regime if pd.notna(row.regime) else None,
                "volatility_state": row.volatility_state if pd.notna(row.volatility_state) else None,
            })
            
        return {
            "asset": canonical,
            "trend_window": trend_window,
            "volatility_window": volatility_window,
            "threshold_mode": threshold_mode,
            "start_date": start_date,
            "end_date": end_date,
            "summary_statistics": summary_stats,
            "transitions": transitions,
            "data": data_records,
        }


# Global singleton regime service instance
regime_service = RegimeService()
