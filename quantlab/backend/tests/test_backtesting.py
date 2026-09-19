import pytest
from app.backtesting.engine import BacktestEngine
from app.backtesting.position_sizing import PositionSizer
from app.backtesting.transaction_costs import TransactionCostModel
from app.strategies.sma_crossover import SMACrossoverStrategy

def generate_market_bars(n=120):
    bars = []
    base_price = 100.0
    for i in range(n):
        price = base_price + (i * 1.2)
        bars.append({
            "date": f"2023-01-{i+1:03d}",
            "symbol": "TEST_ASSET",
            "open": price - 0.5,
            "high": price + 1.0,
            "low": price - 1.0,
            "close": price,
            "adj_close": price,
            "volume": 1000000,
            "daily_return": 0.012
        })
    return bars

def test_position_sizing():
    qty_fixed = PositionSizer.calculate_position_size(
        portfolio_equity=100000.0,
        asset_price=50.0,
        sizing_method="fixed_amount",
        sizing_value=10000.0
    )
    assert qty_fixed == 200.0

    qty_pct = PositionSizer.calculate_position_size(
        portfolio_equity=100000.0,
        asset_price=50.0,
        sizing_method="percent_equity",
        sizing_value=0.50
    )
    assert qty_pct == 1000.0

def test_transaction_cost_model():
    # 100 shares @ $100 = $10,000 notional
    # 10 bps commission = $10
    # 0.1% slippage on entry = $100.10 executed price
    comm = TransactionCostModel.calculate_commission(100.0, 100.0, commission_bps=10.0)
    assert round(comm, 2) == 10.0

    slip_price_buy = TransactionCostModel.apply_slippage(100.0, "BUY", slippage_pct=0.001)
    slip_price_sell = TransactionCostModel.apply_slippage(100.0, "SELL", slippage_pct=0.001)
    assert slip_price_buy > 100.0
    assert slip_price_sell < 100.0

def test_backtest_execution_with_benchmark():
    bars = generate_market_bars(120)
    strat = SMACrossoverStrategy({"fast_period": 10, "slow_period": 30})
    
    engine = BacktestEngine(
        strategy=strat,
        bars=bars,
        initial_capital=100000.0,
        position_sizing="percent_equity",
        position_size_value=0.95,
        commission_bps=5.0,
        slippage_pct=0.0005
    )

    results = engine.run()
    assert "total_return_pct" in results
    assert "sharpe_ratio" in results
    assert "max_drawdown_pct" in results
    assert "equity_curve" in results
    assert "trades" in results
    assert "benchmark" in results

    # Benchmark fields
    bench = results["benchmark"]
    assert "final_equity" in bench
    assert "total_return_pct" in bench
    assert "cagr_pct" in bench
    assert "sharpe_ratio" in bench
    assert "max_drawdown_pct" in bench
    assert "alpha_excess_return_pct" in bench
    assert len(bench["equity_curve"]) == len(bars)

    assert len(results["equity_curve"]) == 120
    assert results["final_equity"] > 0.0
