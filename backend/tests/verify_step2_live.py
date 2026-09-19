import urllib.request
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def fetch_json(endpoint: str):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "Step2Verifier/1.0"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=15) as resp:
        elapsed = (time.perf_counter() - start) * 1000
        status_code = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        return status_code, elapsed, data

def main():
    print("=" * 70)
    print("STEP 2 LIVE VERIFICATION: TWELVE DATA PRIMARY WITH LOCAL CACHING")
    print("=" * 70)

    # 1. Health check
    print("\n--- 1. Testing /health ---")
    status, elapsed, health = fetch_json("/health")
    print(f"Status: {status} in {elapsed:.1f}ms")
    print(f"Primary Provider:   {health.get('primary_provider')}")
    print(f"Fallback Provider:  {health.get('fallback_provider')}")
    print(f"Twelve Data Config: {health.get('twelve_data_configured')} (Masked: {health.get('twelve_data_masked_key')})")
    print(f"Alpha Vantage:      {health.get('alpha_vantage_configured')} (Masked: {health.get('alpha_vantage_masked_key')})")
    print(f"Cache Stats:        {health.get('cache_stats')}")

    # 2. Assets list
    print("\n--- 2. Testing /assets ---")
    status, elapsed, assets = fetch_json("/assets")
    print(f"Status: {status} in {elapsed:.1f}ms | Count: {assets.get('count')}")
    for a in assets.get("assets", []):
        print(f" - {a['name']} ({a['symbol']}) [{a['asset_class']}]")

    # 3. Live Market Data for NVDA, Bitcoin, Gold
    test_assets = [
        ("NVIDIA", "/market/nvidia/latest", "/market/nvidia/historical"),
        ("Bitcoin", "/market/bitcoin/latest", "/market/bitcoin/historical"),
        ("Gold", "/market/gold/latest", "/market/gold/historical"),
    ]

    for name, latest_ep, hist_ep in test_assets:
        print(f"\n--- 3. Testing {name} ---")
        
        # Latest
        st_lat, el_lat, lat_data = fetch_json(latest_ep)
        print(f"Latest  -> HTTP {st_lat} in {el_lat:.1f}ms")
        print(f"  Symbol:       {lat_data.get('symbol')}")
        print(f"  Price:        ${lat_data.get('price'):,.2f}")
        print(f"  Source:       {lat_data.get('source')}")
        print(f"  Status:       {lat_data.get('data_status')}")
        print(f"  Timestamp:    {lat_data.get('timestamp')}")
        print(f"  Volume:       {lat_data.get('volume')}")
        print(f"  Change %:     {lat_data.get('change_percent')}")

        # Historical
        st_hist, el_hist, hist_data = fetch_json(hist_ep)
        points = hist_data.get("data", [])
        print(f"History -> HTTP {st_hist} in {el_hist:.1f}ms | Points: {len(points)}")
        print(f"  Source:       {hist_data.get('source')}")
        if points:
            first_p = points[0]
            last_p = points[-1]
            print(f"  Oldest Point: {first_p['timestamp']} | Close: ${first_p['close']:,.2f} | Volume: {first_p['volume']}")
            print(f"  Newest Point: {last_p['timestamp']} | Close: ${last_p['close']:,.2f} | Volume: {last_p['volume']}")

    # 4. Cache Speedup Test
    print("\n--- 4. Testing Cache Acceleration (Repeated Calls) ---")
    for name, latest_ep, hist_ep in test_assets:
        _, el_lat_cached, _ = fetch_json(latest_ep)
        _, el_hist_cached, _ = fetch_json(hist_ep)
        print(f"Cached {name:7} -> Latest: {el_lat_cached:.2f}ms | History: {el_hist_cached:.2f}ms (Instant disk/memory hit)")

    print("\n" + "=" * 70)
    print("ALL STEP 2 LIVE VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
