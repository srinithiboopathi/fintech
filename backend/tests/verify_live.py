"""
Live verification script for all market endpoints.
Tests:
- /health
- /assets
- /market/nvidia/historical
- /market/bitcoin/historical
- /market/gold/historical
- /market/nvidia/latest
- /market/bitcoin/latest
- /market/gold/latest
"""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

ENDPOINTS = [
    ("/health", "GET /health (System Health)"),
    ("/assets", "GET /assets (Supported Universe)"),
    ("/market/nvidia/historical?outputsize=compact", "GET /market/nvidia/historical (NVIDIA Historical)"),
    ("/market/bitcoin/historical", "GET /market/bitcoin/historical (Bitcoin Historical)"),
    ("/market/gold/historical", "GET /market/gold/historical (Gold Historical)"),
    ("/market/nvidia/latest", "GET /market/nvidia/latest (NVIDIA Latest)"),
    ("/market/bitcoin/latest", "GET /market/bitcoin/latest (Bitcoin Latest)"),
    ("/market/gold/latest", "GET /market/gold/latest (Gold Latest)"),
]

def run_verification():
    print("=" * 70)
    print("RUNNING LIVE ENDPOINT VERIFICATION")
    print("=" * 70)
    
    for path, description in ENDPOINTS:
        url = f"{BASE_URL}{path}"
        print(f"\n---> Testing: {description}")
        print(f"URL: {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantPlatformVerifier/1.0"})
            with urllib.request.urlopen(req) as response:
                status = response.status
                raw = response.read().decode("utf-8")
                data = json.loads(raw)
                print(f"HTTP Status: {status} OK")
                
                # Print a clean sample of the data
                if "data" in data and isinstance(data["data"], list):
                    sample = {
                        "asset": data.get("asset"),
                        "symbol": data.get("symbol"),
                        "source": data.get("source"),
                        "data_status": data.get("data_status"),
                        "total_count": data.get("count"),
                        "sample_first_point": data["data"][0] if data["data"] else None,
                        "sample_last_point": data["data"][-1] if data["data"] else None,
                    }
                    print("Sample Data Summary:")
                    print(json.dumps(sample, indent=2))
                else:
                    print("Data Response:")
                    print(json.dumps(data, indent=2))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            print(f"HTTP Status: {e.code} Error")
            try:
                print(json.dumps(json.loads(err_body), indent=2))
            except Exception:
                print(err_body)
        except Exception as e:
            print(f"Connection Error: {e}")
        import time
        time.sleep(2)

if __name__ == "__main__":
    run_verification()
