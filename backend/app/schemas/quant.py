"""
Pydantic Models and Schemas for Quantitative Analysis Endpoints (Phase 4).
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class IndicatorDataPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 observation date (YYYY-MM-DD)", examples=["2025-12-31"])
    close: float = Field(..., description="Closing price in USD", examples=[134.50])
    sma: Optional[float] = Field(None, description="Simple Moving Average value", examples=[130.25])
    ema: Optional[float] = Field(None, description="Exponential Moving Average value", examples=[132.10])


class IndicatorResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["NVIDIA"])
    frequency: str = Field(default="daily", description="Time-series frequency", examples=["daily"])
    sma_period: int = Field(..., description="Configured SMA period", examples=[20])
    ema_period: int = Field(..., description="Configured EMA period", examples=[20])
    count: int = Field(..., description="Number of returned data points", examples=[250])
    data: List[IndicatorDataPoint] = Field(..., description="Time-series of price and technical indicators")


class ReturnDataPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 observation date (YYYY-MM-DD)", examples=["2025-12-31"])
    close: float = Field(..., description="Closing price in USD", examples=[134.50])
    daily_return: Optional[float] = Field(None, description="Daily arithmetic percentage return", examples=[0.0234])
    cumulative_return: Optional[float] = Field(None, description="Compounded cumulative growth from baseline", examples=[1.452])


class ReturnsResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["Gold"])
    frequency: str = Field(default="daily", description="Time-series frequency", examples=["daily"])
    count: int = Field(..., description="Number of returned data points", examples=[250])
    data: List[ReturnDataPoint] = Field(..., description="Time-series of return observations")


class VolatilityDataPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 observation date (YYYY-MM-DD)", examples=["2025-12-31"])
    rolling_volatility: Optional[float] = Field(None, description="Rolling sample standard deviation (daily)", examples=[0.0185])
    annualized_volatility: Optional[float] = Field(None, description="Rolling annualized volatility", examples=[0.2937])


class VolatilityResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["Bitcoin"])
    window: int = Field(..., description="Lookback window in trading days", examples=[20])
    annualization_factor: int = Field(..., description="Annualization factor used (252 for stocks/gold, 365 for crypto)", examples=[365])
    count: int = Field(..., description="Number of returned observations", examples=[345])
    data: List[VolatilityDataPoint] = Field(..., description="Time-series of volatility measurements")


class RiskMetricsResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["NVIDIA"])
    start_date: str = Field(..., description="Analysis start date", examples=["2020-01-01"])
    end_date: str = Field(..., description="Analysis end date", examples=["2025-12-31"])
    records: int = Field(..., description="Number of observations analyzed", examples=[1508])
    risk_free_rate: float = Field(..., description="Annualized risk-free rate applied", examples=[0.0])
    annualization_factor: int = Field(..., description="Annualization factor (252 or 365)", examples=[252])
    annualized_volatility: Optional[float] = Field(None, description="Annualized historical volatility", examples=[0.4852])
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio", examples=[1.68])
    maximum_drawdown: Optional[float] = Field(None, description="Peak-to-trough Maximum Drawdown percentage", examples=[-0.563])


class RollingPerformancePoint(BaseModel):
    date: str = Field(..., description="ISO 8601 date (YYYY-MM-DD)", examples=["2025-12-31"])
    rolling_return: Optional[float] = Field(None, description="Rolling N-day price return", examples=[0.125])
    rolling_volatility: Optional[float] = Field(None, description="Rolling N-day annualized volatility", examples=[0.32])
    rolling_sharpe: Optional[float] = Field(None, description="Rolling N-day annualized Sharpe ratio", examples=[1.42])
    drawdown: Optional[float] = Field(None, description="Current drawdown from historical peak", examples=[-0.085])


class RollingPerformanceResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["Gold"])
    window: int = Field(..., description="Rolling lookback window in days", examples=[60])
    count: int = Field(..., description="Number of observations", examples=[200])
    data: List[RollingPerformancePoint] = Field(..., description="Rolling performance time-series")


class DailyReturnStats(BaseModel):
    mean: Optional[float] = Field(None, description="Mean daily return", examples=[0.00085])
    std: Optional[float] = Field(None, description="Daily return standard deviation", examples=[0.015])
    min: Optional[float] = Field(None, description="Minimum daily return observed", examples=[-0.187])
    max: Optional[float] = Field(None, description="Maximum daily return observed", examples=[0.243])
    positive_days: int = Field(..., description="Count of positive return days", examples=[3520])
    negative_days: int = Field(..., description="Count of negative return days", examples=[2830])


class AssetQuantSummaryResponse(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["NVIDIA"])
    start_date: str = Field(..., description="Analysis start date", examples=["1999-01-22"])
    end_date: str = Field(..., description="Analysis end date", examples=["2025-12-31"])
    records: int = Field(..., description="Total observation count", examples=[6778])
    latest_close: float = Field(..., description="Most recent closing settlement price in USD", examples=[134.50])
    cumulative_return: Optional[float] = Field(None, description="Total compounded return over period", examples=[425.8])
    annualized_volatility: Optional[float] = Field(None, description="Annualized historical volatility", examples=[0.521])
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio", examples=[0.89])
    maximum_drawdown: Optional[float] = Field(None, description="Maximum peak-to-trough decline", examples=[-0.897])
    return_statistics: DailyReturnStats = Field(..., description="Statistical summary of daily returns")
