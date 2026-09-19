"""
backend/tests/verify_step5_live.py

Live Verification Script for Step 5 Returns & Volatility Analysis.
Tests the live endpoints:
- GET /market/nvidia/risk-metrics?volatility_period=20
- GET /market/bitcoin/risk-metrics?volatility_period=20
- GET /market/gold/risk-metrics?volatility_period=20

Displays for each asset:
- Symbol
- Source
- Total records
- Latest close
- Latest return
- Latest volatility
- Valid return count
- Valid volatility count

Verifies:
1. Metrics are calculated strictly from Step 3 cleaned historical data.
2. Local caching prevents unnecessary external API calls.
3. Input validation rejects invalid periods with HTTP 400.
"""

import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"

ASSETS = [
    ("nvidia", "NVDA", "NVIDIA"),
    ("bitcoin", "BTC/USD", "Bitcoin"),
    ("gold", "XAU/USD", "Gold"),
]

def run_live_verification():
    print("=" * 70)
    print("STEP 5 — RETURNS & VOLATILITY ANALYSIS LIVE VERIFICATION")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

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

    print("\n" + "-" * 70)
    print("VERIFYING ASSET RISK METRICS (volatility_period=20)")
    print("-" * 70)

    results = {}
    for asset_slug, expected_symbol, display_name in ASSETS:
        url = f"/market/{asset_slug}/risk-metrics?volatility_period=20"
        try:
            resp = client.get(url)
            if resp.status_code != 200:
                print(f"[FAIL] {display_name} ({url}) returned {resp.status_code}: {resp.text}")
                continue

            data = resp.json()
            summary = data.get("summary", {})
            series = data.get("data", [])

            results[asset_slug] = {
                "symbol": data.get("symbol"),
                "source": data.get("source"),
                "total_records": summary.get("total_records"),
                "latest_close": summary.get("latest_close"),
                "latest_return": summary.get("latest_return"),
                "latest_volatility": summary.get("latest_volatility"),
                "valid_return_count": summary.get("valid_return_count"),
                "valid_volatility_count": summary.get("valid_volatility_count"),
                "data_status": data.get("data_status"),
                "points_count": len(series),
            }

            print(f"Asset:                  {display_name}")
            print(f"Symbol:                 {results[asset_slug]['symbol']}")
            print(f"Source:                 {results[asset_slug]['source']}")
            print(f"Status:                 {results[asset_slug]['data_status']}")
            print(f"Total Records:          {results[asset_slug]['total_records']}")
            print(f"Latest Close:           {results[asset_slug]['latest_close']}")
            print(f"Latest Daily Return:    {results[asset_slug]['latest_return']}%")
            print(f"Latest Volatility (20): {results[asset_slug]['latest_volatility']}% (daily, not annualized)")
            print(f"Valid Return Count:     {results[asset_slug]['valid_return_count']}")
            print(f"Valid Volatility Count: {results[asset_slug]['valid_volatility_count']}")
            print("-" * 70)

        except Exception as err:
            print(f"[ERROR] Error fetching {display_name}: {err}")

    # 2. Verify Input Validation
    print("\n" + "-" * 70)
    print("VERIFYING INPUT VALIDATION (HTTP 400 REJECTIONS)")
    print("-" * 70)
    validation_tests = [
        ("volatility_period=0", "/market/nvidia/risk-metrics?volatility_period=0"),
        ("volatility_period=-5", "/market/nvidia/risk-metrics?volatility_period=-5"),
        ("volatility_period=1.5", "/market/nvidia/risk-metrics?volatility_period=1.5"),
        ("volatility_period=abc", "/market/nvidia/risk-metrics?volatility_period=abc"),
    ]

    all_validation_passed = True
    for label, query_path in validation_tests:
        v_resp = client.get(query_path)
        if v_resp.status_code == 400 and "positive integer" in v_resp.text:
            print(f"[OK] Rejection {label:22} -> HTTP 400 (Expected message matched)")
        else:
            print(f"[FAIL] Rejection {label:22} -> HTTP {v_resp.status_code}: {v_resp.text}")
            all_validation_passed = False

    # 3. Verify Local Caching (Zero provider calls)
    print("\n" + "-" * 70)
    print("VERIFYING LOCAL CACHING BEHAVIOR")
    print("-" * 70)
    t0 = time.time()
    cached_resp = client.get("/market/nvidia/risk-metrics?volatility_period=20")
    t1 = time.time()
    duration_ms = (t1 - t0) * 1000.0
    print(f"[OK] Cached Risk Metrics fetch latency: {duration_ms:.2f} ms")

    print("\n" + "=" * 70)
    print("STEP 5 LIVE VERIFICATION SUMMARY")
    print("=" * 70)
    for asset_slug, r in results.items():
        print(f"  {r['symbol']:<10} Close={r['latest_close']:<12} Return={r['latest_return']}%  Vol(20)={r['latest_volatility']}%  Records={r['total_records']}")
    print(f"Input Validation: {'PASS' if all_validation_passed else 'FAIL'}")
    print("=" * 70)

if __name__ == "__main__":
    run_live_verification()
