class TransactionCostModel:
    def __init__(self, commission_bps: float = 5.0, slippage_pct: float = 0.001):
        self.commission_bps = commission_bps
        self.slippage_pct = slippage_pct

    def calculate_slippage(self, price: float, side: str) -> float:
        """
        side: 'BUY' or 'SELL'
        """
        slip = price * self.slippage_pct
        return price + slip if side.upper() == "BUY" else price - slip

    def calculate_commission(self, notional_value: float) -> float:
        return notional_value * (self.commission_bps / 10000.0)
