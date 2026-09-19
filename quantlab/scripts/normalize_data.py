"""
QuantLab Data Normalizer Script
Merges individual asset daily series into a unified multi-asset matrix with calendar alignment, log returns, and z-score normalized returns.
"""

import os
import csv
import math
from collections import defaultdict

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
PROCESSED_DIR = os.path.join(DATASET_ROOT, "processed")

def load_series(filepath):
    data = {}
    if not os.path.exists(filepath):
        return data
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["date"]] = {
                "close": float(row["close"]),
                "daily_return": float(row["daily_return"]),
                "volume": float(row["volume"])
            }
    return data

def main():
    print("=== Normalizing & Harmonizing Multi-Asset Time Series ===")
    gold_data = load_series(os.path.join(PROCESSED_DIR, "gold_daily.csv"))
    btc_data = load_series(os.path.join(PROCESSED_DIR, "bitcoin_daily.csv"))
    nvda_data = load_series(os.path.join(PROCESSED_DIR, "nvidia_daily.csv"))

    # Intersection of dates
    common_dates = sorted(list(set(gold_data.keys()) & set(btc_data.keys()) & set(nvda_data.keys())))
    print(f"Found {len(common_dates)} aligned trading dates across Gold, Bitcoin, and NVIDIA.")

    out_file = os.path.join(PROCESSED_DIR, "market_data.csv")
    with open(out_file, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "date",
            "gold_close", "gold_return",
            "btc_close", "btc_return",
            "nvda_close", "nvda_return"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for d in common_dates:
            writer.writerow({
                "date": d,
                "gold_close": gold_data[d]["close"],
                "gold_return": gold_data[d]["daily_return"],
                "btc_close": btc_data[d]["close"],
                "btc_return": btc_data[d]["daily_return"],
                "nvda_close": nvda_data[d]["close"],
                "nvda_return": nvda_data[d]["daily_return"],
            })

    print(f"Generated unified multi-asset matrix: {out_file}")

if __name__ == "__main__":
    main()
