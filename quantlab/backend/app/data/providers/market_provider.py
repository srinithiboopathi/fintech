from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

class BaseMarketProvider(ABC):
    @abstractmethod
    def get_historical_bars(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve cleaned historical OHLCV bars for a given symbol."""
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[Dict[str, Any]]:
        """Retrieve list and metadata for supported assets."""
        pass
