"""
Strategy Service Layer for QUANTLAB (Phase 6).
Orchestrates deterministic trading strategy signal generation, parameter validation,
warm-up preservation, and standardized signal serialization over historical market datasets.
"""
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd

from backend.app.services.market_service import market_service
from backend.app.strategies.enums import SignalType, StrategyType
from backend.app.strategies.validation import (
    validate_sma_parameters,
    validate_ema_parameters,
    validate_momentum_parameters,
    validate_mean_reversion_parameters,
    validate_strategy_name,
)
from backend.app.strategies.sma_crossover import calculate_sma_crossover_signals
from backend.app.strategies.ema_trend import calculate_ema_trend_signals
from backend.app.strategies.momentum import calculate_momentum_signals
from backend.app.strategies.mean_reversion import calculate_mean_reversion_signals


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


class StrategyService:
    """Service layer managing multi-asset strategy signal pipelines."""

    def __init__(self):
        self.market_service = market_service

    def _get_sorted_asset_data(self, asset: str) -> Tuple[pd.DataFrame, str]:
        """Loads and returns sorted historical dataset for asset."""
        canonical = self.market_service.normalize_asset_name(asset)
        if not canonical:
            raise KeyError(
                f"Asset '{asset}' is not recognized. Supported assets: Gold, Bitcoin, NVIDIA."
            )

        df = self.market_service._get_dataset(canonical)
        sorted_df = df.sort_values("date", ascending=True).reset_index(drop=True)
        return sorted_df, canonical

    def get_sma_crossover_signals(
        self,
        asset: str,
        fast_period: int = 20,
        slow_period: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates SMA Crossover signals with full warm-up history preservation."""
        validate_sma_parameters(fast_period, slow_period)
        df, canonical = self._get_sorted_asset_data(asset)

        # Calculate on full history to prevent warm-up distortion
        sig_df = calculate_sma_crossover_signals(
            prices=df["close"],
            fast_period=fast_period,
            slow_period=slow_period,
        )
        sig_df["date"] = df["date"]

        # Date filtering after calculation
        if start_date:
            sig_df = sig_df[sig_df["date"] >= start_date]
        if end_date:
            sig_df = sig_df[sig_df["date"] <= end_date]

        records = []
        buy_cnt = 0
        sell_cnt = 0
        hold_cnt = 0

        for row in sig_df.itertuples(index=False):
            sig_val = row.signal
            if sig_val == SignalType.BUY.value:
                buy_cnt += 1
            elif sig_val == SignalType.SELL.value:
                sell_cnt += 1
            else:
                hold_cnt += 1

            records.append({
                "date": str(row.date),
                "asset": canonical,
                "close": float(row.close),
                "strategy": StrategyType.SMA_CROSSOVER.value,
                "signal": sig_val,
                "fast_sma": _clean_nan(row.fast_sma),
                "slow_sma": _clean_nan(row.slow_sma),
                "short_ema": None,
                "long_ema": None,
                "momentum": None,
                "moving_average": None,
                "deviation": None,
            })

        return {
            "asset": canonical,
            "strategy": StrategyType.SMA_CROSSOVER.value,
            "parameters": {
                "fast_period": fast_period,
                "slow_period": slow_period,
            },
            "start_date": start_date,
            "end_date": end_date,
            "count": len(records),
            "summary": {
                "buy": buy_cnt,
                "sell": sell_cnt,
                "hold": hold_cnt,
                "total": len(records),
            },
            "data": records,
        }

    def get_ema_trend_signals(
        self,
        asset: str,
        short_period: int = 20,
        long_period: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates EMA Trend signals with full warm-up history preservation."""
        validate_ema_parameters(short_period, long_period)
        df, canonical = self._get_sorted_asset_data(asset)

        sig_df = calculate_ema_trend_signals(
            prices=df["close"],
            short_period=short_period,
            long_period=long_period,
        )
        sig_df["date"] = df["date"]

        if start_date:
            sig_df = sig_df[sig_df["date"] >= start_date]
        if end_date:
            sig_df = sig_df[sig_df["date"] <= end_date]

        records = []
        buy_cnt = 0
        sell_cnt = 0
        hold_cnt = 0

        for row in sig_df.itertuples(index=False):
            sig_val = row.signal
            if sig_val == SignalType.BUY.value:
                buy_cnt += 1
            elif sig_val == SignalType.SELL.value:
                sell_cnt += 1
            else:
                hold_cnt += 1

            records.append({
                "date": str(row.date),
                "asset": canonical,
                "close": float(row.close),
                "strategy": StrategyType.EMA_TREND.value,
                "signal": sig_val,
                "fast_sma": None,
                "slow_sma": None,
                "short_ema": _clean_nan(row.short_ema),
                "long_ema": _clean_nan(row.long_ema),
                "momentum": None,
                "moving_average": None,
                "deviation": None,
            })

        return {
            "asset": canonical,
            "strategy": StrategyType.EMA_TREND.value,
            "parameters": {
                "short_period": short_period,
                "long_period": long_period,
            },
            "start_date": start_date,
            "end_date": end_date,
            "count": len(records),
            "summary": {
                "buy": buy_cnt,
                "sell": sell_cnt,
                "hold": hold_cnt,
                "total": len(records),
            },
            "data": records,
        }

    def get_momentum_signals(
        self,
        asset: str,
        lookback: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates Momentum signals with full warm-up history preservation."""
        validate_momentum_parameters(lookback)
        df, canonical = self._get_sorted_asset_data(asset)

        sig_df = calculate_momentum_signals(
            prices=df["close"],
            lookback=lookback,
        )
        sig_df["date"] = df["date"]

        if start_date:
            sig_df = sig_df[sig_df["date"] >= start_date]
        if end_date:
            sig_df = sig_df[sig_df["date"] <= end_date]

        records = []
        buy_cnt = 0
        sell_cnt = 0
        hold_cnt = 0

        for row in sig_df.itertuples(index=False):
            sig_val = row.signal
            if sig_val == SignalType.BUY.value:
                buy_cnt += 1
            elif sig_val == SignalType.SELL.value:
                sell_cnt += 1
            else:
                hold_cnt += 1

            records.append({
                "date": str(row.date),
                "asset": canonical,
                "close": float(row.close),
                "strategy": StrategyType.MOMENTUM.value,
                "signal": sig_val,
                "fast_sma": None,
                "slow_sma": None,
                "short_ema": None,
                "long_ema": None,
                "momentum": _clean_nan(row.momentum),
                "moving_average": None,
                "deviation": None,
            })

        return {
            "asset": canonical,
            "strategy": StrategyType.MOMENTUM.value,
            "parameters": {
                "lookback": lookback,
            },
            "start_date": start_date,
            "end_date": end_date,
            "count": len(records),
            "summary": {
                "buy": buy_cnt,
                "sell": sell_cnt,
                "hold": hold_cnt,
                "total": len(records),
            },
            "data": records,
        }

    def get_mean_reversion_signals(
        self,
        asset: str,
        window: int = 20,
        threshold: float = 0.02,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates Mean Reversion signals with full warm-up history preservation."""
        validate_mean_reversion_parameters(window, threshold)
        df, canonical = self._get_sorted_asset_data(asset)

        sig_df = calculate_mean_reversion_signals(
            prices=df["close"],
            window=window,
            threshold=threshold,
        )
        sig_df["date"] = df["date"]

        if start_date:
            sig_df = sig_df[sig_df["date"] >= start_date]
        if end_date:
            sig_df = sig_df[sig_df["date"] <= end_date]

        records = []
        buy_cnt = 0
        sell_cnt = 0
        hold_cnt = 0

        for row in sig_df.itertuples(index=False):
            sig_val = row.signal
            if sig_val == SignalType.BUY.value:
                buy_cnt += 1
            elif sig_val == SignalType.SELL.value:
                sell_cnt += 1
            else:
                hold_cnt += 1

            records.append({
                "date": str(row.date),
                "asset": canonical,
                "close": float(row.close),
                "strategy": StrategyType.MEAN_REVERSION.value,
                "signal": sig_val,
                "fast_sma": None,
                "slow_sma": None,
                "short_ema": None,
                "long_ema": None,
                "momentum": None,
                "moving_average": _clean_nan(row.moving_average),
                "deviation": _clean_nan(row.deviation),
            })

        return {
            "asset": canonical,
            "strategy": StrategyType.MEAN_REVERSION.value,
            "parameters": {
                "window": window,
                "threshold": threshold,
            },
            "start_date": start_date,
            "end_date": end_date,
            "count": len(records),
            "summary": {
                "buy": buy_cnt,
                "sell": sell_cnt,
                "hold": hold_cnt,
                "total": len(records),
            },
            "data": records,
        }

    def get_signals(
        self,
        asset: str,
        strategy: str,
        fast_period: int = 20,
        slow_period: int = 50,
        short_period: int = 20,
        long_period: int = 50,
        lookback: int = 20,
        window: int = 20,
        threshold: float = 0.02,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Unified dispatcher endpoint for all strategy signal calculations."""
        strat_enum = validate_strategy_name(strategy)

        if strat_enum == StrategyType.SMA_CROSSOVER:
            return self.get_sma_crossover_signals(
                asset=asset,
                fast_period=fast_period,
                slow_period=slow_period,
                start_date=start_date,
                end_date=end_date,
            )
        elif strat_enum == StrategyType.EMA_TREND:
            return self.get_ema_trend_signals(
                asset=asset,
                short_period=short_period,
                long_period=long_period,
                start_date=start_date,
                end_date=end_date,
            )
        elif strat_enum == StrategyType.MOMENTUM:
            return self.get_momentum_signals(
                asset=asset,
                lookback=lookback,
                start_date=start_date,
                end_date=end_date,
            )
        elif strat_enum == StrategyType.MEAN_REVERSION:
            return self.get_mean_reversion_signals(
                asset=asset,
                window=window,
                threshold=threshold,
                start_date=start_date,
                end_date=end_date,
            )
        else:
            raise ValueError(f"Unhandled strategy: {strategy}")


# Global singleton service instance
strategy_service = StrategyService()
