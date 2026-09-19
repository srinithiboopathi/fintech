"""
Quantitative Service Layer for QUANTLAB.
Orchestrates quantitative indicator calculations, return series, risk-adjusted metrics,
and summary analytics over verified historical market datasets.
"""
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd

from backend.app.services.market_service import market_service
from backend.app.quant.indicators import calculate_sma, calculate_ema
from backend.app.quant.returns import calculate_daily_returns, calculate_cumulative_returns
from backend.app.quant.volatility import (
    calculate_rolling_volatility,
    calculate_annualized_volatility,
    calculate_rolling_annualized_volatility,
    get_annualization_factor,
)
from backend.app.quant.sharpe import calculate_sharpe_ratio, calculate_rolling_sharpe
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown
from backend.app.quant.rolling import calculate_rolling_metrics


def _clean_nan(val: Any) -> Optional[float]:
    """Converts NaN / Inf values to None for clean Pydantic/JSON serialization."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    return val


class QuantService:
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

    def get_indicators(
        self,
        asset: str,
        sma_period: int = 20,
        ema_period: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates SMA and EMA technical indicators."""
        df, canonical = self._get_sorted_asset_data(asset)
        
        # Calculate indicators on full history to preserve proper warm-up
        prices = df["close"]
        sma_series = calculate_sma(prices, sma_period)
        ema_series = calculate_ema(prices, ema_period)
        
        calc_df = pd.DataFrame({
            "date": df["date"],
            "close": prices,
            "sma": sma_series,
            "ema": ema_series
        })
        
        # Apply date filters
        if start_date:
            calc_df = calc_df[calc_df["date"] >= start_date]
        if end_date:
            calc_df = calc_df[calc_df["date"] <= end_date]
            
        records = []
        for row in calc_df.itertuples(index=False):
            records.append({
                "date": row.date,
                "close": float(row.close),
                "sma": _clean_nan(row.sma),
                "ema": _clean_nan(row.ema)
            })
            
        return {
            "asset": canonical,
            "frequency": "daily",
            "sma_period": sma_period,
            "ema_period": ema_period,
            "count": len(records),
            "data": records
        }

    def get_returns(
        self,
        asset: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates daily and compounded cumulative returns."""
        df, canonical = self._get_sorted_asset_data(asset)
        
        # Apply date filter before returns if custom window is requested, or compute on slice
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]
            
        df = df.reset_index(drop=True)
        prices = df["close"]
        daily_ret = calculate_daily_returns(prices)
        cum_ret = calculate_cumulative_returns(daily_ret)
        
        records = []
        for i in range(len(df)):
            records.append({
                "date": df["date"].iloc[i],
                "close": float(prices.iloc[i]),
                "daily_return": _clean_nan(daily_ret.iloc[i]),
                "cumulative_return": _clean_nan(cum_ret.iloc[i])
            })
            
        return {
            "asset": canonical,
            "frequency": "daily",
            "count": len(records),
            "data": records
        }

    def get_volatility(
        self,
        asset: str,
        window: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates rolling and annualized volatility."""
        df, canonical = self._get_sorted_asset_data(asset)
        annualization_factor = get_annualization_factor(canonical)
        
        prices = df["close"]
        daily_ret = calculate_daily_returns(prices)
        rolling_vol = calculate_rolling_volatility(daily_ret, window=window)
        rolling_ann_vol = calculate_rolling_annualized_volatility(daily_ret, window=window, annualization_factor=annualization_factor)
        
        calc_df = pd.DataFrame({
            "date": df["date"],
            "rolling_volatility": rolling_vol,
            "annualized_volatility": rolling_ann_vol
        })
        
        if start_date:
            calc_df = calc_df[calc_df["date"] >= start_date]
        if end_date:
            calc_df = calc_df[calc_df["date"] <= end_date]
            
        records = []
        for row in calc_df.itertuples(index=False):
            records.append({
                "date": row.date,
                "rolling_volatility": _clean_nan(row.rolling_volatility),
                "annualized_volatility": _clean_nan(row.annualized_volatility)
            })
            
        return {
            "asset": canonical,
            "window": window,
            "annualization_factor": annualization_factor,
            "count": len(records),
            "data": records
        }

    def get_risk_metrics(
        self,
        asset: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        risk_free_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates summary risk metrics (Annualized Volatility, Sharpe Ratio, Maximum Drawdown)."""
        df, canonical = self._get_sorted_asset_data(asset)
        annualization_factor = get_annualization_factor(canonical)
        
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]
            
        df = df.reset_index(drop=True)
        if df.empty:
            return {
                "asset": canonical,
                "start_date": start_date or "",
                "end_date": end_date or "",
                "records": 0,
                "risk_free_rate": risk_free_rate,
                "annualization_factor": annualization_factor,
                "annualized_volatility": None,
                "sharpe_ratio": None,
                "maximum_drawdown": None,
            }
            
        prices = df["close"]
        daily_ret = calculate_daily_returns(prices)
        
        ann_vol = calculate_annualized_volatility(daily_ret, annualization_factor=annualization_factor)
        sharpe = calculate_sharpe_ratio(daily_ret, risk_free_rate_annual=risk_free_rate, annualization_factor=annualization_factor)
        dd_series = calculate_drawdown_series(prices)
        mdd = calculate_max_drawdown(dd_series)
        
        return {
            "asset": canonical,
            "start_date": str(df["date"].min()),
            "end_date": str(df["date"].max()),
            "records": len(df),
            "risk_free_rate": risk_free_rate,
            "annualization_factor": annualization_factor,
            "annualized_volatility": _clean_nan(ann_vol),
            "sharpe_ratio": _clean_nan(sharpe),
            "maximum_drawdown": _clean_nan(mdd),
        }

    def get_rolling_performance(
        self,
        asset: str,
        window: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        risk_free_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates multi-metric rolling performance series."""
        df, canonical = self._get_sorted_asset_data(asset)
        annualization_factor = get_annualization_factor(canonical)
        
        rolling_df = calculate_rolling_metrics(
            df,
            window=window,
            risk_free_rate_annual=risk_free_rate,
            annualization_factor=annualization_factor
        )
        
        if start_date:
            rolling_df = rolling_df[rolling_df["date"] >= start_date]
        if end_date:
            rolling_df = rolling_df[rolling_df["date"] <= end_date]
            
        records = []
        for row in rolling_df.itertuples(index=False):
            records.append({
                "date": row.date,
                "rolling_return": _clean_nan(row.rolling_return),
                "rolling_volatility": _clean_nan(row.rolling_volatility),
                "rolling_sharpe": _clean_nan(row.rolling_sharpe),
                "drawdown": _clean_nan(row.drawdown),
            })
            
        return {
            "asset": canonical,
            "window": window,
            "count": len(records),
            "data": records
        }

    def get_asset_summary(
        self,
        asset: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        risk_free_rate: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculates a consolidated quantitative and statistical profile for the asset."""
        df, canonical = self._get_sorted_asset_data(asset)
        annualization_factor = get_annualization_factor(canonical)
        
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]
            
        df = df.reset_index(drop=True)
        if df.empty:
            raise ValueError(f"No records available for {canonical} in the requested date range.")
            
        prices = df["close"]
        daily_ret = calculate_daily_returns(prices)
        cum_ret = calculate_cumulative_returns(daily_ret)
        
        valid_ret = daily_ret.dropna()
        
        ann_vol = calculate_annualized_volatility(daily_ret, annualization_factor=annualization_factor)
        sharpe = calculate_sharpe_ratio(daily_ret, risk_free_rate_annual=risk_free_rate, annualization_factor=annualization_factor)
        dd_series = calculate_drawdown_series(prices)
        mdd = calculate_max_drawdown(dd_series)
        
        total_cum_ret = float(cum_ret.iloc[-1]) if not cum_ret.empty else 0.0
        latest_close = float(prices.iloc[-1])
        
        return_stats = {
            "mean": _clean_nan(valid_ret.mean()) if not valid_ret.empty else None,
            "std": _clean_nan(valid_ret.std(ddof=1)) if len(valid_ret) > 1 else None,
            "min": _clean_nan(valid_ret.min()) if not valid_ret.empty else None,
            "max": _clean_nan(valid_ret.max()) if not valid_ret.empty else None,
            "positive_days": int((valid_ret > 0).sum()),
            "negative_days": int((valid_ret < 0).sum()),
        }
        
        return {
            "asset": canonical,
            "start_date": str(df["date"].min()),
            "end_date": str(df["date"].max()),
            "records": len(df),
            "latest_close": latest_close,
            "cumulative_return": _clean_nan(total_cum_ret),
            "annualized_volatility": _clean_nan(ann_vol),
            "sharpe_ratio": _clean_nan(sharpe),
            "maximum_drawdown": _clean_nan(mdd),
            "return_statistics": return_stats
        }


# Global singleton instance
quant_service = QuantService()
