from typing import Dict, Any
from app.backtesting.transaction_costs import TransactionCostModel

class ExecutionSimulator:
    def __init__(self, cost_model: TransactionCostModel):
        self.cost_model = cost_model

    def execute_market_order(self, symbol: str, raw_price: float, side: str, quantity: float) -> Dict[str, Any]:
        fill_price = self.cost_model.calculate_slippage(raw_price, side)
        notional = fill_price * quantity
        commission = self.cost_model.calculate_commission(notional)
        slippage_cost = abs(fill_price - raw_price) * quantity

        return {
            "symbol": symbol,
            "side": side.upper(),
            "raw_price": round(raw_price, 4),
            "fill_price": round(fill_price, 4),
            "quantity": quantity,
            "notional": round(notional, 2),
            "commission": round(commission, 2),
            "slippage_cost": round(slippage_cost, 2)
        }
