"""
QuantLab - Exponential Moving Average (EMA) Trend Strategy

Generates long signals when the asset price closes above its EMA,
and rotates to cash when the price drops below or equals its EMA.
"""

import pandas as pd
from app.quant.indicators import calculate_ema
from app.strategies.base import BaseStrategy


class EMATrendStrategy(BaseStrategy):
    """
    Single EMA price-trend following strategy.

    Parameters
    ----------
    ema_window : int, default 20
        Span for the exponential moving average. Must be >= 1.
    price_col : str, default 'Close'
        Column name used for price data.
    """

    def __init__(self, ema_window: int = 20, price_col: str = "Close"):
        super().__init__(name=f"EMA_Trend_{ema_window}")
        if ema_window < 1:
            raise ValueError(f"ema_window must be >= 1, received: {ema_window}")

        self.ema_window = ema_window
        self.price_col = price_col

    def generate_raw_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate instantaneous signal at close of period t:
        1 if price > ema, else 0.
        """
        if df.empty or self.price_col not in df.columns or len(df) < self.ema_window:
            return pd.Series(0, index=df.index, dtype=int)

        prices = df[self.price_col]
        ema = calculate_ema(prices, span=self.ema_window)

        raw = (prices > ema).astype(int)
        raw = raw.where(~ema.isna(), 0).astype(int)
        return raw

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate execution-ready position signals strictly avoiding look-ahead bias.
        Signal from close of day t is executed on day t + 1 (shift=1).
        """
        raw = self.generate_raw_signals(df)
        if raw.empty:
            return raw

        position = raw.shift(1).fillna(0).astype(int)
        position.name = f"{self.name}_Position"
        return position
