"""
Market Regime Classification Engine for QUANTLAB (Phase 8).
Deterministic historical classification of Trend (BULL/BEAR) and Volatility State (HIGH/LOW).
"""
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

from backend.app.quant.indicators import calculate_sma
from backend.app.quant.returns import calculate_daily_returns
from backend.app.quant.volatility import calculate_rolling_annualized_volatility, get_annualization_factor
from backend.app.regimes.enums import MarketRegime, VolatilityState, ThresholdMode
from backend.app.regimes.validation import validate_regime_parameters


def classify_market_regimes(
    df: pd.DataFrame,
    asset: str,
    trend_window: int = 50,
    volatility_window: int = 20,
    threshold_mode: str = "historical_descriptive",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Computes deterministic trend and volatility regimes on historical market data.
    
    Calculation Methodology:
    1. Trend Indicator:
       - Computes moving average: SMA(Close, trend_window) with center=False.
       - If Close > SMA => BULL
       - If Close <= SMA => BEAR
       - Warm-up period (first trend_window - 1 observations) => None
       
    2. Volatility State:
       - Computes daily returns and rolling annualized volatility over volatility_window with center=False.
       - In 'historical_descriptive' mode: uses median of all valid rolling volatility values across the sample.
       - In 'expanding_threshold' mode: uses expanding median up to date t, guaranteeing causal point-in-time calculation.
       - If Rolling Volatility > Threshold => HIGH_VOLATILITY
       - If Rolling Volatility <= Threshold => LOW_VOLATILITY
       - Warm-up period => None
       
    Important: Indicators and thresholds are computed on the full historical dataset BEFORE date filtering
    to preserve lookback window integrity without forward-filling or truncation.
    
    Parameters:
        df (pd.DataFrame): DataFrame containing 'date' and 'close' columns sorted chronologically.
        asset (str): Asset name for annualization factor determination.
        trend_window (int): Trend SMA period (default 50).
        volatility_window (int): Volatility rolling period (default 20).
        threshold_mode (str): 'historical_descriptive' or 'expanding_threshold'.
        start_date (str, optional): Filter output from start date (YYYY-MM-DD).
        end_date (str, optional): Filter output up to end date (YYYY-MM-DD).
        
    Returns:
        pd.DataFrame: DataFrame containing daily regime indicators and state classifications.
    """
    validate_regime_parameters(
        trend_window=trend_window,
        volatility_window=volatility_window,
        threshold_mode=threshold_mode,
    )
    
    if df.empty or "close" not in df.columns or "date" not in df.columns:
        raise ValueError("DataFrame must contain 'date' and 'close' columns with historical data.")
        
    # Work on sorted copy
    res_df = df.copy().sort_values("date").reset_index(drop=True)
    res_df["close"] = res_df["close"].astype(float)
    
    # 1. Trend Calculation
    res_df["trend_value"] = calculate_sma(res_df["close"], period=trend_window)
    res_df["trend_window"] = trend_window
    
    # Classify Primary Regime (BULL / BEAR / None)
    res_df["regime"] = None
    valid_trend_mask = res_df["trend_value"].notna()
    res_df.loc[valid_trend_mask & (res_df["close"] > res_df["trend_value"]), "regime"] = MarketRegime.BULL.value
    res_df.loc[valid_trend_mask & (res_df["close"] <= res_df["trend_value"]), "regime"] = MarketRegime.BEAR.value
    
    # 2. Daily Returns & Rolling Volatility Calculation
    daily_returns = calculate_daily_returns(res_df["close"])
    res_df["daily_return"] = daily_returns
    
    ann_factor = get_annualization_factor(asset)
    res_df["rolling_volatility"] = calculate_rolling_annualized_volatility(
        daily_returns,
        window=volatility_window,
        annualization_factor=ann_factor,
    )
    res_df["volatility_window"] = volatility_window
    
    # 3. Volatility Threshold Determination
    if threshold_mode == ThresholdMode.EXPANDING_THRESHOLD.value:
        # Causal expanding median up to date t
        res_df["volatility_threshold"] = (
            res_df["rolling_volatility"]
            .expanding(min_periods=1)
            .median()
        )
    else:
        # Historical descriptive full-sample median
        valid_vols = res_df["rolling_volatility"].dropna()
        median_val = float(valid_vols.median()) if not valid_vols.empty else np.nan
        res_df["volatility_threshold"] = median_val
        
    # Classify Volatility State (HIGH_VOLATILITY / LOW_VOLATILITY / None)
    res_df["volatility_state"] = None
    valid_vol_mask = res_df["rolling_volatility"].notna() & res_df["volatility_threshold"].notna()
    res_df.loc[
        valid_vol_mask & (res_df["rolling_volatility"] > res_df["volatility_threshold"]),
        "volatility_state",
    ] = VolatilityState.HIGH_VOLATILITY.value
    res_df.loc[
        valid_vol_mask & (res_df["rolling_volatility"] <= res_df["volatility_threshold"]),
        "volatility_state",
    ] = VolatilityState.LOW_VOLATILITY.value
    
    # Set asset column
    res_df["asset"] = asset
    
    # 4. Filter by requested date range after indicator computation
    if start_date:
        res_df = res_df[res_df["date"] >= start_date].copy()
    if end_date:
        res_df = res_df[res_df["date"] <= end_date].copy()
        
    return res_df.reset_index(drop=True)
