"""
backend/tests/test_backtesting.py

Comprehensive Test Suite for Step 8: Strategy-Agnostic Backtesting Engine.
Tests initial capital, BUY/SELL/HOLD execution, position & cash accounting,
transaction costs, position sizing, risk metrics integration, benchmark comparison,
next-observation causal execution, strict look-ahead protection, validation, and API routes.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CleanHistoricalPoint,
    SignalPoint,
    BacktestRequest,
    BacktestResponse,
)
from app.services.backtesting import (
    BacktestingEngine,
    backtesting_service,
)
from app.utils.exceptions import InvalidBacktestParameterError

client = TestClient(app)


# ==============================================================================
# Deterministic Test Fixtures
# ==============================================================================
def create_deterministic_prices(
    prices: list[float],
    start_date: str = "2026-01-01"
) -> list[CleanHistoricalPoint]:
    """Generates a list of CleanHistoricalPoint objects from a price list."""
    base_dt = datetime.strptime(start_date, "%Y-%m-%d")
    points = []
    for i, p in enumerate(prices):
        dt_str = (base_dt + timedelta(days=i)).strftime("%Y-%m-%dT00:00:00Z")
        points.append(
            CleanHistoricalPoint(
                timestamp=dt_str,
                open=p,
                high=p * 1.02,
                low=p * 0.98,
                close=p,
                volume=5000.0,
                asset="TestAsset",
                symbol="TEST",
                source="Twelve Data",
            )
        )
    return points


def create_signals(
    signal_pairs: list[tuple[str, str]]
) -> list[SignalPoint]:
    """Generates a list of SignalPoint objects from (timestamp, signal_type) tuples."""
    return [SignalPoint(timestamp=ts, signal=sig) for ts, sig in signal_pairs]


# ==============================================================================
# 1. Initial Capital Test
# ==============================================================================
def test_initial_capital():
    """Verifies that configurable initial capital is respected and initializes portfolio equity."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0, 110.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=250000.0,
        transaction_cost_rate=0.001,
        allocation_fraction=1.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    assert result.performance.initial_capital == 250000.0
    assert result.performance.final_portfolio_value == 250000.0
    assert result.equity_curve[0].cash == 250000.0
    assert result.equity_curve[0].portfolio_value == 250000.0


# ==============================================================================
# 2. BUY Execution Test
# ==============================================================================
def test_buy_execution():
    """Verifies BUY signal at t executes at next observation t+1 and allocates position."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0, 110.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=100000.0,
        transaction_cost_rate=0.001,
        allocation_fraction=1.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    # Observation 0: No trade executed yet (action NONE)
    assert result.equity_curve[0].executed_action == "NONE"
    assert result.equity_curve[0].position_quantity == 0.0

    # Observation 1: BUY executed at prices[1].close (105.0)
    assert result.equity_curve[1].executed_action == "BUY"
    assert result.equity_curve[1].position_quantity > 0.0
    assert len(result.trade_history) == 1
    trade = result.trade_history[0]
    assert trade.side == "BUY"
    assert trade.price == 105.0
    assert trade.timestamp == prices[1].timestamp


# ==============================================================================
# 3. SELL Execution Test
# ==============================================================================
def test_sell_execution():
    """Verifies SELL signal at t executes at t+1, liquidates position, and calculates PnL."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 120.0, 125.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),   # executes at t=1 (100.0)
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="SELL"),  # executes at t=3 (125.0)
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=10000.0,
        transaction_cost_rate=0.0,
        allocation_fraction=1.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    assert len(result.trade_history) == 2
    buy_trade, sell_trade = result.trade_history

    assert buy_trade.side == "BUY"
    assert buy_trade.price == 100.0
    assert sell_trade.side == "SELL"
    assert sell_trade.price == 125.0
    assert sell_trade.resulting_position == 0.0
    assert sell_trade.pnl is not None
    assert sell_trade.pnl > 0.0  # Profitable trade
    assert result.performance.winning_trades == 1
    assert result.performance.losing_trades == 0


# ==============================================================================
# 4. HOLD Behavior Test
# ==============================================================================
def test_hold_behavior():
    """Verifies HOLD signal never generates trades or alters existing positions."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 102.0, 105.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(signals=signals)
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    assert len(result.trade_history) == 0
    for obs in result.equity_curve:
        assert obs.position_quantity == 0.0
        assert obs.executed_action in ("NONE", "HOLD")
        assert obs.cash == 100000.0


# ==============================================================================
# 5. Position Accounting Test
# ==============================================================================
def test_position_accounting():
    """Verifies position_market_value == position_quantity * close_price at each step."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 110.0, 115.0, 108.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(signals=signals)
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    for obs in result.equity_curve:
        expected_market_val = round(obs.position_quantity * obs.close_price, 2)
        assert round(obs.position_market_value, 2) == expected_market_val


# ==============================================================================
# 6. Cash Accounting Test
# ==============================================================================
def test_cash_accounting():
    """Verifies cash is strictly non-negative and correctly deducted/credited."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 100.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=50000.0,
        allocation_fraction=1.0,
        transaction_cost_rate=0.001,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    for obs in result.equity_curve:
        assert obs.cash >= 0.0


# ==============================================================================
# 7. Portfolio Value Calculation Test
# ==============================================================================
def test_portfolio_value_calculation():
    """Verifies portfolio_value == cash + position_market_value at all times."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([50.0, 55.0, 60.0, 58.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="SELL"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(signals=signals)
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    for obs in result.equity_curve:
        expected_pv = round(obs.cash + obs.position_market_value, 2)
        assert round(obs.portfolio_value, 2) == expected_pv


# ==============================================================================
# 8. Transaction Cost Calculation Test
# ==============================================================================
def test_transaction_cost_calculation():
    """Verifies fee is accurately computed as trade_value * transaction_cost_rate."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 200.0, 250.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="SELL"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    fee_rate = 0.005  # 0.5%
    request = BacktestRequest(
        initial_capital=10000.0,
        transaction_cost_rate=fee_rate,
        allocation_fraction=1.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    assert len(result.trade_history) == 2
    for trade in result.trade_history:
        expected_fee = round(trade.trade_value * fee_rate, 4)
        assert round(trade.transaction_cost, 4) == expected_fee


# ==============================================================================
# 9. Position Sizing Test
# ==============================================================================
def test_position_sizing():
    """Verifies partial allocation fraction (e.g. 0.5) utilizes half of available cash."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 100.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=100000.0,
        allocation_fraction=0.5,
        transaction_cost_rate=0.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    # With 0 fee and 0.5 allocation, 50,000 should be committed
    trade = result.trade_history[0]
    assert round(trade.trade_value, 2) == 50000.0
    assert round(trade.resulting_cash, 2) == 50000.0


# ==============================================================================
# 10. Insufficient Cash Protection Test
# ==============================================================================
def test_insufficient_cash_protection():
    """Verifies engine rejects spending more cash than available on subsequent BUY."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 100.0, 100.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),   # Uses 100% of cash
        SignalPoint(timestamp=prices[1].timestamp, signal="BUY"),   # Cash is 0; should not overspend
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=10000.0,
        allocation_fraction=1.0,
        transaction_cost_rate=0.001,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    # Only 1 trade should have executed
    assert len(result.trade_history) == 1
    for obs in result.equity_curve:
        assert obs.cash >= 0.0


# ==============================================================================
# 11. Negative Capital Rejection Test
# ==============================================================================
def test_negative_capital_rejection():
    """Verifies that initial_capital <= 0 is rejected with HTTP 400 error."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])
    signals = [SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"), SignalPoint(timestamp=prices[1].timestamp, signal="HOLD")]

    with pytest.raises(InvalidBacktestParameterError) as exc:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(initial_capital=-1000.0, signals=signals))
    assert exc.value.status_code == 400

    with pytest.raises(InvalidBacktestParameterError) as exc_zero:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(initial_capital=0.0, signals=signals))
    assert exc_zero.value.status_code == 400


# ==============================================================================
# 12. Negative Transaction Cost Rejection Test
# ==============================================================================
def test_negative_transaction_cost_rejection():
    """Verifies transaction_cost_rate < 0 is rejected with HTTP 400 error."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])
    signals = [SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"), SignalPoint(timestamp=prices[1].timestamp, signal="HOLD")]

    with pytest.raises(InvalidBacktestParameterError) as exc:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(transaction_cost_rate=-0.01, signals=signals))
    assert exc.value.status_code == 400


# ==============================================================================
# 13. Invalid Allocation Rejection Test
# ==============================================================================
def test_invalid_allocation_rejection():
    """Verifies allocation_fraction <= 0 or > 1.0 is rejected with HTTP 400 error."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])
    signals = [SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"), SignalPoint(timestamp=prices[1].timestamp, signal="HOLD")]

    with pytest.raises(InvalidBacktestParameterError):
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(allocation_fraction=0.0, signals=signals))

    with pytest.raises(InvalidBacktestParameterError):
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(allocation_fraction=1.5, signals=signals))


# ==============================================================================
# 14. Trade History Completeness Test
# ==============================================================================
def test_trade_history_fields():
    """Verifies all required trade audit trail attributes are accurately populated."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 110.0, 120.0, 130.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="SELL"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(signals=signals)
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    assert len(result.trade_history) == 2
    sell = result.trade_history[1]
    assert sell.trade_id == 2
    assert sell.timestamp == prices[3].timestamp
    assert sell.side == "SELL"
    assert sell.price == 130.0
    assert sell.quantity > 0
    assert sell.trade_value > 0
    assert sell.transaction_cost >= 0
    assert sell.resulting_cash > 0
    assert sell.resulting_position == 0.0
    assert sell.pnl is not None
    assert sell.pnl_percent is not None


# ==============================================================================
# 15. Total Return Test
# ==============================================================================
def test_total_return():
    """Verifies total return formula: (final_value - initial_capital) / initial_capital * 100."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 120.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=100000.0,
        transaction_cost_rate=0.0,
        allocation_fraction=1.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    expected_return = (result.performance.final_portfolio_value - 100000.0) / 100000.0 * 100.0
    assert round(result.performance.total_return_pct, 4) == round(expected_return, 4)


# ==============================================================================
# 16. Maximum Drawdown Integration Test
# ==============================================================================
def test_maximum_drawdown_integration():
    """Verifies peak-to-trough maximum drawdown is correctly integrated from portfolio values."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 100.0, 150.0, 75.0, 120.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[4].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=100000.0,
        transaction_cost_rate=0.0,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    # From 150 to 75 represents a 50% drop
    assert result.performance.maximum_drawdown_pct is not None
    assert round(result.performance.maximum_drawdown_pct, 1) == -50.0
    assert result.performance.maximum_drawdown_timestamp == prices[3].timestamp


# ==============================================================================
# 17. Buy-and-Hold Benchmark Test
# ==============================================================================
def test_buy_and_hold_benchmark():
    """Verifies Buy-and-Hold benchmark accurately purchases at first execution price and holds."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 110.0, 120.0, 130.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[3].timestamp, signal="HOLD"),
    ]
    request = BacktestRequest(
        initial_capital=100000.0,
        transaction_cost_rate=0.001,
        signals=signals,
    )
    result = engine.run_simulation("TestAsset", "TEST", prices, request)

    bm = result.benchmark
    assert bm.benchmark_name == "Buy & Hold"
    assert bm.initial_value == 100000.0
    assert len(bm.equity_curve) == len(prices)
    # Benchmark buys at prices[1] (110.0) and finishes at prices[3] (130.0)
    assert bm.final_value > bm.initial_value
    assert bm.total_return_pct > 0


# ==============================================================================
# 18. Chronological Ordering Test
# ==============================================================================
def test_chronological_ordering():
    """Verifies non-chronological signals are rejected with HTTP 400."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])
    out_of_order_signals = [
        SignalPoint(timestamp="2026-01-02T00:00:00Z", signal="BUY"),
        SignalPoint(timestamp="2026-01-01T00:00:00Z", signal="SELL"),
    ]
    with pytest.raises(InvalidBacktestParameterError) as exc:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(signals=out_of_order_signals))
    assert exc.value.status_code == 400


# ==============================================================================
# 19. Next-Observation Execution Test
# ==============================================================================
def test_next_observation_execution():
    """Verifies that a signal at observation i executes strictly at observation i+1."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 120.0, 130.0])
    signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=prices[2].timestamp, signal="HOLD"),
    ]
    result = engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(signals=signals))

    # At observation 0 (prices[0] = 100.0), action is NONE, trade count is 0
    assert result.equity_curve[0].executed_action == "NONE"
    assert len(result.trade_history) == 1
    # Trade execution price MUST be prices[1] (120.0), NOT prices[0] (100.0)
    assert result.trade_history[0].price == 120.0
    assert result.trade_history[0].timestamp == prices[1].timestamp


# ==============================================================================
# 20. Look-Ahead Bias Prevention Test
# ==============================================================================
def test_look_ahead_bias_prevention():
    """Modifying future prices MUST NOT alter earlier trade executions or portfolio values."""
    engine = BacktestingEngine()
    base_prices = create_deterministic_prices([100.0, 105.0, 110.0, 115.0, 120.0])
    signals = [
        SignalPoint(timestamp=base_prices[0].timestamp, signal="BUY"),
        SignalPoint(timestamp=base_prices[1].timestamp, signal="HOLD"),
        SignalPoint(timestamp=base_prices[2].timestamp, signal="SELL"),
        SignalPoint(timestamp=base_prices[3].timestamp, signal="HOLD"),
        SignalPoint(timestamp=base_prices[4].timestamp, signal="HOLD"),
    ]

    base_result = engine.run_simulation("TestAsset", "TEST", base_prices, BacktestRequest(signals=signals))

    # Create mutated prices with extreme future changes at indices 3 and 4
    mutated_prices = [
        CleanHistoricalPoint(
            timestamp=p.timestamp,
            open=p.open,
            high=p.high,
            low=p.low,
            close=p.close if i < 3 else p.close * 10.0,  # 10x price shock in future
            volume=p.volume,
            asset="TestAsset",
            symbol="TEST",
            source="Twelve Data",
        )
        for i, p in enumerate(base_prices)
    ]

    mutated_result = engine.run_simulation("TestAsset", "TEST", mutated_prices, BacktestRequest(signals=signals))

    # Earlier observations (indices 0, 1, 2) MUST be completely identical
    for i in range(3):
        base_obs = base_result.equity_curve[i]
        mutated_obs = mutated_result.equity_curve[i]
        assert base_obs.portfolio_value == mutated_obs.portfolio_value, (
            f"Look-ahead violation at index {i}: base={base_obs.portfolio_value}, mutated={mutated_obs.portfolio_value}"
        )
        assert base_obs.cash == mutated_obs.cash
        assert base_obs.position_quantity == mutated_obs.position_quantity

    # Trade 1 (executed at index 1) MUST be completely identical
    assert base_result.trade_history[0] == mutated_result.trade_history[0]


# ==============================================================================
# 21. Empty Data Handling Test
# ==============================================================================
def test_empty_data_handling():
    """Verifies that empty signals or empty price datasets raise HTTP 400 error."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])

    with pytest.raises(InvalidBacktestParameterError) as exc_signals:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(signals=[]))
    assert exc_signals.value.status_code == 400

    signals = [SignalPoint(timestamp=prices[0].timestamp, signal="BUY")]
    with pytest.raises(InvalidBacktestParameterError) as exc_prices:
        engine.run_simulation("TestAsset", "TEST", [], BacktestRequest(signals=signals))
    assert exc_prices.value.status_code == 400


# ==============================================================================
# 22. Invalid Signals Rejection Test
# ==============================================================================
def test_invalid_signals():
    """Verifies that invalid signal strings (e.g. 'SHORT', 'PANIC') raise HTTP 400."""
    engine = BacktestingEngine()
    prices = create_deterministic_prices([100.0, 105.0])
    invalid_signals = [
        SignalPoint(timestamp=prices[0].timestamp, signal="SHORT"),
        SignalPoint(timestamp=prices[1].timestamp, signal="HOLD"),
    ]
    with pytest.raises(InvalidBacktestParameterError) as exc:
        engine.run_simulation("TestAsset", "TEST", prices, BacktestRequest(signals=invalid_signals))
    assert exc.value.status_code == 400


# ==============================================================================
# 23. API Endpoint Test
# ==============================================================================
def test_api_endpoint_post_backtest():
    """Verifies POST /market/{asset}/backtest returns HTTP 200 and schema."""
    # First fetch clean market data to know valid timestamps
    resp = client.get("/market/nvidia/data")
    assert resp.status_code == 200
    clean_data = resp.json()["data"]
    assert len(clean_data) >= 5

    # Craft 5 chronological signals
    signals = [
        {"timestamp": clean_data[0]["timestamp"], "signal": "BUY"},
        {"timestamp": clean_data[1]["timestamp"], "signal": "HOLD"},
        {"timestamp": clean_data[2]["timestamp"], "signal": "SELL"},
        {"timestamp": clean_data[3]["timestamp"], "signal": "HOLD"},
        {"timestamp": clean_data[4]["timestamp"], "signal": "HOLD"},
    ]

    payload = {
        "initial_capital": 50000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0,
        "signals": signals,
    }

    post_resp = client.post("/market/nvidia/backtest", json=payload)
    assert post_resp.status_code == 200
    data = post_resp.json()

    assert data["asset"] == "NVIDIA"
    assert data["symbol"] == "NVDA"
    assert data["source"] == "Twelve Data"
    assert data["data_status"] == "calculated"
    assert data["performance"]["initial_capital"] == 50000.0
    assert data["performance"]["total_trades"] == 2
    assert "benchmark" in data
    assert len(data["equity_curve"]) == len(clean_data)


# ==============================================================================
# 24. NVIDIA Live/Cached Backtest
# ==============================================================================
def test_nvda_backtest():
    """Verifies backtesting on NVIDIA clean market data."""
    resp = client.get("/market/nvidia/data")
    assert resp.status_code == 200
    pts = resp.json()["data"]

    signals = [
        {"timestamp": pts[0]["timestamp"], "signal": "BUY"},
        {"timestamp": pts[len(pts)//2]["timestamp"], "signal": "SELL"},
    ]
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0,
        "signals": signals,
    }
    r = client.post("/market/nvidia/backtest", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["symbol"] == "NVDA"
    assert res["performance"]["total_trades"] == 2
    assert res["performance"]["total_fees_paid"] > 0


# ==============================================================================
# 25. Bitcoin (BTC/USD) Live/Cached Backtest
# ==============================================================================
def test_btc_backtest():
    """Verifies backtesting on Bitcoin clean market data."""
    resp = client.get("/market/bitcoin/data")
    assert resp.status_code == 200
    pts = resp.json()["data"]

    signals = [
        {"timestamp": pts[0]["timestamp"], "signal": "BUY"},
        {"timestamp": pts[min(5, len(pts)-1)]["timestamp"], "signal": "SELL"},
    ]
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 0.5,
        "signals": signals,
    }
    r = client.post("/market/bitcoin/backtest", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["symbol"] == "BTC/USD"
    assert res["performance"]["final_portfolio_value"] > 0
    assert len(res["benchmark"]["equity_curve"]) > 0


# ==============================================================================
# 26. Gold (XAU/USD) Live/Cached Backtest
# ==============================================================================
def test_gold_backtest():
    """Verifies backtesting on Gold bullion clean market data."""
    resp = client.get("/market/gold/data")
    assert resp.status_code == 200
    pts = resp.json()["data"]

    signals = [
        {"timestamp": pts[0]["timestamp"], "signal": "BUY"},
        {"timestamp": pts[min(10, len(pts)-1)]["timestamp"], "signal": "HOLD"},
    ]
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0,
        "signals": signals,
    }
    r = client.post("/market/gold/backtest", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert res["symbol"] == "XAU/USD"
    assert res["performance"]["total_trades"] == 1
    assert res["performance"]["final_portfolio_value"] > 0
