"""
Isolated script to fetch and display actual Twelve Data live and historical data.
Assets:
1. NVIDIA (NVDA)
2. Bitcoin (BTC/USD)
3. Gold (XAU/USD)

Strictly read-only inspection.
Does NOT modify existing Alpha Vantage endpoints, config, or database.
Never prints or exposes the API key.
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env safely
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "").strip()

if not API_KEY:
    print("[ERROR] TWELVE_DATA_API_KEY not found in backend/.env")
    sys.exit(1)

ASSETS = [
    {"name": "NVIDIA", "symbol": "NVDA"},
    {"name": "Bitcoin", "symbol": "BTC/USD"},
    {"name": "Gold", "symbol": "XAU/USD"}
]

def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "TwelveDataInspector/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def format_table(rows, headers):
    """Simple ASCII table formatter."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
            
    header_str = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    sep_str = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    row_strs = []
    for row in rows:
        row_strs.append(" | ".join(f"{str(val):<{col_widths[i]}}" for i, val in enumerate(row)))
    return f"{header_str}\n{sep_str}\n" + "\n".join(row_strs)

def inspect_asset(asset_info):
    name = asset_info["name"]
    symbol = asset_info["symbol"]
    encoded_sym = urllib.parse.quote(symbol)

    print(f"\n{'='*75}")
    print(f"FETCHING REAL TWELVE DATA: {name} ({symbol})")
    print(f"{'='*75}")

    # 1. Fetch Latest Quote
    quote_url = f"https://api.twelvedata.com/quote?symbol={encoded_sym}&apikey={API_KEY}"
    quote_data = {}
    quote_status = "UNKNOWN"
    try:
        quote_data = fetch_json(quote_url)
        if quote_data.get("status") == "error":
            quote_status = f"ERROR ({quote_data.get('code')}: {quote_data.get('message')})"
        else:
            quote_status = "SUCCESS (200 OK)"
    except Exception as e:
        quote_status = f"FAILED ({e})"

    time.sleep(1) # Gentle spacing to respect 8 calls/min limit

    # 2. Fetch Historical Data (20 records)
    ts_url = f"https://api.twelvedata.com/time_series?symbol={encoded_sym}&interval=1day&outputsize=20&apikey={API_KEY}"
    ts_data = {}
    ts_status = "UNKNOWN"
    try:
        ts_data = fetch_json(ts_url)
        if ts_data.get("status") == "error":
            ts_status = f"ERROR ({ts_data.get('code')}: {ts_data.get('message')})"
        else:
            ts_status = "SUCCESS (200 OK)"
    except Exception as e:
        ts_status = f"FAILED ({e})"

    # Overall Status
    success = (quote_status.startswith("SUCCESS") and ts_status.startswith("SUCCESS"))

    # Display LATEST DATA
    print(f"\n[LATEST DATA - {name} ({symbol})]")
    print(f"API Response Status: {quote_status}")
    print(f"Symbol:             {quote_data.get('symbol', symbol)}")
    print(f"Timestamp:          {quote_data.get('datetime') or quote_data.get('timestamp') or 'N/A'}")
    print(f"Open:               {quote_data.get('open') or 'N/A'}")
    print(f"High:               {quote_data.get('high') or 'N/A'}")
    print(f"Low:                {quote_data.get('low') or 'N/A'}")
    print(f"Close / Price:      {quote_data.get('close') or quote_data.get('price') or 'N/A'}")
    print(f"Volume:             {quote_data.get('volume') or 'N/A'}")
    print(f"Previous Close:     {quote_data.get('previous_close') or 'N/A'}")
    print(f"Change:             {quote_data.get('change') or 'N/A'}")
    print(f"Percentage Change:  {quote_data.get('percent_change') or 'N/A'}")

    # Display HISTORICAL DATA TABLE
    print(f"\n[HISTORICAL DATA (Latest 20 Records) - {name} ({symbol})]")
    print(f"API Response Status: {ts_status}")
    values = ts_data.get("values", [])
    print(f"Records Received:    {len(values)}")

    if values:
        headers = ["Date/Time", "Open", "High", "Low", "Close", "Volume"]
        table_rows = []
        for v in values:
            table_rows.append([
                v.get("datetime", "N/A"),
                v.get("open", "N/A"),
                v.get("high", "N/A"),
                v.get("low", "N/A"),
                v.get("close", "N/A"),
                v.get("volume") or "N/A"
            ])
        print("\n" + format_table(table_rows, headers))
    else:
        print("No historical values returned.")

    return {
        "name": name,
        "symbol": symbol,
        "success": success,
        "quote_status": quote_status,
        "ts_status": ts_status,
        "records": len(values),
        "latest_price": quote_data.get('close') or quote_data.get('price') or 'N/A',
        "latest_time": quote_data.get('datetime') or quote_data.get('timestamp') or 'N/A'
    }

def main():
    print("=" * 75)
    print("STARTING DIRECT TWELVE DATA INSPECTION (3 ASSETS)")
    print("=" * 75)

    summaries = []
    for asset in ASSETS:
        res = inspect_asset(asset)
        summaries.append(res)
        time.sleep(1.5)

    print("\n" + "=" * 75)
    print("FINAL SUMMARY REPORT")
    print("=" * 75)
    for s in summaries:
        status_text = "SUCCESS" if s["success"] else "FAILED"
        print(f"{s['name']} ({s['symbol']}): {status_text} (Price: {s['latest_price']} | Records: {s['records']})")

if __name__ == "__main__":
    main()
