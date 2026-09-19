"""
QuantLab - Simple Moving Average (SMA) Crossover Strategy

Generates long signals when the fast SMA exceeds the slow SMA,
and rotates to cash when the fast SMA crosses below or equals the slow SMA.
"""

import pandas as pd
from app.quant.indicators import calculate_sma
from app.strategies.base import BaseStrategy


class SMACrossoverStrategy(BaseStrategy):
    """
    Dual moving average trend-following strategy.

    Parameters
    ----------
    fast_window : int, default 20
        Number of periods for the fast SMA.
    slow_window : int, default 50
        Number of periods for the slow SMA. Must be > fast_window.
    price_col : str, default 'Close'
        Column name used for price data.
    """

    def __init__(self, fast_window: int = 20, slow_window: int = 50, price_col: str = "Close"):
        super().__init__(name=f"SMA_Crossover_{fast_window}_{slow_window}")
        if fast_window < 1:
            raise ValueError(f"fast_window must be >= 1, received: {fast_window}")
        if slow_window <= fast_window:
            raise ValueError(
                f"slow_window ({slow_window}) must be strictly greater than fast_window ({fast_window})"
            )

        self.fast_window = fast_window
        self.slow_window = slow_window
        self.price_col = price_col

    def generate_raw_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate instantaneous signal at close of period t:
        1 if fast_sma > slow_sma, else 0.
        """
        if df.empty or self.price_col not in df.columns or len(df) < self.slow_window:
            return pd.Series(0, index=df.index, dtype=int)

        prices = df[self.price_col]
        fast_sma = calculate_sma(prices, window=self.fast_window)
        slow_sma = calculate_sma(prices, window=self.slow_window)

        # 1 when fast SMA > slow SMA, 0 otherwise
        raw = (fast_sma > slow_sma).astype(int)
        # Ensure initial uncalculated periods (where slow SMA is NaN) are 0
        raw = raw.where(~slow_sma.isna(), 0).astype(int)
        return raw

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate execution-ready position signals strictly avoiding look-ahead bias.
        Signal from close of day t is executed on day t + 1 (shift=1).
        """
        raw = self.generate_raw_signals(df)
        if raw.empty:
            return raw

        # Shift by 1 period so today's position is dictated strictly by yesterday's data
        position = raw.shift(1).fillna(0).astype(int)
        position.name = f"{self.name}_Position"
        return position
