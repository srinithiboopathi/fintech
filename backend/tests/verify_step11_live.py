"""
backend/tests/verify_step11_live.py

Live verification script for Step 11: Market Regime Analysis.
Validates live endpoints for NVIDIA (NVDA), Bitcoin (BTC/USD), and Gold (XAU/USD).
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def verify_asset_regimes(client: httpx.Client, asset: str, symbol: str):
    print(f"\n--- Verifying {asset.upper()} ({symbol}) Market Regimes ---")

    # 1. Full Regimes Time Series
    url = f"{BASE_URL}/market/{asset}/regimes?trend_period=50&volatility_window=20"
    resp = client.get(url)
    assert resp.status_code == 200, f"Expected 200 for {asset} regimes, got {resp.status_code}: {resp.text}"
    data = resp.json()

    obs_count = data["observation_count"]
    pts = data["data"]
    assert obs_count > 0, f"Expected > 0 observations for {asset}"
    assert len(pts) == obs_count, f"Mismatch in point count: {len(pts)} vs {obs_count}"

    # Verify chronological ordering
    ts_list = [p["timestamp"] for p in pts]
    assert ts_list == sorted(ts_list), f"Timestamps for {asset} not in chronological order!"

    # Verify fields in every point
    combined_regimes = set()
    for p in pts:
        assert "timestamp" in p
        assert "close" in p
        assert "trend_state" in p
        assert p["trend_state"] in {"BULLISH", "BEARISH", "SIDEWAYS", "UNKNOWN"}
        assert "volatility_state" in p
        assert p["volatility_state"] in {"HIGH_VOLATILITY", "LOW_VOLATILITY", "UNKNOWN"}
        assert "combined_regime" in p
        combined_regimes.add(p["combined_regime"])

    print(f"  [OK] Full Regimes Time Series (50/20): {obs_count} points, {len(combined_regimes)} unique regimes observed: {sorted(combined_regimes)}")

    # 1b. Active Regimes with shorter window (trend_period=10, volatility_window=5)
    url_active = f"{BASE_URL}/market/{asset}/regimes?trend_period=10&volatility_window=5"
    resp_active = client.get(url_active)
    assert resp_active.status_code == 200
    data_active = resp_active.json()
    active_regimes = set(p["combined_regime"] for p in data_active["data"] if p["combined_regime"] != "UNKNOWN")
    print(f"  [OK] Active Non-UNKNOWN Regimes (10/5): observed {sorted(active_regimes)}")

    # 2. Executive Summary
    summary_url = f"{BASE_URL}/market/{asset}/regimes/summary?trend_period=10&volatility_window=5"
    sum_resp = client.get(summary_url)
    assert sum_resp.status_code == 200, f"Expected 200 for {asset} summary, got {sum_resp.status_code}: {sum_resp.text}"
    sum_data = sum_resp.json()

    regimes_list = sum_data["regimes"]
    assert len(regimes_list) > 0, f"Expected regimes list in summary for {asset}"
    total_pct = sum(r["percentage"] for r in regimes_list)
    assert 99.0 <= total_pct <= 101.0, f"Percentage sum {total_pct}% is outside expected range"

    print(f"  [OK] Executive Summary: {len(regimes_list)} regime categories, percentage sum: {total_pct:.2f}%")
    for r in regimes_list:
        print(f"       * {r['regime']:<20}: {r['observation_count']:>4} bars ({r['percentage']:>5.2f}%)")

    # 3. Strategy Performance by Regime
    perf_url = f"{BASE_URL}/market/{asset}/regimes/performance?trend_period=50&volatility_window=20"
    perf_resp = client.get(perf_url)
    assert perf_resp.status_code == 200, f"Expected 200 for {asset} performance, got {perf_resp.status_code}: {perf_resp.text}"
    perf_data = perf_resp.json()

    perfs = perf_data["performances"]
    assert len(perfs) > 0, f"Expected performance records for {asset}"
    strategies = set(p["strategy"] for p in perfs)
    assert len(strategies) == 4, f"Expected all 4 strategies in performance breakdown, found {strategies}"
    print(f"  [OK] Strategy Attribution: {len(perfs)} regime-strategy pairs across all 4 strategies")


def verify_error_handling(client: httpx.Client):
    print("\n--- Verifying Parameter Validation & Error Handling ---")

    # 1. Unsupported Asset
    resp = client.get(f"{BASE_URL}/market/unsupported_coin/regimes")
    assert resp.status_code == 400, f"Expected 400 for unsupported asset, got {resp.status_code}"
    assert resp.json()["error"] == "UNSUPPORTED_ASSET"
    print("  [OK] Unsupported asset properly rejected with HTTP 400")

    # 2. Invalid Trend Period (< 1)
    resp = client.get(f"{BASE_URL}/market/nvidia/regimes?trend_period=0")
    assert resp.status_code == 400, f"Expected 400 for trend_period=0, got {resp.status_code}"
    print("  [OK] trend_period=0 properly rejected with HTTP 400")

    # 3. Invalid Volatility Window (< 2)
    resp = client.get(f"{BASE_URL}/market/nvidia/regimes?volatility_window=1")
    assert resp.status_code == 400, f"Expected 400 for volatility_window=1, got {resp.status_code}"
    print("  [OK] volatility_window=1 properly rejected with HTTP 400")

    # 4. Negative Volatility Threshold
    resp = client.get(f"{BASE_URL}/market/nvidia/regimes?volatility_threshold=-2.5")
    assert resp.status_code == 400, f"Expected 400 for volatility_threshold=-2.5, got {resp.status_code}"
    print("  [OK] negative volatility_threshold properly rejected with HTTP 400")


def main():
    print("==================================================")
    print("STEP 11 LIVE VERIFICATION: MARKET REGIME ANALYSIS")
    print("==================================================")

    with httpx.Client(timeout=60.0) as client:
        # Check health
        health = client.get(f"{BASE_URL}/health").json()
        print(f"Connected to backend on {BASE_URL}. Provider: {health['primary_provider']}")

        # Verify all 3 assets
        verify_asset_regimes(client, "nvidia", "NVDA")
        verify_asset_regimes(client, "bitcoin", "BTC/USD")
        verify_asset_regimes(client, "gold", "XAU/USD")

        # Verify error cases
        verify_error_handling(client)

    print("\n==================================================")
    print("ALL STEP 11 LIVE VERIFICATIONS PASSED SUCCESSFULLY")
    print("==================================================")


if __name__ == "__main__":
    main()
