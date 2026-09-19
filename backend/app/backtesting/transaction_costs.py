"""
QuantLab - Transaction Cost Module

Models proportional commission and slippage transaction costs.
Costs are incurred strictly when portfolio positions are initiated or liquidated.
"""

class TransactionCostModel:
    """
    Proportional fee model for trade executions.

    Parameters
    ----------
    cost_pct : float, default 0.001
        Percentage cost applied to total gross trade notional (e.g. 0.001 = 10 bps = 0.1%).
    """

    def __init__(self, cost_pct: float = 0.001):
        if cost_pct < 0.0:
            raise ValueError(f"cost_pct must be non-negative (>= 0.0), received: {cost_pct}")
        self.cost_pct = float(cost_pct)

    def calculate_cost(self, trade_notional: float) -> float:
        """
        Calculate total transaction cost for a given trade size.

        Parameters
        ----------
        trade_notional : float
            Gross monetary value of the trade (shares * price).

        Returns
        -------
        float
            Transaction cost in monetary units.
        """
        return abs(trade_notional) * self.cost_pct
