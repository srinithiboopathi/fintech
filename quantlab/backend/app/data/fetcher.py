from typing import List, Dict, Optional, Any
from app.data.providers.csv_provider import CSVMarketProvider

class MarketDataFetcher:
    def __init__(self, provider=None):
        self.provider = provider or CSVMarketProvider()

    def fetch_ohlcv(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.provider.get_historical_bars(symbol, start_date, end_date)

    def fetch_assets(self) -> List[Dict[str, Any]]:
        return self.provider.get_supported_assets()
