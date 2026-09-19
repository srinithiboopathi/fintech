"""
backend/app/services/strategies.py

Step 9: Quantitative Trading Strategies Service.
Implements the four institutional-grade trading strategies:
1. SMA Crossover (sma_crossover)
2. EMA Trend (ema_trend)
3. Momentum (momentum)
4. Mean Reversion (mean_reversion)

Key Principles:
1. Strategy-Agnostic Output:
   - Each strategy generates strictly generic 'BUY', 'SELL', and 'HOLD' signals.
   - No portfolio accounting or order execution logic is embedded inside strategies.
2. Zero Look-Ahead Bias:
   - Signals generated at timestamp t utilize strictly observations at indices i <= t.
   - Step 8 BacktestingEngine executes the signal at observation t + 1 at Close price P_{t+1}.
3. Parameter Hygiene:
   - All parameters are thoroughly validated.
   - Invalid parameters or unsupported strategy names raise HTTP 400 exceptions.
"""

import math
from typing import List, Dict, Optional, Tuple, Any
from app.models.schemas import (
    CleanHistoricalPoint,
    SignalPoint,
    StrategySignalPoint,
)
from app.services.indicators import indicator_service
from app.utils.exceptions import (
    UnsupportedStrategyError,
    InvalidStrategyParameterError,
)


class BaseStrategy:
    """Abstract base strategy providing common parsing and validation utilities."""

    name: str = "base"

    def parse_int_param(self, val: Any, param_name: str, min_val: int = 1) -> int:
        """Validates that a parameter is an integer >= min_val."""
        if val is None:
            raise InvalidStrategyParameterError(f"Missing required parameter '{param_name}'.")
        try:
            # Reject floats like 20.5
            val_float = float(val)
            if not val_float.is_integer():
                raise InvalidStrategyParameterError(
                    f"Parameter '{param_name}' must be an integer, got float {val}."
                )
            ival = int(val_float)
            if ival < min_val:
                raise InvalidStrategyParameterError(
                    f"Parameter '{param_name}' must be an integer >= {min_val}, got {ival}."
                )
            return ival
        except (ValueError, TypeError):
            raise InvalidStrategyParameterError(
                f"Parameter '{param_name}' must be a valid integer, got {val}."
            )

    def parse_float_param(self, val: Any, param_name: str, min_val: Optional[float] = None, strictly_positive: bool = False) -> float:
        """Validates that a parameter is a float satisfying numerical boundaries."""
        if val is None:
            raise InvalidStrategyParameterError(f"Missing required parameter '{param_name}'.")
        try:
            fval = float(val)
            if not math.isfinite(fval):
                raise InvalidStrategyParameterError(f"Parameter '{param_name}' must be a finite number.")
            if min_val is not None:
                if strictly_positive and fval <= min_val:
                    raise InvalidStrategyParameterError(
                        f"Parameter '{param_name}' must be strictly greater than {min_val}, got {fval}."
                    )
                elif not strictly_positive and fval < min_val:
                    raise InvalidStrategyParameterError(
                        f"Parameter '{param_name}' must be >= {min_val}, got {fval}."
                    )
            return fval
        except (ValueError, TypeError):
            raise InvalidStrategyParameterError(
                f"Parameter '{param_name}' must be a valid numeric value, got {val}."
            )


class SMACrossoverStrategy(BaseStrategy):
    """
    1. SMA Crossover Strategy:
    Generates signals based on moving average crossings:
    - BUY: short SMA crosses from <= long SMA to > long SMA.
    - SELL: short SMA crosses from >= long SMA to < long SMA.
    - HOLD: otherwise.
    Note: Signal represents the crossing event, not the static state.
    """
    name = "sma_crossover"

    def generate_signals(
        self,
        clean_points: List[CleanHistoricalPoint],
        params: Optional[Dict[str, Any]] = None,
        precision: int = 4
    ) -> Tuple[List[StrategySignalPoint], Dict[str, Any]]:
        params = params or {}
        short_period = self.parse_int_param(params.get("short_period", 20), "short_period", min_val=1)
        long_period = self.parse_int_param(params.get("long_period", 50), "long_period", min_val=2)

        if short_period >= long_period:
            raise InvalidStrategyParameterError(
                f"short_period ({short_period}) must be strictly less than long_period ({long_period})."
            )

        active_params = {
            "short_period": short_period,
            "long_period": long_period,
        }

        # Calculate causal SMAs using indicator service
        close_prices = [p.close for p in clean_points]
        short_smas = indicator_service.calculate_sma(close_prices, short_period, precision=precision)
        long_smas = indicator_service.calculate_sma(close_prices, long_period, precision=precision)

        signals: List[StrategySignalPoint] = []
        n = len(clean_points)

        for t in range(n):
            pt = clean_points[t]
            s_t = short_smas[t]
            l_t = long_smas[t]

            indicator_vals = {
                "short_sma": s_t,
                "long_sma": l_t,
            }

            # Insufficient observations for long SMA or initial observation
            if s_t is None or l_t is None or t == 0:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators=indicator_vals,
                    )
                )
                continue

            s_prev = short_smas[t - 1]
            l_prev = long_smas[t - 1]

            if s_prev is None or l_prev is None:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators=indicator_vals,
                    )
                )
                continue

            # Crossover detection
            if s_prev <= l_prev and s_t > l_t:
                action = "BUY"
            elif s_prev >= l_prev and s_t < l_t:
                action = "SELL"
            else:
                action = "HOLD"

            signals.append(
                StrategySignalPoint(
                    timestamp=pt.timestamp,
                    signal=action,
                    close=pt.close,
                    indicators=indicator_vals,
                )
            )

        return signals, active_params


class EMATrendStrategy(BaseStrategy):
    """
    2. EMA Trend Strategy:
    Generates signals based on close price position relative to an EMA:
    - BUY: close > EMA
    - SELL: close < EMA
    - HOLD: close == EMA (or warmup period)
    """
    name = "ema_trend"

    def generate_signals(
        self,
        clean_points: List[CleanHistoricalPoint],
        params: Optional[Dict[str, Any]] = None,
        precision: int = 4
    ) -> Tuple[List[StrategySignalPoint], Dict[str, Any]]:
        params = params or {}
        ema_period = self.parse_int_param(params.get("ema_period", 20), "ema_period", min_val=1)

        active_params = {
            "ema_period": ema_period,
        }

        close_prices = [p.close for p in clean_points]
        emas = indicator_service.calculate_ema(close_prices, ema_period, precision=precision)
        signals: List[StrategySignalPoint] = []
        n = len(clean_points)

        for t in range(n):
            pt = clean_points[t]
            ema_val = emas[t]

            indicator_vals = {
                "ema": ema_val,
            }

            if ema_val is None:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators=indicator_vals,
                    )
                )
                continue

            close = pt.close
            if close > ema_val:
                action = "BUY"
            elif close < ema_val:
                action = "SELL"
            else:
                action = "HOLD"

            signals.append(
                StrategySignalPoint(
                    timestamp=pt.timestamp,
                    signal=action,
                    close=pt.close,
                    indicators=indicator_vals,
                )
            )

        return signals, active_params


class MomentumStrategy(BaseStrategy):
    """
    3. Momentum Strategy:
    Measures percentage rate of change over a lookback window:
    momentum_t = (close_t / close_(t-lookback)) - 1
    - BUY: momentum > 0
    - SELL: momentum < 0
    - HOLD: momentum == 0 (or warmup period)
    """
    name = "momentum"

    def generate_signals(
        self,
        clean_points: List[CleanHistoricalPoint],
        params: Optional[Dict[str, Any]] = None,
        precision: int = 4
    ) -> Tuple[List[StrategySignalPoint], Dict[str, Any]]:
        params = params or {}
        lookback = self.parse_int_param(params.get("lookback", 10), "lookback", min_val=1)

        active_params = {
            "lookback": lookback,
        }

        signals: List[StrategySignalPoint] = []
        n = len(clean_points)

        for t in range(n):
            pt = clean_points[t]

            if t < lookback:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators={"momentum": None},
                    )
                )
                continue

            prev_close = clean_points[t - lookback].close
            if prev_close <= 0:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators={"momentum": None},
                    )
                )
                continue

            momentum_val = (pt.close / prev_close) - 1.0
            momentum_rounded = round(momentum_val, precision)

            if momentum_val > 0.0:
                action = "BUY"
            elif momentum_val < 0.0:
                action = "SELL"
            else:
                action = "HOLD"

            signals.append(
                StrategySignalPoint(
                    timestamp=pt.timestamp,
                    signal=action,
                    close=pt.close,
                    indicators={"momentum": momentum_rounded},
                )
            )

        return signals, active_params


class MeanReversionStrategy(BaseStrategy):
    """
    4. Mean Reversion Strategy:
    Computes rolling z-score of close price against its rolling mean & standard deviation:
    z_score = (close - rolling_mean) / rolling_sample_std
    - BUY: z_score <= -entry_threshold (oversold condition)
    - SELL: z_score >= entry_threshold (overbought condition)
    - HOLD: otherwise
    """
    name = "mean_reversion"

    def generate_signals(
        self,
        clean_points: List[CleanHistoricalPoint],
        params: Optional[Dict[str, Any]] = None,
        precision: int = 4
    ) -> Tuple[List[StrategySignalPoint], Dict[str, Any]]:
        params = params or {}
        lookback = self.parse_int_param(params.get("lookback", 20), "lookback", min_val=2)
        entry_threshold = self.parse_float_param(
            params.get("entry_threshold", 1.0),
            "entry_threshold",
            min_val=0.0,
            strictly_positive=True
        )

        active_params = {
            "lookback": lookback,
            "entry_threshold": entry_threshold,
        }

        signals: List[StrategySignalPoint] = []
        n = len(clean_points)

        for t in range(n):
            pt = clean_points[t]

            # Warmup: fewer than lookback observations available
            if t < lookback - 1:
                signals.append(
                    StrategySignalPoint(
                        timestamp=pt.timestamp,
                        signal="HOLD",
                        close=pt.close,
                        indicators={
                            "rolling_mean": None,
                            "rolling_std": None,
                            "z_score": None,
                        },
                    )
                )
                continue

            # Causal rolling slice: indices [t - lookback + 1 : t + 1]
            window_closes = [clean_points[i].close for i in range(t - lookback + 1, t + 1)]
            rolling_mean = sum(window_closes) / lookback

            # Sample variance with Bessel's correction (ddof=1)
            variance = sum((c - rolling_mean) ** 2 for c in window_closes) / (lookback - 1)
            rolling_std = math.sqrt(variance)

            # Zero standard deviation safeguard (flat price series)
            if rolling_std <= 1e-12:
                z_score = 0.0
                action = "HOLD"
            else:
                z_score = (pt.close - rolling_mean) / rolling_std
                if z_score <= -entry_threshold:
                    action = "BUY"
                elif z_score >= entry_threshold:
                    action = "SELL"
                else:
                    action = "HOLD"

            signals.append(
                StrategySignalPoint(
                    timestamp=pt.timestamp,
                    signal=action,
                    close=pt.close,
                    indicators={
                        "rolling_mean": round(rolling_mean, precision),
                        "rolling_std": round(rolling_std, precision),
                        "z_score": round(z_score, precision),
                    },
                )
            )

        return signals, active_params


class StrategyDispatcher:
    """
    Central dispatcher coordinating all quantitative trading strategies.
    Provides strategy lookup, input hygiene, signal generation, and Step 8 adapter.
    """

    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {
            "sma_crossover": SMACrossoverStrategy(),
            "ema_trend": EMATrendStrategy(),
            "momentum": MomentumStrategy(),
            "mean_reversion": MeanReversionStrategy(),
        }

    @property
    def supported_strategies(self) -> List[str]:
        return list(self._strategies.keys())

    def get_strategy(self, strategy_name: str) -> BaseStrategy:
        """Retrieves registered strategy instance or raises UnsupportedStrategyError (HTTP 400)."""
        if not strategy_name or not isinstance(strategy_name, str):
            raise UnsupportedStrategyError(str(strategy_name), self.supported_strategies)
        norm_name = strategy_name.strip().lower()
        if norm_name not in self._strategies:
            raise UnsupportedStrategyError(norm_name, self.supported_strategies)
        return self._strategies[norm_name]

    def validate_clean_points(self, clean_points: List[CleanHistoricalPoint]) -> None:
        """Ensures non-empty and chronologically ordered historical market dataset."""
        if not clean_points:
            raise InvalidStrategyParameterError("Historical market data is empty.")

        for i in range(1, len(clean_points)):
            if clean_points[i].timestamp < clean_points[i - 1].timestamp:
                raise InvalidStrategyParameterError(
                    f"Historical price data is out of order at index {i}: "
                    f"{clean_points[i].timestamp} < {clean_points[i - 1].timestamp}"
                )

    def generate_signals(
        self,
        strategy_name: str,
        clean_points: List[CleanHistoricalPoint],
        params: Optional[Dict[str, Any]] = None,
        precision: int = 4
    ) -> Tuple[List[StrategySignalPoint], Dict[str, Any]]:
        """
        Dispatches signal generation for the requested strategy with strict validation.
        """
        self.validate_clean_points(clean_points)
        strategy = self.get_strategy(strategy_name)
        return strategy.generate_signals(clean_points, params, precision=precision)

    def to_generic_signals(self, strategy_signals: List[StrategySignalPoint]) -> List[SignalPoint]:
        """Converts rich StrategySignalPoint list into generic Step 8 SignalPoint list."""
        return [
            SignalPoint(timestamp=s.timestamp, signal=s.signal)
            for s in strategy_signals
        ]


strategy_service = StrategyDispatcher()
SUPPORTED_STRATEGIES = ["sma_crossover", "ema_trend", "momentum", "mean_reversion"]
