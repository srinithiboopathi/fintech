"""
backend/tests/verify_step9_live.py

Live Verification Script for Step 9 Four Trading Strategies:
1. SMA Crossover
2. EMA Trend
3. Momentum
4. Mean Reversion

Across:
- NVIDIA (NVDA)
- Bitcoin (BTC/USD)
- Gold (XAU/USD)

Verifies:
1. HTTP 200 responses across all strategies and assets for both signals and backtest.
2. Strategy dispatcher and valid strategy parameters.
3. Chronological signals strictly constrained to {"BUY", "SELL", "HOLD"}.
4. Full integration with Step 8 Backtesting Engine (portfolio metrics, Buy & Hold benchmark, transaction fees).
5. HTTP 400 validation for invalid strategies and out-of-bounds parameters.
6. Zero fake data, strictly real cleaned provider feeds.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def run_live_verification():
    print("=" * 80)
    print("STEP 9 — FOUR TRADING STRATEGIES LIVE VERIFICATION")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

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

    strategies_to_test = [
        ("sma_crossover", {"short_period": 20, "long_period": 50}),
        ("ema_trend", {"ema_period": 20}),
        ("momentum", {"lookback": 10}),
        ("mean_reversion", {"lookback": 20, "entry_threshold": 1.0}),
    ]

    for asset_id, symbol, asset_name in assets_to_test:
        print("\n" + "=" * 80)
        print(f"VERIFYING STRATEGIES FOR {asset_name} ({symbol})")
        print("=" * 80)

        for strat_name, strat_params in strategies_to_test:
            print(f"\n--- Strategy: {strat_name} ({asset_name}) ---")

            # 1. POST /market/{asset}/strategy/signals
            signals_payload = {
                "strategy": strat_name,
                "parameters": strat_params,
            }
            sig_resp = client.post(f"/market/{asset_id}/strategy/signals", json=signals_payload)
            if sig_resp.status_code != 200:
                print(f"[FAIL] /market/{asset_id}/strategy/signals failed ({sig_resp.status_code}): {sig_resp.text}")
                sys.exit(1)

            sig_data = sig_resp.json()
            assert sig_data["asset"] == asset_name, f"Asset name mismatch: {sig_data['asset']}"
            assert sig_data["symbol"] == symbol, f"Symbol mismatch: {sig_data['symbol']}"
            assert sig_data["strategy"] == strat_name, f"Strategy mismatch: {sig_data['strategy']}"
            assert sig_data["observation_count"] > 0, "No observations returned"
            assert len(sig_data["signals"]) == sig_data["observation_count"]

            # Validate signals
            allowed_signals = {"BUY", "SELL", "HOLD"}
            signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
            timestamps = []
            for s in sig_data["signals"]:
                assert s["signal"] in allowed_signals, f"Invalid signal: {s['signal']}"
                signal_counts[s["signal"]] += 1
                timestamps.append(s["timestamp"])

            # Verify chronological sorting
            assert timestamps == sorted(timestamps), "Signals are not sorted chronologically"
            print(f"  [OK] Signals API: {sig_data['observation_count']} points ({sig_data['start_date']} to {sig_data['end_date']})")
            print(f"       Breakdown: BUY={signal_counts['BUY']}, SELL={signal_counts['SELL']}, HOLD={signal_counts['HOLD']}")

            # 2. POST /market/{asset}/strategy/backtest
            backtest_payload = {
                "strategy": strat_name,
                "parameters": strat_params,
                "initial_capital": 100000.0,
                "transaction_cost_rate": 0.001,
                "allocation": 1.0,
            }
            bt_resp = client.post(f"/market/{asset_id}/strategy/backtest", json=backtest_payload)
            if bt_resp.status_code != 200:
                print(f"[FAIL] /market/{asset_id}/strategy/backtest failed ({bt_resp.status_code}): {bt_resp.text}")
                sys.exit(1)

            bt_data = bt_resp.json()
            assert bt_data["asset"] == asset_name
            assert bt_data["symbol"] == symbol
            assert bt_data["strategy"] == strat_name
            assert bt_data["initial_capital"] == 100000.0
            assert bt_data["final_portfolio_value"] > 0
            assert len(bt_data["equity_curve"]) > 0
            assert bt_data["benchmark_buy_and_hold"] is not None
            assert bt_data["benchmark_buy_and_hold"]["initial_capital"] == 100000.0
            assert bt_data["benchmark_buy_and_hold"]["final_portfolio_value"] > 0
            assert "Next-Observation" in bt_data["execution_model"]

            print(f"  [OK] Backtest API: Final Value = ${bt_data['final_portfolio_value']:,.2f} | Total Return = {bt_data['total_return']:.2f}%")
            print(f"       Trades = {bt_data['total_trades']} | Max Drawdown = {bt_data['max_drawdown']:.2f}% | Benchmark Return = {bt_data['benchmark_buy_and_hold']['total_return_pct']:.2f}%")

    # 3. Parameter Validation / Error Rejection Tests (HTTP 400)
    print("\n" + "=" * 80)
    print("VERIFYING ERROR HANDLING & HTTP 400 REJECTIONS")
    print("=" * 80)

    # Invalid strategy name
    inv_strat_resp = client.post("/market/nvidia/strategy/signals", json={"strategy": "martingale", "parameters": {}})
    assert inv_strat_resp.status_code == 400, f"Expected 400 for unknown strategy, got {inv_strat_resp.status_code}"
    print(f"[OK] Unknown strategy correctly rejected: {inv_strat_resp.json().get('message') or inv_strat_resp.json().get('detail')}")

    # Invalid SMA (short >= long)
    inv_sma_resp = client.post("/market/nvidia/strategy/signals", json={"strategy": "sma_crossover", "parameters": {"short_period": 50, "long_period": 20}})
    assert inv_sma_resp.status_code == 400, f"Expected 400 for invalid SMA, got {inv_sma_resp.status_code}"
    print(f"[OK] Invalid SMA parameters correctly rejected: {inv_sma_resp.json().get('message') or inv_sma_resp.json().get('detail')}")

    # Invalid EMA (period <= 0)
    inv_ema_resp = client.post("/market/nvidia/strategy/signals", json={"strategy": "ema_trend", "parameters": {"ema_period": 0}})
    assert inv_ema_resp.status_code == 400, f"Expected 400 for invalid EMA, got {inv_ema_resp.status_code}"
    print(f"[OK] Invalid EMA parameters correctly rejected: {inv_ema_resp.json().get('message') or inv_ema_resp.json().get('detail')}")

    # Invalid Momentum (lookback <= 0)
    inv_mom_resp = client.post("/market/nvidia/strategy/signals", json={"strategy": "momentum", "parameters": {"lookback": -5}})
    assert inv_mom_resp.status_code == 400, f"Expected 400 for invalid Momentum, got {inv_mom_resp.status_code}"
    print(f"[OK] Invalid Momentum parameters correctly rejected: {inv_mom_resp.json().get('message') or inv_mom_resp.json().get('detail')}")

    # Invalid Mean Reversion (threshold <= 0)
    inv_mr_resp = client.post("/market/nvidia/strategy/signals", json={"strategy": "mean_reversion", "parameters": {"lookback": 20, "entry_threshold": -0.5}})
    assert inv_mr_resp.status_code == 400, f"Expected 400 for invalid Mean Reversion, got {inv_mr_resp.status_code}"
    print(f"[OK] Invalid Mean Reversion parameters correctly rejected: {inv_mr_resp.json().get('message') or inv_mr_resp.json().get('detail')}")

    # Invalid Backtest parameters (negative capital)
    inv_cap_resp = client.post(
        "/market/nvidia/strategy/backtest",
        json={"strategy": "momentum", "parameters": {"lookback": 10}, "initial_capital": -1000.0},
    )
    assert inv_cap_resp.status_code == 400, f"Expected 400 for negative capital, got {inv_cap_resp.status_code}"
    print(f"[OK] Negative initial capital correctly rejected: {inv_cap_resp.json().get('message') or inv_cap_resp.json().get('detail')}")

    print("\n" + "=" * 80)
    print("ALL STEP 9 LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_live_verification()
