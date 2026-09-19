"""
QuantLab - Portfolio State Tracking Module

Maintains live mark-to-market valuations, cumulative return series,
and peak-to-trough drawdowns throughout backtest simulation.
"""

from typing import List, Dict, Any
import pandas as pd


class PortfolioTracker:
    """
    Tracks portfolio equity and risk metrics across trading days.

    Parameters
    ----------
    initial_capital : float, default 100000.0
        Starting cash balance.
    """

    def __init__(self, initial_capital: float = 100000.0):
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, received: {initial_capital}")

        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.position = 0
        self.quantity = 0.0
        self.peak_value = float(initial_capital)
        self.history: List[Dict[str, Any]] = []

    def update(self, date: str, price: float) -> Dict[str, Any]:
        """
        Mark portfolio to market at current price and record daily snapshot.

        Parameters
        ----------
        date : str
            Current trading date.
        price : float
            Asset market closing price.

        Returns
        -------
        Dict[str, Any]
            Current portfolio state snapshot.
        """
        equity = self.cash + (self.quantity * price)
        if equity > self.peak_value:
            self.peak_value = equity

        drawdown = (equity - self.peak_value) / self.peak_value if self.peak_value > 0 else 0.0
        cumulative_return = (equity - self.initial_capital) / self.initial_capital

        snapshot = {
            "date": str(date),
            "cash": float(self.cash),
            "position": int(self.position),
            "quantity": float(self.quantity),
            "price": float(price),
            "equity": float(equity),
            "peak": float(self.peak_value),
            "drawdown": float(drawdown),
            "cumulative_return": float(cumulative_return)
        }
        self.history.append(snapshot)
        return snapshot

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert portfolio history log to a structured DataFrame.
        """
        if not self.history:
            return pd.DataFrame()
        df = pd.DataFrame(self.history)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df
