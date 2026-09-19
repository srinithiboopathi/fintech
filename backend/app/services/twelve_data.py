from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx

from app.config import settings, resolve_asset_config, SUPPORTED_ASSETS
from app.models.schemas import (
    HistoricalPoint,
    HistoricalDataResponse,
    LatestMarketDataResponse,
)
from app.utils.exceptions import (
    TwelveDataAuthError,
    TwelveDataRateLimitError,
    TwelveDataDataNotFoundError,
    TwelveDataNetworkError,
    TwelveDataProviderError,
    AlphaVantageMalformedResponseError,
    UnsupportedAssetError,
)
from app.utils.logging import logger

def parse_twelve_data_timestamp_to_utc_iso(ts_str: str) -> str:
    """
    Parses Twelve Data datetime format (e.g. '2026-09-18' or '2026-09-19 11:30:00')
    into UTC ISO-8601 string.
    """
    cleaned = ts_str.strip()
    if not cleaned:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if cleaned.endswith("Z"):
        return cleaned

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return cleaned

class TwelveDataService:
    """
    High-performance market data ingestion client for Twelve Data.
    Provides standardized OHLCV normalization for Equities (NVDA),
    Cryptocurrencies (BTC/USD), and Commodities/Spot FX (XAU/USD).
    """
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    def _get_api_key(self) -> str:
        """Validates and retrieves the Twelve Data API key from environment."""
        if not settings.is_twelve_data_configured:
            raise TwelveDataAuthError(
                message="TWELVE_DATA_API_KEY is not configured in backend/.env. "
                        "Please verify your Twelve Data API key is present in backend/.env."
            )
        return settings.TWELVE_DATA_API_KEY.strip()

    def _check_provider_payload_errors(self, payload: Dict[str, Any], context: str = "") -> None:
        """
        Inspects Twelve Data JSON responses for errors or rate limits.
        Twelve Data returns { 'status': 'error', 'code': ..., 'message': ... } on errors.
        """
        if not isinstance(payload, dict):
            raise AlphaVantageMalformedResponseError(
                message=f"Expected JSON object from Twelve Data, got {type(payload).__name__}",
                details={"context": context}
            )

        status = payload.get("status")
        code = payload.get("code")
        msg = payload.get("message", "")

        if status == "error" or code is not None and int(code) >= 400:
            msg_lower = str(msg).lower()
            code_int = int(code) if code is not None else 500

            # Rate Limit Detection
            if code_int == 429 or "rate limit" in msg_lower or "minute" in msg_lower or "credits" in msg_lower:
                raise TwelveDataRateLimitError(
                    message=f"Twelve Data rate limit reached (8 credits/min limit): {msg}",
                    details={"code": code_int, "message": msg, "context": context}
                )

            # Authentication / Key issues
            if code_int == 401 or "apikey" in msg_lower or "api key" in msg_lower or "unauthorized" in msg_lower:
                raise TwelveDataAuthError(
                    message=f"Twelve Data authentication rejected: {msg}",
                    details={"code": code_int, "message": msg, "context": context}
                )

            # Data not found / symbol not found
            if code_int == 404 or "not found" in msg_lower:
                raise TwelveDataDataNotFoundError(
                    message=f"Twelve Data: {msg}",
                    details={"code": code_int, "message": msg, "context": context}
                )

            # Generic provider error
            raise TwelveDataProviderError(
                message=f"Twelve Data error (code {code_int}): {msg}",
                details={"code": code_int, "message": msg, "context": context}
            )

    async def _fetch_from_provider(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs an asynchronous HTTP GET request to Twelve Data API with redacted logging.
        """
        api_key = self._get_api_key()
        request_params = {**params, "apikey": api_key}
        url = f"{settings.TWELVE_DATA_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

        # Safe redacted logging
        masked_params = {k: ("***REDACTED***" if k == "apikey" else v) for k, v in request_params.items()}
        logger.info(f"Twelve Data Query -> {endpoint} {masked_params}")

        try:
            if self._client:
                response = await self._client.get(url, params=request_params, timeout=15.0)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, params=request_params)
        except httpx.TimeoutException as te:
            logger.error(f"Timeout querying Twelve Data {endpoint}: {te}")
            raise TwelveDataNetworkError(f"Twelve Data query for '{endpoint}' timed out after 15s.")
        except httpx.RequestError as re:
            logger.error(f"Network error querying Twelve Data {endpoint}: {re}")
            raise TwelveDataNetworkError(f"Network error querying Twelve Data: {str(re)}")

        if response.status_code == 429:
            raise TwelveDataRateLimitError(
                message="Twelve Data HTTP 429 Too Many Requests (Rate limit reached).",
                details={"status_code": 429, "endpoint": endpoint}
            )

        if response.status_code != 200:
            raise TwelveDataNetworkError(
                f"Twelve Data returned HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse Twelve Data JSON response: {e}")
            raise AlphaVantageMalformedResponseError("Failed to parse JSON response from Twelve Data.")

        self._check_provider_payload_errors(data, context=endpoint)
        return data

    # ----------------------------------------------------------------------
    # Historical Data Retrieval & Normalization
    # ----------------------------------------------------------------------
    async def get_historical_time_series(
        self,
        asset_config: Dict[str, Any],
        outputsize: int = 20
    ) -> List[HistoricalPoint]:
        """
        Retrieves daily historical OHLCV data from Twelve Data /time_series.
        Returns normalized HistoricalPoint list sorted chronologically (oldest to newest).
        Strictly preserves volume = None for spot crypto/gold where volume is absent.
        """
        twelve_symbol = asset_config.get("twelve_data_symbol", asset_config["symbol"])
        asset_name = asset_config["name"]
        public_symbol = asset_config["symbol"]

        params = {
            "symbol": twelve_symbol,
            "interval": "1day",
            "outputsize": outputsize
        }

        raw_data = await self._fetch_from_provider("time_series", params)

        values = raw_data.get("values")
        if not values or not isinstance(values, list):
            raise TwelveDataDataNotFoundError(
                f"No historical time series values found for {asset_name} ({twelve_symbol})."
            )

        points: List[HistoricalPoint] = []
        for row in values:
            try:
                raw_vol = row.get("volume")
                # Preserve volume as None (null) if missing, None, or empty string. NEVER default to 0.0 for crypto/gold.
                vol: Optional[float] = None
                if raw_vol is not None and str(raw_vol).strip() != "" and str(raw_vol).lower() != "none":
                    try:
                        vol = float(raw_vol)
                    except (ValueError, TypeError):
                        vol = None

                points.append(HistoricalPoint(
                    timestamp=parse_twelve_data_timestamp_to_utc_iso(row.get("datetime", "")),
                    open=float(row.get("open", 0.0)),
                    high=float(row.get("high", 0.0)),
                    low=float(row.get("low", 0.0)),
                    close=float(row.get("close", 0.0)),
                    volume=vol,
                    asset=asset_name,
                    symbol=public_symbol,
                    source="Twelve Data"
                ))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing Twelve Data historical row {row}: {e}")
                continue

        # Sort chronological (oldest to newest)
        points.sort(key=lambda p: p.timestamp)
        return points

    # ----------------------------------------------------------------------
    # Latest Quote Retrieval & Normalization
    # ----------------------------------------------------------------------
    async def get_latest_quote(self, asset_config: Dict[str, Any]) -> LatestMarketDataResponse:
        """
        Retrieves latest available market quote from Twelve Data /quote.
        Correctly formats change percent, previous close, and preserves volume = None if absent.
        """
        twelve_symbol = asset_config.get("twelve_data_symbol", asset_config["symbol"])
        asset_name = asset_config["name"]
        public_symbol = asset_config["symbol"]

        params = {
            "symbol": twelve_symbol
        }

        quote = await self._fetch_from_provider("quote", params)

        raw_price = quote.get("close") or quote.get("price")
        if raw_price is None:
            raise TwelveDataDataNotFoundError(
                f"No current price or close available in Twelve Data quote for {asset_name} ({twelve_symbol})."
            )

        price = float(raw_price)

        # Parse timestamp
        dt_str = quote.get("datetime") or ""
        if not dt_str and quote.get("timestamp"):
            try:
                dt_str = datetime.fromtimestamp(int(quote["timestamp"]), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                dt_str = ""

        # Safe volume parsing: None if not present or null
        raw_vol = quote.get("volume")
        vol: Optional[float] = None
        if raw_vol is not None and str(raw_vol).strip() != "" and str(raw_vol).lower() != "none":
            try:
                vol = float(raw_vol)
            except (ValueError, TypeError):
                vol = None

        # Format percentage change
        raw_pct = quote.get("percent_change")
        change_pct_str: Optional[str] = None
        if raw_pct is not None:
            try:
                change_pct_str = f"{float(raw_pct):+.2f}%"
            except (ValueError, TypeError):
                change_pct_str = str(raw_pct)

        return LatestMarketDataResponse(
            asset=asset_name,
            symbol=public_symbol,
            price=price,
            timestamp=parse_twelve_data_timestamp_to_utc_iso(dt_str),
            source="Twelve Data",
            data_status="latest_available",
            open=float(quote["open"]) if quote.get("open") is not None else None,
            high=float(quote["high"]) if quote.get("high") is not None else None,
            low=float(quote["low"]) if quote.get("low") is not None else None,
            close=price,
            volume=vol,
            previous_close=float(quote["previous_close"]) if quote.get("previous_close") is not None else None,
            change=float(quote["change"]) if quote.get("change") is not None else None,
            change_percent=change_pct_str
        )

twelve_data_service = TwelveDataService()
