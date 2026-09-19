from typing import Optional, Dict, Any

class AlphaVantageBaseException(Exception):
    """Base exception for market data ingestion errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "PROVIDER_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}

class AlphaVantageAuthError(AlphaVantageBaseException):
    """Raised when API key is missing or rejected by Alpha Vantage."""
    def __init__(self, message: str = "Invalid or unconfigured Alpha Vantage API key.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_type="AUTHENTICATION_FAILED",
            details=details
        )

class AlphaVantageRateLimitError(AlphaVantageBaseException):
    """Raised when provider standard 25 requests/day or 5 calls/min frequency is exceeded."""
    def __init__(self, message: str = "Alpha Vantage API rate limit exceeded.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_type="RATE_LIMIT_EXCEEDED",
            details=details
        )

class AlphaVantageDataNotFoundError(AlphaVantageBaseException):
    """Raised when data for the requested asset is empty or missing."""
    def __init__(self, message: str = "No market data found for the requested asset.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_type="DATA_NOT_FOUND",
            details=details
        )

class AlphaVantageNetworkError(AlphaVantageBaseException):
    """Raised when network connectivity or DNS resolution fails."""
    def __init__(self, message: str = "Network failure connecting to Alpha Vantage.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_type="NETWORK_FAILURE",
            details=details
        )

class AlphaVantageMalformedResponseError(AlphaVantageBaseException):
    """Raised when provider returns invalid JSON or unparseable format."""
    def __init__(self, message: str = "Malformed response received from market data provider.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,
            error_type="MALFORMED_PROVIDER_RESPONSE",
            details=details
        )

class AlphaVantageProviderError(AlphaVantageBaseException):
    """Raised when provider returns an error payload or unknown error message."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,
            error_type="PROVIDER_ERROR_MESSAGE",
            details=details
        )

class UnsupportedAssetError(AlphaVantageBaseException):
    """Raised when user queries an asset outside the supported scope."""
    def __init__(self, asset_name: str, supported: list[str]):
        super().__init__(
            message=f"Unsupported asset '{asset_name}'. Supported assets are: {', '.join(supported)}.",
            status_code=400,
            error_type="UNSUPPORTED_ASSET",
            details={"requested_asset": asset_name, "supported_assets": supported}
        )

# Twelve Data Provider Exceptions
class TwelveDataBaseException(AlphaVantageBaseException):
    """Base exception for Twelve Data provider errors."""
    pass

class TwelveDataAuthError(TwelveDataBaseException):
    def __init__(self, message: str = "Invalid or unconfigured Twelve Data API key.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, error_type="AUTHENTICATION_FAILED", details=details)

class TwelveDataRateLimitError(TwelveDataBaseException):
    def __init__(self, message: str = "Twelve Data API rate limit exceeded (e.g. 8 credits/min limit).", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=429, error_type="RATE_LIMIT_EXCEEDED", details=details)

class TwelveDataDataNotFoundError(TwelveDataBaseException):
    def __init__(self, message: str = "No market data found on Twelve Data for the requested asset.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, error_type="DATA_NOT_FOUND", details=details)

class TwelveDataNetworkError(TwelveDataBaseException):
    def __init__(self, message: str = "Network failure connecting to Twelve Data.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=503, error_type="NETWORK_FAILURE", details=details)

class TwelveDataProviderError(TwelveDataBaseException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=502, error_type="PROVIDER_ERROR_MESSAGE", details=details)

# Step 4: Quantitative Indicator Exceptions
class InvalidIndicatorPeriodError(AlphaVantageBaseException):
    """Raised when an invalid period is supplied for technical indicators (e.g. <= 0, float, non-digit)."""
    def __init__(
        self,
        message: str = "Indicator periods must be positive integers greater than or equal to 1.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_PERIOD",
            details=details
        )

# Step 5: Risk Metrics Exceptions
class InvalidVolatilityPeriodError(AlphaVantageBaseException):
    """Raised when an invalid volatility period is supplied (e.g. <= 0, float, non-digit)."""
    def __init__(
        self,
        message: str = "Volatility period must be a positive integer greater than or equal to 1.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_PERIOD",
            details=details
        )

# Step 6: Risk Analysis Exceptions
class InvalidRiskAnalysisParameterError(AlphaVantageBaseException):
    """Raised when an invalid risk analysis parameter is supplied (e.g. negative risk_free_rate, non-integer or < 1 annualization_factor)."""
    def __init__(
        self,
        message: str = "Invalid risk analysis parameter: risk_free_rate must be a non-negative number and annualization_factor must be a positive integer greater than or equal to 1.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_PARAMETER",
            details=details
        )

# Step 7: Correlation Exceptions
class InvalidCorrelationWindowError(AlphaVantageBaseException):
    """Raised when an invalid rolling window is supplied for correlation (e.g. < 2, float, non-digit)."""
    def __init__(
        self,
        message: str = "Rolling correlation window must be a positive integer greater than or equal to 2.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_WINDOW",
            details=details
        )



