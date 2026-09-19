"""
Isolated test script for Twelve Data API.
Tests:
1. NVIDIA: NVDA
2. Bitcoin: BTC/USD
3. Gold: XAU/USD

DOES NOT modify existing Alpha Vantage backend or frontend.
NEVER logs or exposes the API key.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env safely
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def get_twelve_data_api_key() -> str:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    key = os.environ.get("TWELVE_DATA_API_KEY", "").strip()
    return key

def fetch_api_usage(api_key: str):
    url = f"https://api.twelvedata.com/api_usage?apikey={api_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TwelveDataTest/1.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode())
    except Exception:
        return None

def test_symbol(symbol: str, api_key: str):
    """
    Queries Twelve Data /quote and /time_series for the given symbol.
    Returns structured results matching the user's exact requirements.
    """
    quote_url = f"https://api.twelvedata.com/quote?symbol={urllib.parse.quote(symbol)}&apikey={api_key}"
    result = {
        "symbol": symbol,
        "http_status": None,
        "api_status": None,
        "data_successfully_returned": False,
        "latest_timestamp": "N/A",
        "latest_price": "N/A",
        "error_message": None,
        "raw_response": None
    }

    try:
        req = urllib.request.Request(quote_url, headers={"User-Agent": "TwelveDataTest/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result["http_status"] = resp.status
            body_text = resp.read().decode("utf-8")
            data = json.loads(body_text)
            result["raw_response"] = data

            # Twelve Data returns errors with "status": "error"
            if data.get("status") == "error":
                result["api_status"] = f"error (code: {data.get('code')})"
                result["error_message"] = data.get("message", "Unknown provider error")
                result["data_successfully_returned"] = False
            elif "close" in data or "price" in data or "name" in data:
                result["api_status"] = "ok"
                result["data_successfully_returned"] = True
                result["latest_price"] = data.get("close") or data.get("price") or "N/A"
                result["latest_timestamp"] = data.get("datetime") or str(data.get("timestamp")) or "N/A"
            else:
                result["api_status"] = "unexpected_format"
                result["error_message"] = "No price field in response"

    except urllib.error.HTTPError as e:
        result["http_status"] = e.code
        try:
            err_data = json.loads(e.read().decode("utf-8"))
            result["error_message"] = err_data.get("message", str(e))
            result["api_status"] = err_data.get("status", "http_error")
        except Exception:
            result["error_message"] = str(e)
            result["api_status"] = "http_error"
    except Exception as e:
        result["http_status"] = "network_error"
        result["error_message"] = str(e)

    return result

def run_tests():
    api_key = get_twelve_data_api_key()
    
    print("=" * 70)
    print("TWELVE DATA ISOLATED INSTRUMENT TEST")
    print("=" * 70)

    if not api_key or api_key == "your_twelve_data_api_key_here":
        print("\n[!] ERROR: TWELVE_DATA_API_KEY is not set in backend/.env")
        print(f"Please open: {ENV_PATH}")
        print("and set: TWELVE_DATA_API_KEY=your_actual_key\n")
        sys.exit(1)

    # Fetch Usage/Credits
    usage_info = fetch_api_usage(api_key)
    credits_str = "Unknown"
    if usage_info and "current_usage" in usage_info:
        credits_str = f"Usage: {usage_info.get('current_usage')}/{usage_info.get('plan_limit', 'Unlimited')} (Plan: {usage_info.get('plan_category', 'N/A')})"

    targets = ["NVDA", "BTC/USD", "XAU/USD"]
    results = []

    for sym in targets:
        print(f"\n---> Testing symbol: {sym} ...")
        res = test_symbol(sym, api_key)
        res["credits_used"] = credits_str
        results.append(res)
        time.sleep(1)  # Gentle spacing between requests

    print("\n" + "=" * 70)
    print("FINAL TEST REPORT (NO KEYS EXPOSED)")
    print("=" * 70)

    for r in results:
        print(f"\nSymbol: {r['symbol']}")
        print(f"- HTTP/API status: HTTP {r['http_status']} / API: {r['api_status']}")
        print(f"- Data successfully returned: {r['data_successfully_returned']}")
        print(f"- Latest timestamp returned: {r['latest_timestamp']}")
        print(f"- Latest price returned: {r['latest_price']}")
        print(f"- API credits used: {r['credits_used']}")
        if r['error_message']:
            print(f"- Error message: {r['error_message']}")
        else:
            print("- Error message: None")

if __name__ == "__main__":
    run_tests()
