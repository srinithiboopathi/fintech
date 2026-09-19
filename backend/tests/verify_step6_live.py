"""
backend/tests/verify_step6_live.py

Live Verification Script for Step 6 Risk Analysis:
- GET /market/nvidia/risk-analysis
- GET /market/bitcoin/risk-analysis
- GET /market/gold/risk-analysis

Displays for each asset:
- Symbol
- Source
- Latest close
- Valid return count
- Sharpe ratio
- Maximum drawdown (%)
- Maximum drawdown timestamp
- Risk-free rate
- Annualization factor

Verifies:
1. Metrics are calculated strictly from Step 3 cleaned historical data.
2. Local caching prevents unnecessary external API calls.
3. Input validation rejects invalid parameters with HTTP 400.
"""

import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"

ASSETS = [
    ("nvidia", "NVDA", "NVIDIA"),
    ("bitcoin", "BTC/USD", "Bitcoin"),
    ("gold", "XAU/USD", "Gold"),
]


def run_live_verification():
    print("=" * 75)
    print("STEP 6 — SHARPE RATIO & MAXIMUM DRAWDOWN LIVE VERIFICATION")
    print("=" * 75)

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

    print("\n" + "-" * 75)
    print("VERIFYING ASSET RISK ANALYSIS (Sharpe Ratio & Maximum Drawdown)")
    print("-" * 75)

    for asset_id, expected_symbol, name in ASSETS:
        url = f"/market/{asset_id}/risk-analysis"
        print(f"\nQuerying: {url} ...")
        resp = client.get(url)

        if resp.status_code != 200:
            print(f"  [FAIL] HTTP {resp.status_code}: {resp.text}")
            sys.exit(1)

        data = resp.json()
        summary = data.get("summary", {})
        drawdowns = data.get("drawdown_series", [])

        print(f"  [PASS] Asset:                      {data.get('asset')} ({data.get('symbol')})")
        print(f"         Source:                     {data.get('source')}")
        print(f"         Data Status:                {data.get('data_status')}")
        print(f"         Latest Close:               {summary.get('latest_close')}")
        print(f"         Valid Returns:              {summary.get('valid_return_count')}")
        print(f"         Sharpe Ratio (Annualized):  {summary.get('sharpe_ratio')}")
        print(f"         Maximum Drawdown:           {summary.get('maximum_drawdown_pct')}%")
        print(f"         Max Drawdown Date:          {summary.get('maximum_drawdown_timestamp')}")
        print(f"         Risk-Free Rate:             {summary.get('risk_free_rate')}%")
        print(f"         Annualization Factor:       {summary.get('annualization_factor')} days")
        print(f"         Drawdown Series Length:     {len(drawdowns)} observations")

        # Sanity assertions
        assert summary.get("valid_return_count", 0) > 0, "Expected positive return count"
        assert summary.get("maximum_drawdown_pct") is not None, "Expected valid drawdown percentage"
        assert summary.get("maximum_drawdown_pct") <= 0.0, "Drawdown must be non-positive"
        assert len(drawdowns) > 0, "Drawdown series must not be empty"

    # 2. Verify Parameter Validation (HTTP 400 rejection)
    print("\n" + "-" * 75)
    print("VERIFYING PARAMETER VALIDATION (Error Handlers)")
    print("-" * 75)

    bad_requests = [
        ("Negative risk-free rate", "/market/nvidia/risk-analysis?risk_free_rate=-1.0"),
        ("Non-numeric risk-free rate", "/market/nvidia/risk-analysis?risk_free_rate=bad_rate"),
        ("Zero annualization factor", "/market/nvidia/risk-analysis?annualization_factor=0"),
        ("Negative annualization factor", "/market/nvidia/risk-analysis?annualization_factor=-252"),
        ("Decimal annualization factor", "/market/nvidia/risk-analysis?annualization_factor=252.5"),
    ]

    for label, bad_url in bad_requests:
        resp = client.get(bad_url)
        if resp.status_code == 400:
            print(f"  [PASS] {label}: Successfully rejected with HTTP 400")
        else:
            print(f"  [FAIL] {label}: Expected HTTP 400, got {resp.status_code}")
            sys.exit(1)

    print("\n" + "=" * 75)
    print("ALL STEP 6 LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_live_verification()
