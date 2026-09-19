"""
Correlation and Cross-Asset Service Layer for QUANTLAB.
Composes MarketDataService and quantitative modules to deliver high-performance,
leak-free correlation matrices, pairwise metrics, rolling correlation, and comparative performance.
"""
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

from backend.app.services.market_service import market_service
from backend.app.correlation.alignment import align_two_asset_returns, align_asset_returns
from backend.app.correlation.matrix import calculate_correlation_matrix, calculate_pairwise_correlation
from backend.app.correlation.rolling import calculate_rolling_correlation
from backend.app.quant.returns import calculate_daily_returns, calculate_cumulative_returns
from backend.app.quant.volatility import calculate_annualized_volatility, get_annualization_factor
from backend.app.quant.sharpe import calculate_sharpe_ratio
from backend.app.quant.drawdown import calculate_drawdown_series, calculate_max_drawdown


def _clean_val(val: Any) -> Optional[float]:
    """Cleans NaN / Inf to None for JSON compliance."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if np.isnan(val) or np.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    return val


class CorrelationService:
    DEFAULT_ASSETS = ["Gold", "Bitcoin", "NVIDIA"]

    def __init__(self):
        self.market_service = market_service

    def _get_canonical_asset_name(self, asset: str) -> str:
        """Validates and normalizes asset identifier."""
        canonical = self.market_service.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(f"Asset '{asset}' is not recognized. Supported assets: Gold, Bitcoin, NVIDIA.")
        return canonical

    def _load_asset_df(self, canonical: str) -> pd.DataFrame:
        """Loads and pre-sorts dataset for an asset."""
        df = self.market_service._get_dataset(canonical)
        return df.sort_values("date", ascending=True).reset_index(drop=True)

    def get_pairwise_correlation(
        self,
        asset_a: str,
        asset_b: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates pairwise Pearson correlation on aligned dates."""
        can_a = self._get_canonical_asset_name(asset_a)
        can_b = self._get_canonical_asset_name(asset_b)
        
        df_a = self._load_asset_df(can_a)
        df_b = self._load_asset_df(can_b)
        
        res = calculate_pairwise_correlation(
            df_a, df_b, can_a, can_b, start_date=start_date, end_date=end_date
        )
        return {
            "asset_a": can_a,
            "asset_b": can_b,
            "correlation": _clean_val(res["correlation"]),
            "observations": res["observations"],
            "start_date": res["start_date"],
            "end_date": res["end_date"],
        }

    def get_correlation_matrix(
        self,
        assets: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates cross-asset correlation matrix for specified or default assets."""
        if not assets:
            target_assets = self.DEFAULT_ASSETS
        else:
            target_assets = [self._get_canonical_asset_name(a) for a in assets]
            # Remove duplicates while preserving deterministic order
            target_assets = list(dict.fromkeys(target_assets))
            
        dfs = {a: self._load_asset_df(a) for a in target_assets}
        
        raw_result = calculate_correlation_matrix(dfs, start_date=start_date, end_date=end_date)
        
        cleaned_matrix: Dict[str, Dict[str, Optional[float]]] = {}
        for a1, row in raw_result["matrix"].items():
            cleaned_matrix[a1] = {a2: _clean_val(val) for a2, val in row.items()}
            
        return {
            "assets": raw_result["assets"],
            "matrix": cleaned_matrix,
            "observation_counts": raw_result["observation_counts"],
            "start_date": raw_result["start_date"],
            "end_date": raw_result["end_date"],
        }

    def get_rolling_correlation(
        self,
        asset_a: str,
        asset_b: str,
        window: int = 30,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates rolling correlation time-series between two assets."""
        can_a = self._get_canonical_asset_name(asset_a)
        can_b = self._get_canonical_asset_name(asset_b)
        
        df_a = self._load_asset_df(can_a)
        df_b = self._load_asset_df(can_b)
        
        rolling_df = calculate_rolling_correlation(
            df_a, df_b, can_a, can_b, window=window, start_date=start_date, end_date=end_date
        )
        
        records = []
        for row in rolling_df.itertuples(index=False):
            records.append({
                "date": row.date,
                "correlation": _clean_val(row.rolling_correlation)
            })
            
        return {
            "asset_a": can_a,
            "asset_b": can_b,
            "window": window,
            "count": len(records),
            "data": records,
        }

    def get_asset_comparison(
        self,
        assets: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Composes Phase 4 quantitative metrics to provide comparative cross-asset performance."""
        if not assets:
            target_assets = self.DEFAULT_ASSETS
        else:
            target_assets = [self._get_canonical_asset_name(a) for a in assets]
            target_assets = list(dict.fromkeys(target_assets))
            
        comparison_list = []
        all_starts = []
        all_ends = []
        
        dfs_for_alignment = {}
        
        for asset in target_assets:
            df = self._load_asset_df(asset)
            ann_factor = get_annualization_factor(asset)
            
            if start_date:
                df = df[df["date"] >= start_date]
            if end_date:
                df = df[df["date"] <= end_date]
                
            df = df.reset_index(drop=True)
            if df.empty:
                continue
                
            dfs_for_alignment[asset] = df
            
            prices = df["close"]
            daily_ret = calculate_daily_returns(prices)
            cum_ret = calculate_cumulative_returns(daily_ret)
            
            total_ret = float(cum_ret.iloc[-1]) if not cum_ret.empty else 0.0
            
            # Annualized return (CAGR)
            records_count = len(df)
            ann_ret = None
            if records_count > 1:
                try:
                    d_start = datetime.strptime(str(df["date"].iloc[0]), "%Y-%m-%d")
                    d_end = datetime.strptime(str(df["date"].iloc[-1]), "%Y-%m-%d")
                    days_elapsed = max((d_end - d_start).days, 1)
                    years_elapsed = days_elapsed / 365.25
                    if years_elapsed > 0 and (1.0 + total_ret) > 0:
                        ann_ret = float((1.0 + total_ret) ** (1.0 / years_elapsed) - 1.0)
                except Exception:
                    ann_ret = None
                    
            ann_vol = calculate_annualized_volatility(daily_ret, annualization_factor=ann_factor)
            sharpe = calculate_sharpe_ratio(daily_ret, risk_free_rate_annual=0.0, annualization_factor=ann_factor)
            dd_series = calculate_drawdown_series(prices)
            mdd = calculate_max_drawdown(dd_series)
            
            s_date = str(df["date"].min())
            e_date = str(df["date"].max())
            all_starts.append(s_date)
            all_ends.append(e_date)
            
            comparison_list.append({
                "asset": asset,
                "start_date": s_date,
                "end_date": e_date,
                "records": records_count,
                "total_return": _clean_val(total_ret),
                "annualized_return": _clean_val(ann_ret),
                "annualized_volatility": _clean_val(ann_vol),
                "sharpe_ratio": _clean_val(sharpe),
                "maximum_drawdown": _clean_val(mdd),
            })
            
        # Determine aligned overlapping count across all selected assets
        aligned_count = None
        if len(dfs_for_alignment) >= 2:
            aligned_df = align_asset_returns(dfs_for_alignment, start_date=start_date, end_date=end_date, how="inner")
            aligned_count = len(aligned_df)
            
        return {
            "assets": comparison_list,
            "start_date": min(all_starts) if all_starts else (start_date or ""),
            "end_date": max(all_ends) if all_ends else (end_date or ""),
            "aligned_records": aligned_count,
        }


# Global singleton
correlation_service = CorrelationService()
