"""
backend/app/services/market_regimes.py

Market Regime Analysis Service.
Identifies macroeconomic market regimes (trend state, volatility state, and combined regime)
from historical price time series strictly using deterministic, causal mathematical rules.

Specifications:
1. Trend Classification (SMA-based):
   - Default trend period: 50
   - BULLISH: close > SMA
   - BEARISH: close < SMA
   - SIDEWAYS: close within neutral band of SMA (or close == SMA)
   - UNKNOWN: insufficient historical data for SMA warmup

2. Volatility Classification (Rolling Sample Standard Deviation, ddof=1):
   - Default volatility window: 20
   - HIGH_VOLATILITY: rolling volatility > threshold/median
   - LOW_VOLATILITY: rolling volatility <= threshold/median
   - UNKNOWN: insufficient historical data for volatility warmup

3. Combined Regimes:
   - BULLISH_LOW_VOL, BULLISH_HIGH_VOL
   - BEARISH_LOW_VOL, BEARISH_HIGH_VOL
   - SIDEWAYS_LOW_VOL, SIDEWAYS_HIGH_VOL
   - UNKNOWN (if either trend or volatility is UNKNOWN)

4. Zero Look-Ahead Bias:
   - At timestamp t, regime classification uses ONLY data available at indices <= t.
   - When volatility_threshold is not specified, causal expanding median is used.
   - Mutating future prices strictly leaves past regime classifications unchanged.

5. Strategy-by-Regime Attribution:
   - Factual attribution of strategy performance and maximum drawdown across detected regimes.
   - Zero subjective ranking ("best/worst/winner/loser").
"""

import math
import statistics
from typing import Dict, List, Optional, Tuple, Any

from app.models.schemas import (
    CleanHistoricalPoint,
    MarketRegimePoint,
    MarketRegimesParameters,
    MarketRegimesResponse,
    RegimeSummaryItem,
    MarketRegimesSummaryResponse,
    StrategyRegimePerformanceItem,
    StrategyRegimePerformanceResponse,
)
from app.services.indicators import calculate_sma
from app.services.risk_metrics import calculate_daily_returns, calculate_rolling_volatility
from app.services.strategies import StrategyDispatcher, SUPPORTED_STRATEGIES
from app.services.backtesting import BacktestingEngine
from app.utils.exceptions import (
    InvalidRegimeParameterError,
    InsufficientHistoricalDataError,
)

MAX_REGIME_PERIOD = 500
MIN_TREND_PERIOD = 1
MIN_VOLATILITY_WINDOW = 2


class MarketRegimeService:
    """Service for deterministic, causal market regime analysis and strategy attribution."""

    def __init__(self):
        self.strategy_dispatcher = StrategyDispatcher()
        self.backtesting_engine = BacktestingEngine()

    def validate_parameters(
        self,
        trend_period: int,
        volatility_window: int,
        volatility_threshold: Optional[float] = None,
        trend_threshold: float = 0.0,
    ) -> None:
        """
        Validates market regime parameters against bounded constraints.

        Raises:
            InvalidRegimeParameterError: If any parameter is out of bounds or invalid type.
        """
        if not isinstance(trend_period, int) or trend_period < MIN_TREND_PERIOD or trend_period > MAX_REGIME_PERIOD:
            raise InvalidRegimeParameterError(
                f"Trend period must be an integer between {MIN_TREND_PERIOD} and {MAX_REGIME_PERIOD}. Received: {trend_period}"
            )

        if not isinstance(volatility_window, int) or volatility_window < MIN_VOLATILITY_WINDOW or volatility_window > MAX_REGIME_PERIOD:
            raise InvalidRegimeParameterError(
                f"Volatility window must be an integer between {MIN_VOLATILITY_WINDOW} and {MAX_REGIME_PERIOD}. Received: {volatility_window}"
            )

        if volatility_threshold is not None:
            if not isinstance(volatility_threshold, (int, float)) or volatility_threshold <= 0.0 or volatility_threshold > 100.0:
                raise InvalidRegimeParameterError(
                    f"Volatility threshold must be a positive number between 0.0 and 100.0. Received: {volatility_threshold}"
                )

        if not isinstance(trend_threshold, (int, float)) or trend_threshold < 0.0 or trend_threshold > 1.0:
            raise InvalidRegimeParameterError(
                f"Trend neutral threshold must be a float between 0.0 and 1.0. Received: {trend_threshold}"
            )

    def classify_regimes(
        self,
        clean_points: List[CleanHistoricalPoint],
        trend_period: int = 50,
        volatility_window: int = 20,
        volatility_threshold: Optional[float] = None,
        trend_threshold: float = 0.0,
    ) -> Tuple[List[MarketRegimePoint], MarketRegimesParameters]:
        """
        Classifies chronological market records into trend, volatility, and combined regimes.

        Args:
            clean_points: Validated historical observations from Step 3.
            trend_period: SMA lookback window (default: 50).
            volatility_window: Rolling returns volatility window (default: 20).
            volatility_threshold: Fixed threshold. If None, causal expanding median is used.
            trend_threshold: Neutral band fraction for sideways trend (default: 0.0).

        Returns:
            Tuple of (List[MarketRegimePoint], MarketRegimesParameters).
        """
        self.validate_parameters(
            trend_period=trend_period,
            volatility_window=volatility_window,
            volatility_threshold=volatility_threshold,
            trend_threshold=trend_threshold,
        )

        n = len(clean_points)
        if n == 0:
            raise InsufficientHistoricalDataError("No historical data available for regime analysis.")

        # Ensure strict chronological order
        sorted_points = sorted(clean_points, key=lambda p: p.timestamp)
        prices = [p.close for p in sorted_points]

        # 1. Compute SMA
        sma_values = calculate_sma(prices, period=trend_period, precision=4)

        # 2. Compute Daily Returns & Rolling Volatility
        returns = calculate_daily_returns(prices, precision=4)
        vol_values = calculate_rolling_volatility(returns, period=volatility_window, precision=4)

        # Calculate dataset median for reporting in parameters (if threshold is None)
        valid_vols = [v for v in vol_values if v is not None]
        dataset_median_vol = round(float(statistics.median(valid_vols)), 4) if valid_vols else None

        reported_threshold = volatility_threshold if volatility_threshold is not None else dataset_median_vol

        parameters = MarketRegimesParameters(
            trend_period=trend_period,
            volatility_window=volatility_window,
            volatility_threshold=reported_threshold,
            trend_threshold=trend_threshold,
        )

        regime_points: List[MarketRegimePoint] = []
        expanding_valid_vols: List[float] = []

        for i in range(n):
            ts = sorted_points[i].timestamp
            close_p = prices[i]
            sma_val = sma_values[i]
            vol_val = vol_values[i]

            # 3. Classify Trend
            if sma_val is None:
                trend_state = "UNKNOWN"
            else:
                neutral_band = sma_val * trend_threshold
                if close_p > (sma_val + neutral_band):
                    trend_state = "BULLISH"
                elif close_p < (sma_val - neutral_band):
                    trend_state = "BEARISH"
                else:
                    trend_state = "SIDEWAYS"

            # 4. Classify Volatility
            if vol_val is None:
                vol_state = "UNKNOWN"
            else:
                expanding_valid_vols.append(vol_val)
                if volatility_threshold is not None:
                    eff_thresh = volatility_threshold
                else:
                    # Causal expanding median up to index i guarantees zero look-ahead bias
                    eff_thresh = float(statistics.median(expanding_valid_vols))

                if vol_val > eff_thresh:
                    vol_state = "HIGH_VOLATILITY"
                else:
                    vol_state = "LOW_VOLATILITY"

            # 5. Classify Combined Regime
            if trend_state == "UNKNOWN" or vol_state == "UNKNOWN":
                combined = "UNKNOWN"
            elif trend_state == "BULLISH":
                combined = "BULLISH_HIGH_VOL" if vol_state == "HIGH_VOLATILITY" else "BULLISH_LOW_VOL"
            elif trend_state == "BEARISH":
                combined = "BEARISH_HIGH_VOL" if vol_state == "HIGH_VOLATILITY" else "BEARISH_LOW_VOL"
            elif trend_state == "SIDEWAYS":
                combined = "SIDEWAYS_HIGH_VOL" if vol_state == "HIGH_VOLATILITY" else "SIDEWAYS_LOW_VOL"
            else:
                combined = "UNKNOWN"

            regime_points.append(
                MarketRegimePoint(
                    timestamp=ts,
                    close=close_p,
                    sma=sma_val,
                    rolling_volatility=vol_val,
                    trend_state=trend_state,
                    volatility_state=vol_state,
                    combined_regime=combined,
                )
            )

        return regime_points, parameters

    def summarize_regimes(
        self,
        regime_points: List[MarketRegimePoint],
    ) -> List[RegimeSummaryItem]:
        """
        Computes distribution summary across all detected combined market regimes.

        Args:
            regime_points: List of classified MarketRegimePoint.

        Returns:
            List of RegimeSummaryItem.
        """
        total = len(regime_points)
        if total == 0:
            return []

        counts: Dict[str, int] = {}
        first_dates: Dict[str, str] = {}
        last_dates: Dict[str, str] = {}

        for pt in regime_points:
            reg = pt.combined_regime
            counts[reg] = counts.get(reg, 0) + 1
            if reg not in first_dates:
                first_dates[reg] = pt.timestamp
            last_dates[reg] = pt.timestamp

        # Standard canonical ordering for output readability
        canonical_order = [
            "BULLISH_LOW_VOL",
            "BULLISH_HIGH_VOL",
            "BEARISH_LOW_VOL",
            "BEARISH_HIGH_VOL",
            "SIDEWAYS_LOW_VOL",
            "SIDEWAYS_HIGH_VOL",
            "UNKNOWN",
        ]

        summary_items: List[RegimeSummaryItem] = []
        # First include regimes present in canonical order
        for reg in canonical_order:
            if reg in counts:
                cnt = counts[reg]
                pct = round((cnt / total) * 100.0, 2)
                summary_items.append(
                    RegimeSummaryItem(
                        regime=reg,
                        observation_count=cnt,
                        percentage=pct,
                        percentage_of_observations=pct,
                        start_date=first_dates.get(reg),
                        end_date=last_dates.get(reg),
                    )
                )

        # Include any remaining regimes
        for reg, cnt in counts.items():
            if reg not in canonical_order:
                pct = round((cnt / total) * 100.0, 2)
                summary_items.append(
                    RegimeSummaryItem(
                        regime=reg,
                        observation_count=cnt,
                        percentage=pct,
                        percentage_of_observations=pct,
                        start_date=first_dates.get(reg),
                        end_date=last_dates.get(reg),
                    )
                )

        return summary_items

    def analyze_strategy_performance_by_regime(
        self,
        clean_points: List[CleanHistoricalPoint],
        trend_period: int = 50,
        volatility_window: int = 20,
        volatility_threshold: Optional[float] = None,
        trend_threshold: float = 0.0,
        initial_capital: float = 10000.0,
        transaction_cost_rate: float = 0.001,
        allocation: float = 1.0,
    ) -> Tuple[List[StrategyRegimePerformanceItem], MarketRegimesParameters]:
        """
        Evaluates the factual performance of all 4 quantitative strategies across each detected market regime.

        Args:
            clean_points: Validated historical observations from Step 3.
            trend_period: SMA trend period.
            volatility_window: Volatility window.
            volatility_threshold: Volatility threshold.
            trend_threshold: Neutral trend band.
            initial_capital: Backtest initial capital.
            transaction_cost_rate: Backtest transaction cost rate.
            allocation: Portfolio capital allocation fraction.

        Returns:
            Tuple of (List[StrategyRegimePerformanceItem], MarketRegimesParameters).
        """
        regime_points, parameters = self.classify_regimes(
            clean_points=clean_points,
            trend_period=trend_period,
            volatility_window=volatility_window,
            volatility_threshold=volatility_threshold,
            trend_threshold=trend_threshold,
        )

        # Create timestamp to regime mapping
        regime_by_ts = {pt.timestamp: pt.combined_regime for pt in regime_points}

        # Unique active regimes in dataset
        all_regimes = list(dict.fromkeys(pt.combined_regime for pt in regime_points))

        performance_items: List[StrategyRegimePerformanceItem] = []

        for strategy_name in SUPPORTED_STRATEGIES:
            # 1. Generate signals using Step 9 strategy dispatcher
            signals, _ = self.strategy_dispatcher.generate_signals(strategy_name, clean_points)

            # 2. Run backtest using Step 8 engine
            asset_name = clean_points[0].asset if clean_points else "Asset"
            symbol = clean_points[0].symbol if clean_points else "SYMBOL"
            backtest_result = self.backtesting_engine.run_simulation(
                asset=asset_name,
                symbol=symbol,
                clean_points=clean_points,
                initial_capital=initial_capital,
                transaction_cost_rate=transaction_cost_rate,
                allocation_fraction=allocation,
                signals=signals,
            )

            # Map trades by timestamp
            trades_by_ts: Dict[str, int] = {}
            for t in backtest_result.trade_history:
                trades_by_ts[t.timestamp] = trades_by_ts.get(t.timestamp, 0) + 1

            # Group daily portfolio returns by regime
            # Daily returns are defined for equity curve points i >= 1
            eq_curve = backtest_result.equity_curve
            regime_returns: Dict[str, List[float]] = {r: [] for r in all_regimes}
            regime_trades: Dict[str, int] = {r: 0 for r in all_regimes}
            regime_obs: Dict[str, int] = {r: 0 for r in all_regimes}

            for i in range(1, len(eq_curve)):
                ts = eq_curve[i].timestamp
                r_type = regime_by_ts.get(ts, "UNKNOWN")
                prev_val = eq_curve[i - 1].portfolio_value
                curr_val = eq_curve[i].portfolio_value
                daily_pct_ret = ((curr_val - prev_val) / prev_val) * 100.0 if prev_val > 0 else 0.0

                regime_obs[r_type] = regime_obs.get(r_type, 0) + 1
                regime_returns.setdefault(r_type, []).append(daily_pct_ret)
                if ts in trades_by_ts:
                    regime_trades[r_type] = regime_trades.get(r_type, 0) + trades_by_ts[ts]

            # Compute compound return and maximum drawdown for each regime
            for r_type in all_regimes:
                obs_count = regime_obs.get(r_type, 0)
                trade_count = regime_trades.get(r_type, 0)
                rets = regime_returns.get(r_type, [])

                if obs_count == 0 or len(rets) == 0:
                    total_ret = 0.0
                    mdd = 0.0
                else:
                    # Compound return across days spent in this regime:
                    # product(1 + r/100) - 1
                    compound_factor = 1.0
                    peak = 1.0
                    max_dd = 0.0
                    for r in rets:
                        compound_factor *= (1.0 + (r / 100.0))
                        if compound_factor > peak:
                            peak = compound_factor
                        dd = ((compound_factor - peak) / peak) * 100.0 if peak > 0 else 0.0
                        if dd < max_dd:
                            max_dd = dd

                    total_ret = round((compound_factor - 1.0) * 100.0, 4)
                    mdd = round(abs(max_dd), 4)

                performance_items.append(
                    StrategyRegimePerformanceItem(
                        strategy=strategy_name,
                        regime=r_type,
                        observations=obs_count,
                        trades=trade_count,
                        total_return=total_ret,
                        maximum_drawdown=mdd,
                    )
                )

        return performance_items, parameters
