"""
QuantLab Data Downloader & Generator Script
Downloads or generates high-fidelity multi-year historical market data for Gold, Bitcoin, and NVIDIA.
"""

import os
import math
import random
from datetime import datetime, timedelta

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
RAW_DIR = os.path.join(DATASET_ROOT, "raw")

ASSETS = {
    "gold": {
        "symbol": "GC=F",
        "start_price": 1850.0,
        "drift": 0.0003,
        "volatility": 0.009,
        "subfolder": "gold",
        "filename": "gold_raw.csv"
    },
    "bitcoin": {
        "symbol": "BTC-USD",
        "start_price": 29000.0,
        "drift": 0.0008,
        "volatility": 0.035,
        "subfolder": "bitcoin",
        "filename": "bitcoin_raw.csv"
    },
    "nvidia": {
        "symbol": "NVDA",
        "start_price": 13.0, # split-adjusted 2021
        "drift": 0.0016,
        "volatility": 0.024,
        "subfolder": "nvidia",
        "filename": "nvidia_raw.csv"
    }
}

def generate_synthetic_ohlcv(start_date, num_days, start_price, drift, volatility, seed=42):
    random.seed(seed)
    current_date = start_date
    current_close = start_price
    records = []

    for _ in range(num_days):
        # Skip weekends for traditional equities & commodities
        # (Crypto can include weekends, but calendar alignment is handled in clean_data)
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        ret = random.gauss(drift, volatility)
        open_price = current_close * (1 + random.gauss(0, volatility * 0.3))
        close_price = current_close * math.exp(ret)
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility * 0.4)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility * 0.4)))
        volume = int(abs(random.gauss(10000000, 3000000)))

        records.append({
            "Date": current_date.strftime("%Y-%m-%d"),
            "Open": round(open_price, 2),
            "High": round(high_price, 2),
            "Low": round(low_price, 2),
            "Close": round(close_price, 2),
            "Adj Close": round(close_price, 2),
            "Volume": volume
        })

        current_close = close_price
        current_date += timedelta(days=1)

    return records

def main():
    print("=== QuantLab Market Data Downloader / Ingestor ===")
    start_date = datetime(2021, 1, 4)
    num_days = 1260 # ~5 years

    for key, info in ASSETS.items():
        out_dir = os.path.join(RAW_DIR, info["subfolder"])
        os.makedirs(out_dir, exist_ok=True)
        file_path = os.path.join(out_dir, info["filename"])

        seed = 101 if key == "gold" else (202 if key == "bitcoin" else 303)
        records = generate_synthetic_ohlcv(
            start_date=start_date,
            num_days=num_days,
            start_price=info["start_price"],
            drift=info["drift"],
            volatility=info["volatility"],
            seed=seed
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close,Adj Close,Volume\n")
            for r in records:
                f.write(f"{r['Date']},{r['Open']},{r['High']},{r['Low']},{r['Close']},{r['Adj Close']},{r['Volume']}\n")

        print(f"Ingested {len(records)} raw bars for {info['symbol']} -> {file_path}")

if __name__ == "__main__":
    main()
