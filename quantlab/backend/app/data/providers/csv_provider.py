import os
import csv
from typing import List, Dict, Optional, Any
from app.config.settings import settings
from app.data.providers.market_provider import BaseMarketProvider
from app.data.cleaner import DataCleaner

SYMBOL_MAP = {
    "GC=F": "gold_daily.csv",
    "GOLD": "gold_daily.csv",
    "XAU": "gold_daily.csv",
    "BTC-USD": "bitcoin_daily.csv",
    "BTC": "bitcoin_daily.csv",
    "BITCOIN": "bitcoin_daily.csv",
    "NVDA": "nvidia_daily.csv",
    "NVIDIA": "nvidia_daily.csv",
}

ASSET_METADATA = [
    {
        "symbol": "BTC-USD",
        "name": "Bitcoin Core",
        "category": "Digital Asset",
        "current_price": 59150.0,
        "change_24h": -1.82,
        "volatility_30d": 0.54,
        "sharpe_1y": 1.95,
        "regime": "High Volatility",
        "volume_24h": 28500000000,
        "high_52w": 73750.0,
        "low_52w": 26800.0,
        "sparkline": [58200, 60400, 62100, 64250, 61500, 59800, 59150]
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "category": "Equities",
        "current_price": 129.80,
        "change_24h": 2.45,
        "volatility_30d": 0.42,
        "sharpe_1y": 2.34,
        "regime": "Bull Trend",
        "volume_24h": 225000000,
        "high_52w": 140.76,
        "low_52w": 41.20,
        "sparkline": [115.0, 118.2, 121.3, 128.6, 120.5, 126.4, 129.8]
    },
    {
        "symbol": "GC=F",
        "name": "Gold Continuous Futures",
        "category": "Commodities",
        "current_price": 2524.3,
        "change_24h": 0.65,
        "volatility_30d": 0.13,
        "sharpe_1y": 1.28,
        "regime": "Bull Trend",
        "volume_24h": 315000,
        "high_52w": 2530.0,
        "low_52w": 1827.0,
        "sparkline": [2347, 2332, 2410, 2456, 2480, 2502, 2524]
    }
]

class CSVMarketProvider(BaseMarketProvider):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(settings.DATASET_DIR, "processed")

    def get_supported_assets(self) -> List[Dict[str, Any]]:
        return ASSET_METADATA

    def normalize_symbol(self, symbol: str) -> str:
        s = symbol.upper().strip()
        if "BTC" in s:
            return "BTC-USD"
        if "GOLD" in s or "GC" in s or "XAU" in s:
            return "GC=F"
        if "NVDA" in s or "NVIDIA" in s:
            return "NVDA"
        return s

    def get_historical_bars(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        norm_sym = self.normalize_symbol(symbol)
        filename = SYMBOL_MAP.get(norm_sym, "nvidia_daily.csv")

        filepath = os.path.join(self.base_dir, filename)
        if not os.path.exists(filepath):
            # Try alternate path relative to backend
            alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "processed", filename))
            if os.path.exists(alt_path):
                filepath = alt_path

        raw_rows = []
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_rows.append(row)

        cleaned_bars = DataCleaner.clean_raw_records(raw_rows, symbol=norm_sym)

        # Apply date filter
        filtered_bars = []
        for b in cleaned_bars:
            d = b["date"]
            if start_date and d < start_date:
                continue
            if end_date and d > end_date:
                continue
            filtered_bars.append(b)

        return filtered_bars
