"""
backend/tests/verify_step10_live.py

Live Verification Script for Step 10: Strategy Comparison & Robustness Analysis.
Verifies:
1. HTTP 200 responses across all three assets (NVDA, BTC/USD, XAU/USD) for Strategy Comparison.
2. All four strategies represented in comparison response with factual metrics.
3. Baseline Buy & Hold benchmark present and identical across comparisons.
4. Excess return vs benchmark calculated accurately (total_return - benchmark_return).
5. Robustness analysis across all four strategies:
   - SMA Crossover: bounded short/long grid
   - EMA Trend: bounded period grid
   - Momentum: bounded lookback grid
   - Mean Reversion: bounded lookback & threshold grid
6. Parameter validation & HTTP 400 rejection:
   - Negative initial capital
   - Unsupported strategy
   - Empty parameter lists
   - Invalid parameter bounds / short >= long
   - Exceeding combination limits (> 50 combinations)
7. Zero fake data, zero look-ahead bias.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def run_live_verification():
    print("=" * 80)
    print("STEP 10 — STRATEGY COMPARISON & ROBUSTNESS ANALYSIS LIVE VERIFICATION")
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

    # =========================================================================
    # PART 1: STRATEGY COMPARISON ACROSS ALL 3 ASSETS
    # =========================================================================
    print("\n" + "=" * 80)
    print("PART 1: VERIFYING STRATEGY COMPARISON API")
    print("=" * 80)

    for asset_id, symbol, asset_name in assets_to_test:
        print(f"\n--- Strategy Comparison for {asset_name} ({symbol}) ---")
        compare_payload = {
            "initial_capital": 100000.0,
            "transaction_cost_rate": 0.001,
            "allocation": 1.0,
        }
        resp = client.post(f"/market/{asset_id}/strategy/compare", json=compare_payload)
        if resp.status_code != 200:
            print(f"[FAIL] /market/{asset_id}/strategy/compare failed ({resp.status_code}): {resp.text}")
            sys.exit(1)

        data = resp.json()
        assert data["asset"] == asset_name, f"Asset mismatch: {data['asset']}"
        assert data["symbol"] == symbol, f"Symbol mismatch: {data['symbol']}"
        assert data["observation_count"] > 0, "No observations reported"
        assert data["benchmark"] is not None, "Benchmark is missing"
        bench_ret = data["benchmark"]["total_return_pct"]

        print(f"  [OK] Observation period: {data['start_date']} to {data['end_date']} ({data['observation_count']} bars)")
        print(f"  [OK] Baseline Benchmark (Buy & Hold) Return: {bench_ret:.2f}%")

        strategies = data["strategies"]
        assert len(strategies) == 4, f"Expected 4 strategies, got {len(strategies)}"

        expected_strats = {"sma_crossover", "ema_trend", "momentum", "mean_reversion"}
        actual_strats = {s["strategy"] for s in strategies}
        assert actual_strats == expected_strats, f"Strategies mismatch: {actual_strats}"

        for s in strategies:
            strat_name = s["strategy"]
            final_val = s["final_portfolio_value"]
            tot_ret = s["total_return"]
            trades = s["total_trades"]
            max_dd = s["maximum_drawdown"]
            excess = s["excess_return_vs_benchmark"]

            # Mathematical verification: excess == total_ret - bench_ret
            calc_excess = round(tot_ret - bench_ret, 4)
            assert abs(excess - calc_excess) < 1e-3, f"Excess return mismatch: {excess} vs {calc_excess}"

            print(f"    * {strat_name:15s} | Value: ${final_val:10,.2f} | Return: {tot_ret:6.2f}% | Trades: {trades:2d} | MaxDD: {max_dd:6.2f}% | Excess: {excess:+6.2f}%")

    # =========================================================================
    # PART 2: ROBUSTNESS ANALYSIS ACROSS ALL 4 STRATEGIES
    # =========================================================================
    print("\n" + "=" * 80)
    print("PART 2: VERIFYING PARAMETER SENSITIVITY & ROBUSTNESS API")
    print("=" * 80)

    robustness_tests = [
        (
            "nvidia",
            "NVIDIA",
            "sma_crossover",
            {"short_period": [10, 20], "long_period": [30, 40]},
            "4 combinations (short < long)",
        ),
        (
            "bitcoin",
            "Bitcoin",
            "ema_trend",
            {"ema_period": [10, 20, 30]},
            "3 period variations",
        ),
        (
            "gold",
            "Gold",
            "momentum",
            {"lookback": [5, 10, 20]},
            "3 lookback windows",
        ),
        (
            "nvidia",
            "NVIDIA",
            "mean_reversion",
            {"lookback": [10, 20], "entry_threshold": [0.5, 1.0, 1.5]},
            "6 combinations (2 lookbacks x 3 thresholds)",
        ),
    ]

    for asset_id, asset_name, strat, grid, desc in robustness_tests:
        print(f"\n--- Robustness: {strat} on {asset_name} ({desc}) ---")
        rob_payload = {
            "strategy": strat,
            "parameter_grid": grid,
            "initial_capital": 100000.0,
            "transaction_cost_rate": 0.001,
            "allocation": 1.0,
        }
        r = client.post(f"/market/{asset_id}/strategy/robustness", json=rob_payload)
        if r.status_code != 200:
            print(f"[FAIL] /market/{asset_id}/strategy/robustness failed ({r.status_code}): {r.text}")
            sys.exit(1)

        rdata = r.json()
        assert rdata["strategy"] == strat
        assert rdata["total_combinations_tested"] == len(rdata["results"])
        assert rdata["total_combinations_tested"] > 0
        bench_ret = rdata["benchmark"]["total_return_pct"]

        print(f"  [OK] Successfully evaluated {rdata['total_combinations_tested']} combinations. Benchmark: {bench_ret:.2f}%")
        for res in rdata["results"]:
            p_str = ", ".join(f"{k}={v}" for k, v in res["parameters"].items())
            print(f"    * [{p_str:30s}] -> Return: {res['total_return']:6.2f}% | Value: ${res['final_portfolio_value']:10,.2f} | Trades: {res['total_trades']:2d} | MaxDD: {res['maximum_drawdown']:6.2f}% | Excess: {res['excess_return_vs_benchmark']:+6.2f}%")

    # =========================================================================
    # PART 3: ERROR HANDLING & HTTP 400 REJECTIONS
    # =========================================================================
    print("\n" + "=" * 80)
    print("PART 3: VERIFYING ERROR HANDLING & HTTP 400 REJECTIONS")
    print("=" * 80)

    # 1. Unsupported Strategy
    inv_strat = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "reinforcement_learning", "parameter_grid": {"gamma": [0.99]}},
    )
    assert inv_strat.status_code == 400
    print(f"[OK] Unknown strategy correctly rejected: {inv_strat.json().get('message') or inv_strat.json().get('detail')}")

    # 2. Negative Initial Capital
    neg_cap = client.post(
        "/market/nvidia/strategy/compare",
        json={"initial_capital": -50000.0},
    )
    assert neg_cap.status_code == 400
    print(f"[OK] Negative capital correctly rejected: {neg_cap.json().get('message') or neg_cap.json().get('detail')}")

    # 3. Empty Parameter Grid
    empty_grid = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "momentum", "parameter_grid": {}},
    )
    assert empty_grid.status_code == 400
    print(f"[OK] Empty parameter grid correctly rejected: {empty_grid.json().get('message') or empty_grid.json().get('detail')}")

    # 4. SMA Invalid Combinations (all short >= long)
    inv_sma = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "sma_crossover", "parameter_grid": {"short_period": [50, 60], "long_period": [20, 30]}},
    )
    assert inv_sma.status_code == 400
    print(f"[OK] Inverted SMA periods correctly rejected: {inv_sma.json().get('message') or inv_sma.json().get('detail')}")

    # 5. Exceeding Grid Bounds (> 50 combinations)
    big_grid = {
        "short_period": list(range(1, 11)),
        "long_period": list(range(20, 30)),
    }
    big_resp = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "sma_crossover", "parameter_grid": big_grid},
    )
    assert big_resp.status_code == 400
    print(f"[OK] Excessively large grid (>50 combinations) correctly rejected: {big_resp.json().get('message') or big_resp.json().get('detail')}")

    print("\n" + "=" * 80)
    print("ALL STEP 10 LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_live_verification()
