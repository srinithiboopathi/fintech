from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class TimeSeriesPoint(BaseModel):
    date: str
    value: Optional[float]

class SMAResponse(BaseModel):
    symbol: str
    indicator: str = "SMA"
    period: int
    series: List[TimeSeriesPoint]

class EMAResponse(BaseModel):
    symbol: str
    indicator: str = "EMA"
    period: int
    series: List[TimeSeriesPoint]

class ReturnPoint(BaseModel):
    date: str
    daily_return: float
    cumulative_return: float

class ReturnsResponse(BaseModel):
    symbol: str
    total_cumulative_return: float
    cagr: float
    series: List[ReturnPoint]

class VolatilityPoint(BaseModel):
    date: str
    rolling_volatility: Optional[float]

class VolatilityResponse(BaseModel):
    symbol: str
    annualized_volatility: float
    downside_volatility: float
    window: int = 30
    series: List[VolatilityPoint]

class SharpePoint(BaseModel):
    date: str
    rolling_sharpe: Optional[float]

class SharpeResponse(BaseModel):
    symbol: str
    risk_free_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    window: int = 60
    series: List[SharpePoint]

class DrawdownPoint(BaseModel):
    date: str
    price: float
    peak: float
    drawdown_pct: float

class DrawdownResponse(BaseModel):
    symbol: str
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    series: List[DrawdownPoint]

class IndicatorPoint(BaseModel):
    date: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr: Optional[float] = None

class RiskMetricsSummary(BaseModel):
    symbol: str
    cagr: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int
    var_95: float
    var_99: float
    cvar_95: float
    beta_to_sp500: float
    alpha_annualized: float

class CorrelationMatrixResponse(BaseModel):
    symbols: List[str]
    raw_symbols: List[str]
    matrix: List[List[float]]
    method: str = "pearson"

class RollingCorrelationPoint(BaseModel):
    date: str
    correlation: float

class RollingCorrelationResponse(BaseModel):
    pair: str
    asset_a: str
    asset_b: str
    window: int
    series: List[RollingCorrelationPoint]
