import json
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from app.config import settings
from app.utils.logging import logger

class CacheManager:
    """
    Thread-safe local disk and in-memory cache manager.
    Protects API rate limits, prevents duplicate in-flight requests,
    and provides resilient offline/stale fallback.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def _safe_filename(self, key: str) -> str:
        return key.replace("/", "_").replace("^", "").replace("=", "_").replace("-", "_").lower()

    def _get_path(self, key_type: str, symbol: str) -> Path:
        safe_sym = self._safe_filename(symbol)
        return self.cache_dir / f"{key_type}_{safe_sym}.json"

    # ----------------------------------------------------------------------
    # Historical Data Cache (24-Hour TTL)
    # ----------------------------------------------------------------------
    def get_historical(self, symbol: str, max_age_hours: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached historical data if fresh.
        Returns payload dict or None.
        """
        max_age = max_age_hours if max_age_hours is not None else settings.HISTORICAL_CACHE_TTL_HOURS
        path = self._get_path("historical", symbol)

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            saved_at = cached.get("_cached_at", 0)
            age_hours = (time.time() - saved_at) / 3600.0

            if age_hours <= max_age:
                logger.info(f"Cache HIT for historical {symbol} (age: {age_hours:.2f}h / max: {max_age}h)")
                return cached.get("payload")
            else:
                logger.info(f"Cache EXPIRED for historical {symbol} (age: {age_hours:.2f}h > {max_age}h)")
                return None
        except Exception as e:
            logger.warning(f"Error reading cache file {path}: {e}")
            return None

    def get_stale_historical(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached historical data regardless of age.
        Used strictly as emergency fallback if the external API is unreachable or rate-limited.
        """
        path = self._get_path("historical", symbol)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            logger.warning(f"Serving STALE fallback cache for historical {symbol}")
            return cached.get("payload")
        except Exception:
            return None

    def save_historical(self, symbol: str, payload: Dict[str, Any]) -> None:
        """Saves historical response payload to local disk."""
        path = self._get_path("historical", symbol)
        try:
            container = {
                "_cached_at": time.time(),
                "symbol": symbol,
                "payload": payload
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(container, f, indent=2)
            logger.info(f"Saved historical cache for {symbol} to {path.name}")
        except Exception as e:
            logger.error(f"Failed to write historical cache for {symbol}: {e}")

    # ----------------------------------------------------------------------
    # Clean Historical Data Cache (24-Hour TTL)
    # ----------------------------------------------------------------------
    def get_clean_historical(self, symbol: str, max_age_hours: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieves cached clean historical data if fresh."""
        max_age = max_age_hours if max_age_hours is not None else settings.HISTORICAL_CACHE_TTL_HOURS
        path = self._get_path("clean", symbol)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            saved_at = cached.get("_cached_at", 0)
            age_hours = (time.time() - saved_at) / 3600.0
            if age_hours <= max_age:
                logger.info(f"Cache HIT for clean historical {symbol} (age: {age_hours:.2f}h)")
                return cached.get("payload")
            return None
        except Exception as e:
            logger.warning(f"Error reading clean cache file {path}: {e}")
            return None

    def save_clean_historical(self, symbol: str, payload: Dict[str, Any]) -> None:
        """Saves clean historical dataset payload to local disk."""
        path = self._get_path("clean", symbol)
        try:
            container = {
                "_cached_at": time.time(),
                "symbol": symbol,
                "payload": payload
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(container, f, indent=2)
            logger.info(f"Saved clean historical cache for {symbol} to {path.name}")
        except Exception as e:
            logger.error(f"Failed to write clean cache for {symbol}: {e}")

    # ----------------------------------------------------------------------
    # Latest Quote Cache (60-Second TTL)
    # ----------------------------------------------------------------------
    def get_latest(self, symbol: str, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieves cached latest quote if within TTL."""
        max_age = max_age_seconds if max_age_seconds is not None else settings.LATEST_CACHE_TTL_SECONDS
        
        # Check memory first
        mem = self._memory_cache.get(f"latest_{symbol}")
        if mem:
            age = time.time() - mem["_cached_at"]
            if age <= max_age:
                logger.info(f"Memory Cache HIT for latest {symbol} (age: {age:.1f}s)")
                return mem["payload"]

        # Check disk
        path = self._get_path("latest", symbol)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)

            saved_at = cached.get("_cached_at", 0)
            age = time.time() - saved_at
            if age <= max_age:
                logger.info(f"Disk Cache HIT for latest {symbol} (age: {age:.1f}s / max: {max_age}s)")
                # Update memory
                self._memory_cache[f"latest_{symbol}"] = cached
                return cached.get("payload")
            return None
        except Exception:
            return None

    def get_stale_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Emergency fallback returning last known price if API fails."""
        mem = self._memory_cache.get(f"latest_{symbol}")
        if mem:
            return mem["payload"]
        path = self._get_path("latest", symbol)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                return cached.get("payload")
            except Exception:
                return None
        return None

    def save_latest(self, symbol: str, payload: Dict[str, Any]) -> None:
        """Saves latest quote payload to memory and disk."""
        container = {
            "_cached_at": time.time(),
            "symbol": symbol,
            "payload": payload
        }
        self._memory_cache[f"latest_{symbol}"] = container
        path = self._get_path("latest", symbol)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(container, f, indent=2)
            logger.info(f"Saved latest quote cache for {symbol}")
        except Exception as e:
            logger.error(f"Failed to write latest quote cache for {symbol}: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns statistics on cached assets."""
        files = list(self.cache_dir.glob("*.json"))
        return {
            "cache_dir": str(self.cache_dir),
            "total_cached_files": len(files),
            "files": [f.name for f in files]
        }

cache_manager = CacheManager()
