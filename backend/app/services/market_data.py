import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import httpx

from app.config import settings, resolve_asset_config, SUPPORTED_ASSETS
from app.models.schemas import (
    HistoricalPoint,
    HistoricalDataResponse,
    LatestMarketDataResponse,
    AssetMetadata,
    CleanHistoricalPoint,
    DataQualityReport,
    CleanMarketDataResponse,
    DataSummaryResponse,
    IndicatorsResponse,
    RiskMetricsResponse,
)
from app.services.cache_manager import cache_manager
from app.services.twelve_data import twelve_data_service
from app.services.data_cleaner import data_cleaning_service
from app.services.indicators import indicator_service
from app.services.risk_metrics import risk_metrics_service


from app.utils.exceptions import (
    AlphaVantageAuthError,
    AlphaVantageRateLimitError,
    AlphaVantageDataNotFoundError,
    AlphaVantageNetworkError,
    AlphaVantageMalformedResponseError,
    AlphaVantageProviderError,
    TwelveDataBaseException,
    TwelveDataRateLimitError,
    TwelveDataAuthError,
    TwelveDataDataNotFoundError,
    UnsupportedAssetError,
)
from app.utils.logging import logger

def parse_to_utc_iso(timestamp_str: str, default_tz: str = "UTC") -> str:
    """
    Parses various provider timestamp formats into a clean UTC ISO-8601 string.
    Example: '2026-09-18' -> '2026-09-18T00:00:00Z'
    Example: '2026-09-19 10:38:45' -> '2026-09-19T10:38:45Z'
    """
    ts = timestamp_str.strip()
    if not ts:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
    # Already ends in Z or offset
    if ts.endswith("Z"):
        return ts
        
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    ):
        try:
            dt = datetime.strptime(ts, fmt)
            # Alpha Vantage returns timestamps in UTC for digital currencies & commodities,
            # and US/Eastern for US equities. If it's a date only, default to 00:00:00 UTC.
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue
            
    return ts

class MarketDataService:
    """
    Production-grade market data ingestion service for Alpha Vantage.
    Normalizes Stock, Crypto, and Commodity data into standardized schemas.
    """
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    def _get_api_key(self) -> str:
        """Retrieves and validates that the API key is configured."""
        if not settings.is_api_key_configured:
            raise AlphaVantageAuthError(
                message="ALPHA_VANTAGE_API_KEY is not configured in backend/.env. "
                        "Please place your valid Alpha Vantage API key in backend/.env."
            )
        return settings.ALPHA_VANTAGE_API_KEY.strip()

    def _check_provider_payload_errors(self, payload: Dict[str, Any], context: str = "") -> None:
        """
        Inspects provider JSON for errors, rate limit notes, or informational notices.
        Never allows error messages to silently return as valid data.
        """
        if not isinstance(payload, dict):
            raise AlphaVantageMalformedResponseError(
                message=f"Expected JSON object from provider, got {type(payload).__name__}",
                details={"context": context}
            )

        # 1. Check for Alpha Vantage explicit Error Message
        if "Error Message" in payload:
            err_msg = payload["Error Message"]
            if "apikey" in err_msg.lower():
                raise AlphaVantageAuthError(
                    message=f"Alpha Vantage rejected the API key: {err_msg}",
                    details={"provider_error": err_msg, "context": context}
                )
            raise AlphaVantageProviderError(
                message=f"Alpha Vantage provider error: {err_msg}",
                details={"provider_error": err_msg, "context": context}
            )

        # 2. Check for Information (daily rate limit or demo key notice)
        if "Information" in payload:
            info_msg = payload["Information"]
            info_lower = info_msg.lower()
            if "demo" in info_lower:
                raise AlphaVantageAuthError(
                    message="Using placeholder or 'demo' API key. Please set your real Alpha Vantage API key in backend/.env.",
                    details={"information": info_msg, "context": context}
                )
            if "rate limit" in info_lower or "25 requests" in info_lower:
                raise AlphaVantageRateLimitError(
                    message=f"Alpha Vantage daily rate limit reached: {info_msg}",
                    details={"information": info_msg, "context": context}
                )
            raise AlphaVantageProviderError(
                message=f"Alpha Vantage provider notice: {info_msg}",
                details={"information": info_msg, "context": context}
            )

        # 3. Check for Note (per-minute frequency rate limit)
        if "Note" in payload:
            note_msg = payload["Note"]
            if "call frequency" in note_msg.lower() or "calls per minute" in note_msg.lower():
                raise AlphaVantageRateLimitError(
                    message=f"Alpha Vantage call frequency exceeded (5 calls/min limit): {note_msg}",
                    details={"note": note_msg, "context": context}
                )
            raise AlphaVantageProviderError(
                message=f"Alpha Vantage note: {note_msg}",
                details={"note": note_msg, "context": context}
            )

    async def _fetch_from_provider(self, params: Dict[str, str]) -> Dict[str, Any]:
        """
        Dispatches HTTP GET to Alpha Vantage with redacting exception handling.
        """
        api_key = self._get_api_key()
        request_params = {**params, "apikey": api_key}
        
        # Redacted logging
        masked_params = {k: ("***REDACTED***" if k == "apikey" else v) for k, v in request_params.items()}
        logger.info(f"Alpha Vantage Query -> {masked_params}")

        try:
            if self._client:
                response = await self._client.get(settings.ALPHA_VANTAGE_BASE_URL, params=request_params, timeout=15.0)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(settings.ALPHA_VANTAGE_BASE_URL, params=request_params)
        except httpx.TimeoutException as te:
            logger.error(f"Timeout querying Alpha Vantage: {te}")
            raise AlphaVantageNetworkError("Request to Alpha Vantage timed out after 15 seconds.")
        except httpx.RequestError as re:
            logger.error(f"Network error querying Alpha Vantage: {re}")
            raise AlphaVantageNetworkError(f"Network connectivity error contacting Alpha Vantage: {str(re)}")

        if response.status_code != 200:
            raise AlphaVantageNetworkError(
                f"Alpha Vantage HTTP error {response.status_code}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise AlphaVantageMalformedResponseError("Failed to parse JSON response from Alpha Vantage.")

        self._check_provider_payload_errors(data, context=params.get("function", ""))
        return data

    def list_supported_assets(self) -> List[AssetMetadata]:
        """Returns metadata for all supported assets."""
        results = []
        for asset_id, config in SUPPORTED_ASSETS.items():
            results.append(AssetMetadata(
                asset_id=config["asset_id"],
                name=config["name"],
                symbol=config["symbol"],
                asset_class=config["asset_class"],
                description=config["description"],
                supported_endpoints=[
                    f"/market/{asset_id}/historical",
                    f"/market/{asset_id}/latest"
                ]
            ))
        return results

    # ----------------------------------------------------------------------
    # NVIDIA (Equity) Normalization
    # ----------------------------------------------------------------------
    def _normalize_stock_historical(self, data: Dict[str, Any], asset_name: str, symbol: str) -> List[HistoricalPoint]:
        time_series = data.get("Time Series (Daily)")
        if not time_series:
            raise AlphaVantageDataNotFoundError(
                f"No 'Time Series (Daily)' key found in response for {asset_name} ({symbol})."
            )

        points: List[HistoricalPoint] = []
        for date_str, ohlcv in time_series.items():
            try:
                points.append(HistoricalPoint(
                    timestamp=parse_to_utc_iso(date_str),
                    open=float(ohlcv.get("1. open", 0.0)),
                    high=float(ohlcv.get("2. high", 0.0)),
                    low=float(ohlcv.get("3. low", 0.0)),
                    close=float(ohlcv.get("4. close", 0.0)),
                    volume=float(ohlcv.get("5. volume", 0.0)) if "5. volume" in ohlcv else None,
                    asset=asset_name,
                    symbol=symbol,
                    source="Alpha Vantage"
                ))
            except (ValueError, TypeError) as parse_err:
                logger.warning(f"Error parsing date {date_str} for {symbol}: {parse_err}")
                continue

        # Sort chronological (oldest to newest)
        points.sort(key=lambda p: p.timestamp)
        return points

    def _normalize_stock_latest(self, data: Dict[str, Any], asset_name: str, symbol: str) -> LatestMarketDataResponse:
        quote = data.get("Global Quote")
        if not quote or not quote.get("05. price"):
            raise AlphaVantageDataNotFoundError(f"No 'Global Quote' data available for {asset_name} ({symbol}).")

        price = float(quote.get("05. price", 0.0))
        timestamp_str = quote.get("07. latest trading day", "")
        
        return LatestMarketDataResponse(
            asset=asset_name,
            symbol=symbol,
            price=price,
            timestamp=parse_to_utc_iso(timestamp_str),
            source="Alpha Vantage",
            data_status="latest_available",
            open=float(quote.get("02. open")) if quote.get("02. open") else None,
            high=float(quote.get("03. high")) if quote.get("03. high") else None,
            low=float(quote.get("04. low")) if quote.get("04. low") else None,
            close=price,
            volume=float(quote.get("06. volume")) if quote.get("06. volume") else None,
            previous_close=float(quote.get("08. previous close")) if quote.get("08. previous close") else None,
            change=float(quote.get("09. change")) if quote.get("09. change") else None,
            change_percent=quote.get("10. change percent")
        )

    # ----------------------------------------------------------------------
    # Bitcoin (Crypto) Normalization
    # ----------------------------------------------------------------------
    def _normalize_crypto_historical(self, data: Dict[str, Any], asset_name: str, symbol: str) -> List[HistoricalPoint]:
        time_series = data.get("Time Series (Digital Currency Daily)")
        if not time_series:
            raise AlphaVantageDataNotFoundError(
                f"No 'Time Series (Digital Currency Daily)' key found for {asset_name} ({symbol})."
            )

        points: List[HistoricalPoint] = []
        for date_str, metrics in time_series.items():
            try:
                # Support both "1. open" and older "1a. open (USD)"
                o = metrics.get("1. open") or metrics.get("1a. open (USD)") or 0.0
                h = metrics.get("2. high") or metrics.get("2a. high (USD)") or 0.0
                l = metrics.get("3. low") or metrics.get("3a. low (USD)") or 0.0
                c = metrics.get("4. close") or metrics.get("4a. close (USD)") or 0.0
                v = metrics.get("5. volume") or 0.0

                points.append(HistoricalPoint(
                    timestamp=parse_to_utc_iso(date_str),
                    open=float(o),
                    high=float(h),
                    low=float(l),
                    close=float(c),
                    volume=float(v) if v is not None else None,
                    asset=asset_name,
                    symbol=symbol,
                    source="Alpha Vantage"
                ))
            except (ValueError, TypeError) as parse_err:
                logger.warning(f"Error parsing crypto date {date_str}: {parse_err}")
                continue

        points.sort(key=lambda p: p.timestamp)
        return points

    def _normalize_crypto_latest(self, data: Dict[str, Any], asset_name: str, symbol: str) -> LatestMarketDataResponse:
        rate_obj = data.get("Realtime Currency Exchange Rate")
        if not rate_obj or not rate_obj.get("5. Exchange Rate"):
            raise AlphaVantageDataNotFoundError(
                f"No 'Realtime Currency Exchange Rate' found for {asset_name} ({symbol})."
            )

        price = float(rate_obj.get("5. Exchange Rate", 0.0))
        timestamp_str = rate_obj.get("6. Last Refreshed", "")
        bid = float(rate_obj.get("8. Bid Price")) if rate_obj.get("8. Bid Price") else None
        ask = float(rate_obj.get("9. Ask Price")) if rate_obj.get("9. Ask Price") else None

        return LatestMarketDataResponse(
            asset=asset_name,
            symbol=symbol,
            price=price,
            timestamp=parse_to_utc_iso(timestamp_str),
            source="Alpha Vantage",
            data_status="latest_available",
            open=None,
            high=ask,
            low=bid,
            close=price,
            volume=None
        )

    # ----------------------------------------------------------------------
    # Gold (Commodity / ETF) Normalization
    # ----------------------------------------------------------------------
    def _normalize_gold_history(self, data: Dict[str, Any], asset_name: str, symbol: str) -> List[HistoricalPoint]:
        # Case 1: GOLD_SILVER_HISTORY format: {"data": [{"date": "YYYY-MM-DD", "price": "..."}]}
        if "data" in data and isinstance(data["data"], list):
            points: List[HistoricalPoint] = []
            for item in data["data"]:
                date_str = item.get("date")
                price_val = item.get("price")
                if date_str and price_val and price_val != ".":
                    try:
                        p = float(price_val)
                        points.append(HistoricalPoint(
                            timestamp=parse_to_utc_iso(date_str),
                            open=p,
                            high=p,
                            low=p,
                            close=p,
                            volume=None,
                            asset=asset_name,
                            symbol=symbol,
                            source="Alpha Vantage"
                        ))
                    except (ValueError, TypeError):
                        continue
            points.sort(key=lambda p: p.timestamp)
            return points

        # Case 2: Stock ETF GLD format: "Time Series (Daily)"
        if "Time Series (Daily)" in data:
            return self._normalize_stock_historical(data, asset_name, symbol)

        raise AlphaVantageDataNotFoundError(f"Could not parse Gold historical data payload.")

    def _normalize_gold_latest(self, data: Dict[str, Any], asset_name: str, symbol: str) -> LatestMarketDataResponse:
        # Case 1: GOLD_SILVER_SPOT: {"nominal": "XAUUSD", "timestamp": "...", "price": "..."}
        if "price" in data and ("nominal" in data or "timestamp" in data):
            try:
                price = float(data["price"])
                ts = data.get("timestamp", "")
                return LatestMarketDataResponse(
                    asset=asset_name,
                    symbol=symbol,
                    price=price,
                    timestamp=parse_to_utc_iso(ts),
                    source="Alpha Vantage",
                    data_status="latest_available",
                    close=price
                )
            except (ValueError, TypeError) as e:
                raise AlphaVantageMalformedResponseError(f"Invalid price value in gold spot response: {e}")

        # Case 2: CURRENCY_EXCHANGE_RATE format for XAU/USD
        if "Realtime Currency Exchange Rate" in data:
            return self._normalize_crypto_latest(data, asset_name, symbol)

        # Case 3: Global Quote for GLD
        if "Global Quote" in data:
            return self._normalize_stock_latest(data, asset_name, symbol)

        raise AlphaVantageDataNotFoundError(f"Could not parse Gold latest quote payload.")

    # ----------------------------------------------------------------------
    # Alpha Vantage Fallback Fetchers
    # ----------------------------------------------------------------------
    async def _get_alpha_vantage_historical(self, config: Dict[str, Any], outputsize: str = "compact") -> HistoricalDataResponse:
        asset_id = config["asset_id"]
        asset_name = config["name"]
        symbol = config["symbol"]
        points: List[HistoricalPoint] = []

        if asset_id == "nvidia":
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": config.get("alpha_vantage_symbol", symbol),
                "outputsize": outputsize
            }
            raw_data = await self._fetch_from_provider(params)
            points = self._normalize_stock_historical(raw_data, asset_name, symbol)

        elif asset_id == "bitcoin":
            params = {
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": config.get("alpha_vantage_symbol", "BTC"),
                "market": "USD"
            }
            raw_data = await self._fetch_from_provider(params)
            points = self._normalize_crypto_historical(raw_data, asset_name, symbol)

        elif asset_id == "gold":
            try:
                params = {
                    "function": "GOLD_SILVER_HISTORY",
                    "symbol": "GOLD",
                    "interval": "daily"
                }
                raw_data = await self._fetch_from_provider(params)
                points = self._normalize_gold_history(raw_data, asset_name, symbol)
            except (AlphaVantageProviderError, AlphaVantageDataNotFoundError) as primary_err:
                logger.warning(
                    f"Commodity GOLD_SILVER_HISTORY returned notice ({primary_err}). "
                    f"Falling back to SPDR Gold Shares ETF (GLD) time series."
                )
                etf_symbol = config.get("etf_symbol", "GLD")
                etf_params = {
                    "function": "TIME_SERIES_DAILY",
                    "symbol": etf_symbol,
                    "outputsize": outputsize
                }
                raw_data = await self._fetch_from_provider(etf_params)
                points = self._normalize_stock_historical(raw_data, f"{asset_name} (GLD ETF)", etf_symbol)

        if not points:
            raise AlphaVantageDataNotFoundError(f"No historical data points available for {asset_name} from Alpha Vantage.")

        return HistoricalDataResponse(
            asset=asset_name,
            symbol=symbol,
            source="Alpha Vantage (Fallback)",
            data_status="latest_available",
            count=len(points),
            data=points
        )

    async def _get_alpha_vantage_latest(self, config: Dict[str, Any]) -> LatestMarketDataResponse:
        asset_id = config["asset_id"]
        asset_name = config["name"]
        symbol = config["symbol"]

        if asset_id == "nvidia":
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": config.get("alpha_vantage_symbol", symbol)
            }
            raw_data = await self._fetch_from_provider(params)
            resp = self._normalize_stock_latest(raw_data, asset_name, symbol)
            resp.source = "Alpha Vantage (Fallback)"
            return resp

        elif asset_id == "bitcoin":
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": config.get("alpha_vantage_symbol", "BTC"),
                "to_currency": "USD"
            }
            raw_data = await self._fetch_from_provider(params)
            resp = self._normalize_crypto_latest(raw_data, asset_name, symbol)
            resp.source = "Alpha Vantage (Fallback)"
            return resp

        elif asset_id == "gold":
            try:
                params = {
                    "function": "GOLD_SILVER_SPOT",
                    "symbol": "GOLD"
                }
                raw_data = await self._fetch_from_provider(params)
                resp = self._normalize_gold_latest(raw_data, asset_name, symbol)
                resp.source = "Alpha Vantage (Fallback)"
                return resp
            except (AlphaVantageProviderError, AlphaVantageDataNotFoundError):
                try:
                    fx_params = {
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": "XAU",
                        "to_currency": "USD"
                    }
                    raw_data = await self._fetch_from_provider(fx_params)
                    resp = self._normalize_crypto_latest(raw_data, asset_name, symbol)
                    resp.source = "Alpha Vantage (Fallback)"
                    return resp
                except Exception:
                    etf_symbol = config.get("etf_symbol", "GLD")
                    etf_params = {
                        "function": "GLOBAL_QUOTE",
                        "symbol": etf_symbol
                    }
                    raw_data = await self._fetch_from_provider(etf_params)
                    resp = self._normalize_stock_latest(raw_data, f"{asset_name} (GLD ETF)", etf_symbol)
                    resp.source = "Alpha Vantage (Fallback)"
                    return resp

        raise UnsupportedAssetError(asset_id, list(SUPPORTED_ASSETS.keys()))

    # ----------------------------------------------------------------------
    # Public Ingestion APIs (with Cache & Twelve Data / Alpha Vantage Fallback)
    # ----------------------------------------------------------------------
    async def get_historical_data(
        self,
        asset_identifier: str,
        outputsize: str = "compact",
        refresh: bool = False
    ) -> HistoricalDataResponse:
        """
        Retrieves normalized historical price data for NVIDIA, Bitcoin, or Gold.
        Uses Twelve Data as primary provider, protected by local cache,
        with automated Alpha Vantage fallback and stale cache resilience.
        """
        config = resolve_asset_config(asset_identifier)
        if not config:
            raise UnsupportedAssetError(asset_identifier, list(SUPPORTED_ASSETS.keys()))

        symbol = config["symbol"]
        asset_name = config["name"]

        # 1. Check fresh cache unless refresh requested
        if not refresh:
            cached_payload = cache_manager.get_historical(symbol)
            if cached_payload:
                return HistoricalDataResponse(**cached_payload)

        # 2. Inflight request deduplication lock
        async with cache_manager._get_lock(f"hist_{symbol}"):
            # Re-check cache inside lock in case parallel request populated it
            if not refresh:
                cached_payload = cache_manager.get_historical(symbol)
                if cached_payload:
                    return HistoricalDataResponse(**cached_payload)

            output_count = 30 if outputsize == "compact" else 100

            # 3. Try Primary Provider (Twelve Data)
            if settings.PRIMARY_PROVIDER == "twelve_data" and settings.is_twelve_data_configured:
                try:
                    points = await twelve_data_service.get_historical_time_series(
                        asset_config=config,
                        outputsize=output_count
                    )
                    resp = HistoricalDataResponse(
                        asset=asset_name,
                        symbol=symbol,
                        source="Twelve Data",
                        data_status="latest_available",
                        count=len(points),
                        data=points
                    )
                    cache_manager.save_historical(symbol, resp.model_dump())
                    return resp
                except Exception as td_err:
                    logger.warning(f"Twelve Data historical fetch failed for {symbol}: {td_err}. Attempting fallback.")

            # 4. Fallback Provider (Alpha Vantage)
            if settings.is_alpha_vantage_configured:
                try:
                    logger.info(f"Using Alpha Vantage fallback for historical {symbol}")
                    resp = await self._get_alpha_vantage_historical(config, outputsize=outputsize)
                    cache_manager.save_historical(symbol, resp.model_dump())
                    return resp
                except Exception as av_err:
                    logger.warning(f"Alpha Vantage historical fallback also failed for {symbol}: {av_err}")

            # 5. Stale cache fallback if all live providers fail
            stale_payload = cache_manager.get_stale_historical(symbol)
            if stale_payload:
                logger.warning(f"Returning stale cached historical data for {symbol} due to provider unavailability.")
                return HistoricalDataResponse(**stale_payload)

            # 6. If no cache and all failed, raise error
            raise TwelveDataProviderError(
                message=f"Failed to retrieve historical data for {asset_name} ({symbol}) from primary and fallback providers.",
                details={"symbol": symbol, "primary": settings.PRIMARY_PROVIDER}
            )

    async def get_latest_data(
        self,
        asset_identifier: str,
        refresh: bool = False
    ) -> LatestMarketDataResponse:
        """
        Retrieves normalized latest available market price for NVIDIA, Bitcoin, or Gold.
        Uses Twelve Data as primary provider with caching and Alpha Vantage fallback.
        """
        config = resolve_asset_config(asset_identifier)
        if not config:
            raise UnsupportedAssetError(asset_identifier, list(SUPPORTED_ASSETS.keys()))

        symbol = config["symbol"]
        asset_name = config["name"]

        # 1. Check fresh cache unless refresh requested
        if not refresh:
            cached_payload = cache_manager.get_latest(symbol)
            if cached_payload:
                return LatestMarketDataResponse(**cached_payload)

        # 2. Inflight request deduplication lock
        async with cache_manager._get_lock(f"quote_{symbol}"):
            # Re-check cache inside lock
            if not refresh:
                cached_payload = cache_manager.get_latest(symbol)
                if cached_payload:
                    return LatestMarketDataResponse(**cached_payload)

            # 3. Try Primary Provider (Twelve Data)
            if settings.PRIMARY_PROVIDER == "twelve_data" and settings.is_twelve_data_configured:
                try:
                    resp = await twelve_data_service.get_latest_quote(asset_config=config)
                    cache_manager.save_latest(symbol, resp.model_dump())
                    return resp
                except Exception as td_err:
                    logger.warning(f"Twelve Data quote fetch failed for {symbol}: {td_err}. Attempting fallback.")

            # 4. Fallback Provider (Alpha Vantage)
            if settings.is_alpha_vantage_configured:
                try:
                    logger.info(f"Using Alpha Vantage fallback for quote {symbol}")
                    resp = await self._get_alpha_vantage_latest(config)
                    cache_manager.save_latest(symbol, resp.model_dump())
                    return resp
                except Exception as av_err:
                    logger.warning(f"Alpha Vantage quote fallback also failed for {symbol}: {av_err}")

            # 5. Stale cache fallback if all live providers fail
            stale_payload = cache_manager.get_stale_latest(symbol)
            if stale_payload:
                logger.warning(f"Returning stale cached quote for {symbol} due to provider unavailability.")
                return LatestMarketDataResponse(**stale_payload)

            raise TwelveDataProviderError(
                message=f"Failed to retrieve latest market data for {asset_name} ({symbol}) from primary and fallback providers.",
                details={"symbol": symbol, "primary": settings.PRIMARY_PROVIDER}
            )

    # ----------------------------------------------------------------------
    # Step 3: Clean Historical Data & Summary APIs
    # ----------------------------------------------------------------------
    async def get_clean_data(
        self,
        asset_identifier: str,
        refresh: bool = False
    ) -> CleanMarketDataResponse:
        """
        Retrieves clean, validated, sorted, and quality-inspected historical data.
        Reuses cached raw historical data to eliminate unnecessary API requests.
        """
        config = resolve_asset_config(asset_identifier)
        if not config:
            raise UnsupportedAssetError(asset_identifier, list(SUPPORTED_ASSETS.keys()))

        symbol = config["symbol"]
        asset_name = config["name"]

        # 1. Check clean cache first unless refresh requested
        if not refresh:
            cached_clean = cache_manager.get_clean_historical(symbol)
            if cached_clean:
                return CleanMarketDataResponse(**cached_clean)

        # 2. Acquire inflight lock for clean computation
        async with cache_manager._get_lock(f"clean_{symbol}"):
            if not refresh:
                cached_clean = cache_manager.get_clean_historical(symbol)
                if cached_clean:
                    return CleanMarketDataResponse(**cached_clean)

            # 3. Retrieve raw historical data (from raw cache or live provider)
            raw_response = await self.get_historical_data(asset_identifier=asset_identifier, refresh=refresh)

            # 4. Clean and validate records
            clean_points, quality_report = data_cleaning_service.clean_historical_records(
                raw_records=raw_response.data,
                asset_name=asset_name,
                symbol=symbol,
                source=raw_response.source
            )

            # 5. Assemble response
            clean_response = CleanMarketDataResponse(
                asset=asset_name,
                symbol=symbol,
                source=raw_response.source,
                data_status="clean_verified",
                count=len(clean_points),
                quality_report=quality_report,
                data=clean_points
            )

            # 6. Save clean payload in cache
            cache_manager.save_clean_historical(symbol, clean_response.model_dump())
            return clean_response

    async def get_clean_summary(
        self,
        asset_identifier: str,
        refresh: bool = False
    ) -> DataSummaryResponse:
        """
        Retrieves concise executive summary of clean market data quality,
        dates, missing counts, and latest close.
        """
        clean_data = await self.get_clean_data(asset_identifier=asset_identifier, refresh=refresh)
        return data_cleaning_service.build_summary(
            asset_name=clean_data.asset,
            symbol=clean_data.symbol,
            source=clean_data.source,
            clean_points=clean_data.data,
            report=clean_data.quality_report
        )

    # ----------------------------------------------------------------------
    # Step 4: Quantitative Moving Average Indicators (SMA & EMA)
    # ----------------------------------------------------------------------
    async def get_indicators(
        self,
        asset_identifier: str,
        sma_period: int = 20,
        ema_period: int = 20,
        refresh: bool = False
    ) -> IndicatorsResponse:
        """
        Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA)
        for NVIDIA, Bitcoin, or Gold.
        Operates strictly on the cleaned historical data produced by Step 3.
        Reuses cached clean data to eliminate unnecessary external provider calls.
        """
        config = resolve_asset_config(asset_identifier)
        if not config:
            raise UnsupportedAssetError(asset_identifier, list(SUPPORTED_ASSETS.keys()))

        symbol = config["symbol"]
        asset_name = config["name"]

        # Fetch clean historical market data (cached from Step 3)
        clean_resp = await self.get_clean_data(asset_identifier=asset_identifier, refresh=refresh)

        # Compute SMA and EMA indicators via indicator service
        indicator_points, summary = indicator_service.compute_indicators(
            clean_points=clean_resp.data,
            sma_period=sma_period,
            ema_period=ema_period
        )

        return IndicatorsResponse(
            asset=asset_name,
            symbol=symbol,
            source=clean_resp.source,
            data_status="calculated",
            summary=summary,
            data=indicator_points
        )

    # ----------------------------------------------------------------------
    # Step 5: Quantitative Returns & Volatility Analysis (Risk Metrics)
    # ----------------------------------------------------------------------
    async def get_risk_metrics(
        self,
        asset_identifier: str,
        volatility_period: int = 20,
        refresh: bool = False
    ) -> RiskMetricsResponse:
        """
        Calculates percentage daily returns and rolling sample volatility (ddof=1)
        for NVIDIA, Bitcoin, or Gold.
        Operates strictly on the cleaned historical data produced by Step 3.
        Reuses cached clean data to eliminate unnecessary external provider calls.
        """
        config = resolve_asset_config(asset_identifier)
        if not config:
            raise UnsupportedAssetError(asset_identifier, list(SUPPORTED_ASSETS.keys()))

        symbol = config["symbol"]
        asset_name = config["name"]

        # Fetch clean historical market data (cached from Step 3)
        clean_resp = await self.get_clean_data(asset_identifier=asset_identifier, refresh=refresh)

        # Compute returns and rolling volatility via risk metrics service
        metric_points, summary = risk_metrics_service.compute_risk_metrics(
            clean_points=clean_resp.data,
            volatility_period=volatility_period
        )

        return RiskMetricsResponse(
            asset=asset_name,
            symbol=symbol,
            source=clean_resp.source,
            data_status="calculated",
            summary=summary,
            data=metric_points
        )

market_data_service = MarketDataService()


