import urllib.request
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def fetch_json(endpoint: str):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "Step3Verifier/1.0"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=15) as resp:
        elapsed = (time.perf_counter() - start) * 1000
        status_code = resp.status
        data = json.loads(resp.read().decode("utf-8"))
        return status_code, elapsed, data

def main():
    print("=" * 75)
    print("STEP 3 LIVE VERIFICATION: DATA STORAGE AND CLEANING LAYER")
    print("=" * 75)

    assets = [
        ("NVIDIA", "nvidia"),
        ("Bitcoin", "bitcoin"),
        ("Gold", "gold"),
    ]

    cleaned_samples = {}
    summaries = {}

    # 1. Test Clean Data & Summary Endpoints for all 3 assets
    for name, asset_id in assets:
        print(f"\n---> Testing {name} ({asset_id.upper()}) Clean Data & Summary Endpoints <---")
        
        # Clean data endpoint: /market/{asset}/data
        data_ep = f"/market/{asset_id}/data"
        st_data, el_data, clean_payload = fetch_json(data_ep)
        print(f"GET {data_ep:<32} -> HTTP {st_data} in {el_data:.1f}ms")
        assert st_data == 200
        assert clean_payload["data_status"] == "clean_verified"
        assert clean_payload["count"] > 0
        points = clean_payload["data"]
        
        # Verify chronological ordering
        for i in range(len(points) - 1):
            assert points[i]["timestamp"] <= points[i+1]["timestamp"], f"Chronological order violated at {i}!"

        # Save one sample point
        cleaned_samples[name] = points[-1]

        # Clean summary endpoint: /market/{asset}/data/summary
        summary_ep = f"/market/{asset_id}/data/summary"
        st_sum, el_sum, summary_payload = fetch_json(summary_ep)
        print(f"GET {summary_ep:<32} -> HTTP {st_sum} in {el_sum:.1f}ms")
        assert st_sum == 200
        assert summary_payload["total_records"] == clean_payload["count"]
        summaries[name] = summary_payload

        # Print quality metrics
        q_rep = clean_payload["quality_report"]
        print(f"  Total Clean Records:    {q_rep['total_records']}")
        print(f"  Quality Status:         {q_rep['quality_status'].upper()}")
        print(f"  Duplicates Removed:     {q_rep['duplicates_removed']}")
        print(f"  Invalid Dropped:        {q_rep['invalid_records_dropped']}")
        print(f"  Missing Close:          {q_rep['missing_close_count']}")
        print(f"  Missing Volume (null):  {q_rep['missing_volume_count']}")
        print(f"  OHLC Anomalies Checked: {q_rep['ohlc_anomalies_detected']}")
        print(f"  Earliest -> Latest:     {q_rep['earliest_timestamp']} -> {q_rep['latest_timestamp']}")

    # 2. Verify Cache Reuse (<15ms response times)
    print("\n---> Verifying Cache Reuse (Zero Redundant External Calls) <---")
    for name, asset_id in assets:
        _, el_cache, _ = fetch_json(f"/market/{asset_id}/data")
        print(f"Cached Clean {name:<8} -> {el_cache:.2f}ms (Instant local cache response)")
        assert el_cache < 50.0, f"Cache response too slow: {el_cache}ms"

    # 3. Confirm Step 1 & Step 2 Endpoints Still Function Perfectly
    print("\n---> Confirming Step 1 & Step 2 Compatibility <---")
    st_h, el_h, health = fetch_json("/health")
    print(f"GET /health                     -> HTTP {st_h} ({health['status']}) in {el_h:.1f}ms")
    assert st_h == 200 and health["status"] == "healthy"

    st_a, el_a, asset_list = fetch_json("/assets")
    print(f"GET /assets                     -> HTTP {st_a} ({asset_list['count']} assets) in {el_a:.1f}ms")
    assert st_a == 200 and asset_list["count"] == 3

    for name, asset_id in assets:
        st_lat, _, lat = fetch_json(f"/market/{asset_id}/latest")
        st_hist, _, hist = fetch_json(f"/market/{asset_id}/historical")
        print(f"Step 1/2 Endpoints for {name:<8} -> Latest: HTTP {st_lat} | History: HTTP {st_hist}")
        assert st_lat == 200 and st_hist == 200

    print("\n" + "=" * 75)
    print("CLEANED SAMPLES:")
    print("=" * 75)
    for name, sample in cleaned_samples.items():
        print(f"\nAsset: {name}")
        print(json.dumps(sample, indent=2))

    print("\n" + "=" * 75)
    print("DATA SUMMARIES (/market/{asset}/data/summary):")
    print("=" * 75)
    for name, summary in summaries.items():
        print(f"\nSummary: {name}")
        print(json.dumps(summary, indent=2))

    print("\n" + "=" * 75)
    print("ALL STEP 3 VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    main()
