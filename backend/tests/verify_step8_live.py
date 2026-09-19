"""
backend/tests/verify_step8_live.py

Live Verification Script for Step 8 Strategy-Agnostic Backtesting Engine:
- POST /market/nvidia/backtest
- POST /market/bitcoin/backtest
- POST /market/gold/backtest

Verifies:
1. HTTP 200 responses across all three assets.
2. Next-observation causal execution (Signal at t executes at t+1 at P_{t+1}).
3. Valid portfolio value, equity curve, trade history, fees paid, and metrics.
4. Correct Buy-and-Hold benchmark computation and equity curve.
5. Strict look-ahead bias prevention.
6. Parameter rejection: negative capital, negative fees, out-of-bounds allocation, invalid signals (HTTP 400).
7. Zero fake market data: operations derived from verified cleaned datasets.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def run_live_verification():
    print("=" * 75)
    print("STEP 8 — STRATEGY-AGNOSTIC BACKTESTING ENGINE LIVE VERIFICATION")
    print("=" * 75)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Health check
    try:
        health_resp = client.get("/health")
        if health_resp.status_code != 200:
            print(f"[FAIL] Health check returned status {health_resp.status_code}")
            sys.exit(1)
        health_data = health_resp.json()
        print(f"[OK] Backend Online: Primary={health_data.get('primary_provider')}, Fallback={health_data.get('fallback_provider')}")
    except Exception as e:
        print(f"[FAIL] Failed to reach backend server at {BASE_URL}: {e}")
        sys.exit(1)

    assets_to_test = [
        ("nvidia", "NVDA", "NVIDIA"),
        ("bitcoin", "BTC/USD", "Bitcoin"),
        ("gold", "XAU/USD", "Gold"),
    ]

    for asset_id, symbol, asset_name in assets_to_test:
        print("\n" + "-" * 75)
        print(f"VERIFYING BACKTEST FOR {asset_name} ({symbol})")
        print("-" * 75)

        # 1. Fetch clean data to construct deterministic signals
        data_resp = client.get(f"/market/{asset_id}/data")
        if data_resp.status_code != 200:
            print(f"[FAIL] Failed to fetch clean data for {asset_id}: {data_resp.text}")
            sys.exit(1)

        clean_points = data_resp.json()["data"]
        n_points = len(clean_points)
        print(f"[OK] Fetched {n_points} clean points for {symbol}. Date range: {clean_points[0]['timestamp']} to {clean_points[-1]['timestamp']}")

        # 2. Build deterministic signals:
        # BUY at observation 0 -> executes at observation 1
        # HOLD during middle
        # SELL at middle observation -> executes at middle + 1
        # HOLD till end
        mid_idx = n_points // 2
        signals = [
            {"timestamp": clean_points[0]["timestamp"], "signal": "BUY"},
            {"timestamp": clean_points[mid_idx]["timestamp"], "signal": "SELL"},
        ]

        payload = {
            "initial_capital": 100000.0,
            "transaction_cost_rate": 0.001,
            "allocation_fraction": 1.0,
            "signals": signals,
        }

        bt_resp = client.post(f"/market/{asset_id}/backtest", json=payload)
        if bt_resp.status_code != 200:
            print(f"[FAIL] /market/{asset_id}/backtest returned {bt_resp.status_code}: {bt_resp.text}")
            sys.exit(1)

        bt_data = bt_resp.json()

        # Validations
        assert bt_data["symbol"] == symbol, f"Symbol mismatch: expected {symbol}, got {bt_data['symbol']}"
        assert bt_data["asset"] == asset_name, f"Asset mismatch: expected {asset_name}, got {bt_data['asset']}"
        assert bt_data["source"] in ("Twelve Data", "Alpha Vantage"), f"Unexpected source: {bt_data['source']}"
        assert bt_data["data_status"] == "calculated"
        assert "Next-Observation" in bt_data["execution_model"]

        perf = bt_data["performance"]
        assert perf["initial_capital"] == 100000.0
        assert perf["final_portfolio_value"] > 0
        assert perf["total_trades"] == 2
        assert perf["total_fees_paid"] > 0
        assert perf["maximum_drawdown_pct"] is not None

        # Check trades
        trades = bt_data["trade_history"]
        assert len(trades) == 2
        buy_trade = trades[0]
        sell_trade = trades[1]

        assert buy_trade["side"] == "BUY"
        assert buy_trade["timestamp"] == clean_points[1]["timestamp"], "BUY must execute at observation 1 (next observation)"
        assert buy_trade["price"] == clean_points[1]["close"]
        assert buy_trade["transaction_cost"] > 0

        assert sell_trade["side"] == "SELL"
        assert sell_trade["timestamp"] == clean_points[mid_idx + 1]["timestamp"], "SELL must execute at mid_idx + 1"
        assert sell_trade["resulting_position"] == 0.0
        assert sell_trade["pnl"] is not None

        # Check equity curve
        curve = bt_data["equity_curve"]
        assert len(curve) == n_points
        assert curve[0]["portfolio_value"] == 100000.0
        assert curve[0]["executed_action"] == "NONE"
        assert curve[1]["executed_action"] == "BUY"
        assert curve[mid_idx + 1]["executed_action"] == "SELL"

        # Check benchmark
        bm = bt_data["benchmark"]
        assert bm["benchmark_name"] == "Buy & Hold"
        assert bm["initial_value"] == 100000.0
        assert bm["final_value"] > 0
        assert len(bm["equity_curve"]) == n_points

        print(f"[OK] Backtest successful for {symbol}:")
        print(f"     Initial Capital:       ${perf['initial_capital']:,.2f}")
        print(f"     Final Portfolio Value: ${perf['final_portfolio_value']:,.2f}")
        print(f"     Total Strategy Return: {perf['total_return_pct']:+.2f}%")
        print(f"     Total Trades:          {perf['total_trades']} (Win Rate: {perf['win_rate_pct']}%)")
        print(f"     Total Fees Paid:       ${perf['total_fees_paid']:,.2f}")
        print(f"     Max Drawdown:          {perf['maximum_drawdown_pct']:.2f}% (at {perf['maximum_drawdown_timestamp']})")
        print(f"     Sharpe Ratio:          {perf['sharpe_ratio']}")
        print(f"     Benchmark Return:      {bm['total_return_pct']:+.2f}%")

    # 3. Parameter Validation Checks (HTTP 400 rejection)
    print("\n" + "-" * 75)
    print("VERIFYING PARAMETER VALIDATION & ERROR REJECTION (HTTP 400)")
    print("-" * 75)

    valid_signals = [{"timestamp": clean_points[0]["timestamp"], "signal": "BUY"}]

    invalid_test_cases = [
        ("Negative initial capital", {"initial_capital": -1000.0, "signals": valid_signals}),
        ("Zero initial capital", {"initial_capital": 0.0, "signals": valid_signals}),
        ("Non-numeric initial capital", {"initial_capital": "invalid_abc", "signals": valid_signals}),
        ("Negative transaction cost", {"transaction_cost_rate": -0.01, "signals": valid_signals}),
        ("Zero allocation fraction", {"allocation_fraction": 0.0, "signals": valid_signals}),
        ("Excess allocation fraction (> 1.0)", {"allocation_fraction": 1.5, "signals": valid_signals}),
        ("Empty signals sequence", {"signals": []}),
        ("Invalid signal type ('SHORT')", {"signals": [{"timestamp": clean_points[0]["timestamp"], "signal": "SHORT"}]}),
        ("Unsorted timestamps", {"signals": [
            {"timestamp": clean_points[1]["timestamp"], "signal": "BUY"},
            {"timestamp": clean_points[0]["timestamp"], "signal": "SELL"},
        ]}),
    ]

    for label, bad_payload in invalid_test_cases:
        r = client.post("/market/nvidia/backtest", json=bad_payload)
        if r.status_code == 400:
            print(f"[OK] Successfully rejected with HTTP 400: {label}")
        else:
            print(f"[FAIL] Expected HTTP 400 for '{label}', got {r.status_code}: {r.text}")
            sys.exit(1)

    print("\n" + "=" * 75)
    print("ALL STEP 8 LIVE VERIFICATIONS PASSED SUCCESSFULLY (3/3 ASSETS + VALIDATION)")
    print("=" * 75)


if __name__ == "__main__":
    run_live_verification()
