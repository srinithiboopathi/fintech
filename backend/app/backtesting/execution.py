"""
QuantLab - Trade Execution Module

Converts signal transitions into simulated order fills and tracks trade records.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Tuple
from app.backtesting.transaction_costs import TransactionCostModel


@dataclass
class Trade:
    """
    Detailed audit record of an executed trade order.
    """
    date: str
    action: str  # 'BUY' or 'SELL'
    price: float
    position: int
    quantity: float
    transaction_cost: float
    portfolio_value: float

    def to_dict(self) -> dict:
        return asdict(self)


class ExecutionHandler:
    """
    Executes trades when target position deviates from current holdings.

    Parameters
    ----------
    cost_model : TransactionCostModel
        Configured fee and slippage model.
    """

    def __init__(self, cost_model: TransactionCostModel):
        self.cost_model = cost_model

    def execute(
        self,
        date: str,
        current_position: int,
        target_position: int,
        current_quantity: float,
        current_cash: float,
        price: float,
        target_allocation: float
    ) -> Tuple[int, float, float, Optional[Trade]]:
        """
        Execute trade if position changes.

        Returns
        -------
        Tuple[new_position, new_quantity, new_cash, Trade or None]
        """
        if target_position == current_position:
            return current_position, current_quantity, current_cash, None

        if target_position == 1 and current_position == 0:
            # BUY: allocate cash up to available funds
            alloc_capital = min(current_cash, target_allocation)
            if alloc_capital <= 0 or price <= 0:
                return current_position, current_quantity, current_cash, None

            # Gross trade value + cost = alloc_capital
            trade_value = alloc_capital / (1.0 + self.cost_model.cost_pct)
            quantity = trade_value / price
            cost = self.cost_model.calculate_cost(trade_value)
            new_cash = current_cash - trade_value - cost
            portfolio_val = new_cash + quantity * price

            trade = Trade(
                date=str(date),
                action="BUY",
                price=float(price),
                position=1,
                quantity=float(quantity),
                transaction_cost=float(cost),
                portfolio_value=float(portfolio_val)
            )
            return 1, quantity, new_cash, trade

        elif target_position == 0 and current_position == 1:
            # SELL: liquidate all held units
            if current_quantity <= 0 or price <= 0:
                return 0, 0.0, current_cash, None

            gross_proceeds = current_quantity * price
            cost = self.cost_model.calculate_cost(gross_proceeds)
            new_cash = current_cash + gross_proceeds - cost
            portfolio_val = new_cash

            trade = Trade(
                date=str(date),
                action="SELL",
                price=float(price),
                position=0,
                quantity=float(current_quantity),
                transaction_cost=float(cost),
                portfolio_value=float(portfolio_val)
            )
            return 0, 0.0, new_cash, trade

        return current_position, current_quantity, current_cash, None
