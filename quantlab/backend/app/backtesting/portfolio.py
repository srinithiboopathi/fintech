from typing import Dict, Any

class PortfolioTracker:
    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.position_qty = 0.0
        self.entry_price = 0.0
        self.entry_date = ""

    def total_equity(self, current_price: float) -> float:
        return self.cash + (self.position_qty * current_price)

    def is_invested(self) -> bool:
        return self.position_qty > 0.00001

    def enter_long(self, date: str, fill_price: float, quantity: float, commission: float):
        total_cost = (fill_price * quantity) + commission
        self.cash -= total_cost
        self.position_qty = quantity
        self.entry_price = fill_price
        self.entry_date = date

    def exit_long(self, date: str, fill_price: float, commission: float) -> Dict[str, Any]:
        gross_proceeds = fill_price * self.position_qty
        net_proceeds = gross_proceeds - commission
        self.cash += net_proceeds

        cost_basis = self.entry_price * self.position_qty
        pnl_usd = net_proceeds - cost_basis
        pnl_pct = (fill_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0.0

        trade_info = {
            "entry_date": self.entry_date,
            "entry_price": round(self.entry_price, 4),
            "exit_date": date,
            "exit_price": round(fill_price, 4),
            "quantity": self.position_qty,
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct * 100.0, 2),
            "commission": round(commission, 2)
        }

        self.position_qty = 0.0
        self.entry_price = 0.0
        self.entry_date = ""

        return trade_info
