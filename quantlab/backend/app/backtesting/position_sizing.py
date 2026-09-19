class PositionSizer:
    @staticmethod
    def calculate_units(
        method: str,
        value: float,
        portfolio_equity: float,
        price: float,
        asset_volatility: float = 0.20
    ) -> float:
        if price <= 0 or portfolio_equity <= 0:
            return 0.0

        if method == "fixed_amount":
            target_dollars = min(value, portfolio_equity)
            return target_dollars / price

        elif method == "volatility_parity":
            # Target 15% portfolio annualized volatility
            target_vol = 0.15
            vol = max(asset_volatility, 0.05)
            weight = min(1.0, target_vol / vol)
            target_dollars = portfolio_equity * weight
            return target_dollars / price

        else: # "percent_equity"
            pct = min(max(value, 0.01), 1.0)
            target_dollars = portfolio_equity * pct
            return target_dollars / price
