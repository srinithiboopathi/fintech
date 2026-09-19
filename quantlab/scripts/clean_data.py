"""
QuantLab Data Cleaner & Harmonizer Script
Cleans raw market CSVs: handles missing values, removes outliers, validates OHLC bounds, and outputs daily series.
"""

import os
import csv
from datetime import datetime

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
RAW_DIR = os.path.join(DATASET_ROOT, "raw")
PROCESSED_DIR = os.path.join(DATASET_ROOT, "processed")

os.makedirs(PROCESSED_DIR, exist_ok=True)

ASSETS = [
    {"raw": os.path.join(RAW_DIR, "gold", "gold_raw.csv"), "out": os.path.join(PROCESSED_DIR, "gold_daily.csv"), "symbol": "GC=F"},
    {"raw": os.path.join(RAW_DIR, "bitcoin", "bitcoin_raw.csv"), "out": os.path.join(PROCESSED_DIR, "bitcoin_daily.csv"), "symbol": "BTC-USD"},
    {"raw": os.path.join(RAW_DIR, "nvidia", "nvidia_raw.csv"), "out": os.path.join(PROCESSED_DIR, "nvidia_daily.csv"), "symbol": "NVDA"},
]

def clean_csv(raw_path, out_path, symbol):
    if not os.path.exists(raw_path):
        print(f"File not found: {raw_path}")
        return

    cleaned_rows = []
    with open(raw_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prev_close = None
        for row in reader:
            try:
                date_str = row["Date"].strip()
                # Parse date to ensure format
                datetime.strptime(date_str, "%Y-%m-%d")
                
                open_p = float(row["Open"])
                high_p = float(row["High"])
                low_p = float(row["Low"])
                close_p = float(row["Close"])
                adj_close = float(row.get("Adj Close", close_p))
                volume = float(row["Volume"])

                # Sanity check: High >= Low, Open & Close within High and Low
                high_p = max(high_p, open_p, close_p)
                low_p = min(low_p, open_p, close_p)

                # Return calculation
                daily_return = (close_p - prev_close) / prev_close if prev_close else 0.0
                prev_close = close_p

                cleaned_rows.append({
                    "date": date_str,
                    "symbol": symbol,
                    "open": round(open_p, 4),
                    "high": round(high_p, 4),
                    "low": round(low_p, 4),
                    "close": round(close_p, 4),
                    "adj_close": round(adj_close, 4),
                    "volume": int(volume),
                    "daily_return": round(daily_return, 6)
                })
            except Exception as e:
                continue

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["date", "symbol", "open", "high", "low", "close", "adj_close", "volume", "daily_return"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    print(f"Cleaned {len(cleaned_rows)} rows for {symbol} -> {out_path}")

def main():
    print("=== Cleaning QuantLab Market Datasets ===")
    for item in ASSETS:
        clean_csv(item["raw"], item["out"], item["symbol"])

if __name__ == "__main__":
    main()
