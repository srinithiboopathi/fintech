from typing import Optional, Dict, Any, List

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

# Step 8: Backtesting Exceptions
class InvalidBacktestParameterError(AlphaVantageBaseException):
    """Raised when an invalid backtesting parameter or signal sequence is supplied."""
    def __init__(
        self,
        message: str = "Invalid backtesting parameter: check initial_capital (> 0), transaction_cost_rate (>= 0), allocation_fraction (0 < alloc <= 1), and signal formats.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_BACKTEST_PARAMETER",
            details=details
        )


# Step 9: Trading Strategy Exceptions
class UnsupportedStrategyError(AlphaVantageBaseException):
    """Raised when an unrecognized strategy identifier is requested."""
    def __init__(
        self,
        strategy: str,
        supported_strategies: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        supported = supported_strategies or ["sma_crossover", "ema_trend", "momentum", "mean_reversion"]
        super().__init__(
            message=f"Unsupported strategy '{strategy}'. Supported strategies: {', '.join(supported)}.",
            status_code=400,
            error_type="UNSUPPORTED_STRATEGY",
            details=details or {"strategy": strategy, "supported_strategies": supported}
        )


class InvalidStrategyParameterError(AlphaVantageBaseException):
    """Raised when strategy parameters are invalid, negative, or violate mathematical constraints."""
    def __init__(
        self,
        message: str = "Invalid strategy parameter supplied.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_STRATEGY_PARAMETER",
            details=details
        )


# Step 10: Strategy Comparison & Robustness Analysis Exceptions
class InvalidComparisonRequestError(AlphaVantageBaseException):
    """Raised when strategy comparison configuration or parameters are invalid."""
    def __init__(
        self,
        message: str = "Invalid strategy comparison request.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_COMPARISON_REQUEST",
            details=details
        )


class InvalidRobustnessParameterError(AlphaVantageBaseException):
    """Raised when robustness testing parameter grid is empty, invalid, or exceeds bounded ranges."""
    def __init__(
        self,
        message: str = "Invalid robustness parameter grid supplied.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INVALID_ROBUSTNESS_PARAMETER",
            details=details
        )


class InsufficientHistoricalDataError(AlphaVantageBaseException):
    """Raised when insufficient historical observations exist to run analysis."""
    def __init__(
        self,
        message: str = "Insufficient historical observations available.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_type="INSUFFICIENT_HISTORICAL_DATA",
            details=details
        )




