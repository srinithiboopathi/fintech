"""
Validation Module for Market Regime Analysis (Phase 8).
Ensures parameters, lookback windows, and threshold modes satisfy quantitative constraints.
"""
from typing import Optional
from backend.app.quant.validation import validate_positive_integer
from backend.app.regimes.enums import ThresholdMode


def validate_regime_parameters(
    trend_window: int = 50,
    volatility_window: int = 20,
    threshold_mode: str = "historical_descriptive",
) -> None:
    """
    Validates input parameters for regime analysis.
    
    Parameters:
        trend_window (int): Moving average period for trend classification (>= 2).
        volatility_window (int): Lookback window for rolling volatility (>= 2).
        threshold_mode (str): 'historical_descriptive' or 'expanding_threshold'.
        
    Raises:
        ValueError: If any parameter violates constraints.
    """
    validate_positive_integer(trend_window, name="trend_window", min_value=2)
    validate_positive_integer(volatility_window, name="volatility_window", min_value=2)
    
    valid_modes = [m.value for m in ThresholdMode]
    if threshold_mode not in valid_modes:
        raise ValueError(
            f"Invalid threshold_mode '{threshold_mode}'. Must be one of: {valid_modes}"
        )
