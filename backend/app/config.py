import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Base Directory Resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
DATA_CACHE_DIR = BACKEND_DIR / "data" / "cache"

# Ensure cache directory exists
DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load .env from backend/ or workspace root
env_paths = [
    BACKEND_DIR / ".env",
    ROOT_DIR / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantitative Multi-Asset Financial Intelligence & Backtesting Platform"
    VERSION: str = "1.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Provider Selection
    PRIMARY_PROVIDER: str = "twelve_data"
    FALLBACK_PROVIDER: str = "alpha_vantage"
    
    # Twelve Data Configuration (Primary)
    TWELVE_DATA_API_KEY: str = ""
    TWELVE_DATA_BASE_URL: str = "https://api.twelvedata.com"
    
    # Alpha Vantage Configuration (Fallback)
    ALPHA_VANTAGE_API_KEY: str = ""
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"

    # Cache Settings
    CACHE_DIR: Path = DATA_CACHE_DIR
    HISTORICAL_CACHE_TTL_HOURS: int = 24
    LATEST_CACHE_TTL_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    @property
    def is_twelve_data_configured(self) -> bool:
        key = self.TWELVE_DATA_API_KEY.strip()
        return bool(key and key.lower() not in ("your_twelve_data_api_key_here", "demo", "none", ""))

    @property
    def masked_twelve_data_key(self) -> str:
        key = self.TWELVE_DATA_API_KEY.strip()
        if not self.is_twelve_data_configured:
            return "NOT_CONFIGURED"
        if len(key) <= 6:
            return "******"
        return f"{'*' * (len(key) - 6)}{key[-6:]}"

    @property
    def is_alpha_vantage_configured(self) -> bool:
        key = self.ALPHA_VANTAGE_API_KEY.strip()
        return bool(key and key.lower() not in ("your_alpha_vantage_api_key_here", "demo", "none", ""))

    @property
    def masked_alpha_vantage_key(self) -> str:
        key = self.ALPHA_VANTAGE_API_KEY.strip()
        if not self.is_alpha_vantage_configured:
            return "NOT_CONFIGURED"
        if len(key) <= 4:
            return "****"
        return f"{'*' * (len(key) - 4)}{key[-4:]}"

    # Backwards compatibility
    @property
    def is_api_key_configured(self) -> bool:
        return self.is_twelve_data_configured or self.is_alpha_vantage_configured

    @property
    def masked_api_key(self) -> str:
        return self.masked_twelve_data_key if self.is_twelve_data_configured else self.masked_alpha_vantage_key

    model_config = SettingsConfigDict(
        env_file=[str(p) for p in env_paths if p.exists()] or ".env",
        extra="ignore"
    )

settings = Settings()

# Supported Assets Definition with Twelve Data & Alpha Vantage Symbol Mappings
SUPPORTED_ASSETS: Dict[str, Dict[str, Any]] = {
    "nvidia": {
        "asset_id": "nvidia",
        "name": "NVIDIA",
        "symbol": "NVDA",
        "twelve_data_symbol": "NVDA",
        "alpha_vantage_symbol": "NVDA",
        "asset_class": "equity",
        "description": "NVIDIA Corporation (Equity / Stock)",
        "aliases": ["nvda", "nvidia", "nvidia stock"]
    },
    "bitcoin": {
        "asset_id": "bitcoin",
        "name": "Bitcoin",
        "symbol": "BTC/USD",
        "twelve_data_symbol": "BTC/USD",
        "alpha_vantage_symbol": "BTC",
        "asset_class": "cryptocurrency",
        "description": "Bitcoin USD (Cryptocurrency)",
        "aliases": ["btc", "bitcoin", "btc-usd", "btcusd", "btc/usd"]
    },
    "gold": {
        "asset_id": "gold",
        "name": "Gold",
        "symbol": "XAU/USD",
        "twelve_data_symbol": "XAU/USD",
        "alpha_vantage_symbol": "XAU",
        "etf_symbol": "GLD",
        "asset_class": "commodity",
        "description": "Gold Spot Bullion (XAU/USD) & SPDR Gold Shares (GLD)",
        "aliases": ["gold", "xau", "gld", "gold spot", "xauusd", "xau-usd", "xau/usd"]
    }
}

def resolve_asset_config(asset_identifier: str) -> Optional[Dict[str, Any]]:
    """Resolves an asset identifier or alias to its standardized metadata."""
    cleaned = asset_identifier.strip().lower()
    for asset_id, config in SUPPORTED_ASSETS.items():
        if cleaned == asset_id or cleaned in [a.lower() for a in config["aliases"]]:
            return config
    return None
