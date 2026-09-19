"""
Pydantic Schemas for Market Regime Analysis and Volatility State Classification (Phase 8).
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RegimeDataPoint(BaseModel):
    """Daily record with price, moving average, volatility indicator, and regime labels."""
    date: str = Field(..., description="Observation date (YYYY-MM-DD)", examples=["2024-01-02"])
    asset: str = Field(..., description="Asset identifier", examples=["Gold"])
    close: float = Field(..., description="Closing price", examples=[2063.7])
    trend_value: Optional[float] = Field(None, description="Moving average trend value", examples=[2010.5])
    trend_window: int = Field(50, description="Trend lookback window", examples=[50])
    rolling_volatility: Optional[float] = Field(None, description="Rolling annualized volatility", examples=[0.125])
    volatility_window: int = Field(20, description="Volatility lookback window", examples=[20])
    volatility_threshold: Optional[float] = Field(None, description="Threshold dividing high vs low volatility", examples=[0.142])
    regime: Optional[str] = Field(None, description="Primary trend regime: BULL or BEAR (or null during warmup)", examples=["BULL"])
    volatility_state: Optional[str] = Field(None, description="Secondary volatility state: HIGH_VOLATILITY or LOW_VOLATILITY (or null during warmup)", examples=["LOW_VOLATILITY"])


class RegimeMetrics(BaseModel):
    """Descriptive performance metrics for a specific market regime or volatility state."""
    observation_count: int = Field(..., description="Number of trading days in this regime", examples=[1250])
    percentage: float = Field(..., description="Percentage of classified days spent in this state", examples=[0.542])
    start_date: Optional[str] = Field(None, description="First date observed in this regime", examples=["2010-01-04"])
    end_date: Optional[str] = Field(None, description="Last date observed in this regime", examples=["2025-12-31"])
    average_daily_return: Optional[float] = Field(None, description="Mean arithmetic daily return", examples=[0.00045])
    cumulative_return: Optional[float] = Field(None, description="Compounded cumulative return on regime days", examples=[1.245])
    annualized_volatility: Optional[float] = Field(None, description="Annualized volatility of returns", examples=[0.142])
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio (assuming 0 risk-free rate)", examples=[0.78])
    maximum_drawdown: Optional[float] = Field(None, description="Maximum drawdown during regime periods", examples=[-0.185])


class TransitionEvent(BaseModel):
    """State transition occurrence in primary regime or volatility state."""
    date: str = Field(..., description="Date on which the regime changed", examples=["2024-03-15"])
    transition_type: str = Field(..., description="Type of transition ('regime' or 'volatility')", examples=["regime"])
    from_state: str = Field(..., description="Previous state", examples=["BEAR"])
    to_state: str = Field(..., description="New state entered", examples=["BULL"])


class RegimeSummaryStatistics(BaseModel):
    """Aggregate descriptive metrics across all regimes and volatility states."""
    bull: RegimeMetrics = Field(..., description="Descriptive statistics for BULL regime")
    bear: RegimeMetrics = Field(..., description="Descriptive statistics for BEAR regime")
    high_volatility: RegimeMetrics = Field(..., description="Descriptive statistics for HIGH_VOLATILITY state")
    low_volatility: RegimeMetrics = Field(..., description="Descriptive statistics for LOW_VOLATILITY state")
    total_observations: int = Field(..., description="Total raw daily observations in filtered series", examples=[6358])
    classified_trend_observations: int = Field(..., description="Total observations with valid trend classification", examples=[6309])
    classified_volatility_observations: int = Field(..., description="Total observations with valid volatility state", examples=[6339])


class RegimeResponse(BaseModel):
    """Response payload containing daily regime classifications, summary statistics, and transitions."""
    asset: str = Field(..., description="Asset analyzed", examples=["Gold"])
    trend_window: int = Field(..., description="Trend SMA lookback period", examples=[50])
    volatility_window: int = Field(..., description="Volatility rolling lookback period", examples=[20])
    threshold_mode: str = Field(..., description="Volatility thresholding mode applied", examples=["historical_descriptive"])
    start_date: Optional[str] = Field(None, description="Output start date filter applied")
    end_date: Optional[str] = Field(None, description="Output end date filter applied")
    summary_statistics: RegimeSummaryStatistics = Field(..., description="Descriptive summary metrics")
    transitions: List[TransitionEvent] = Field(..., description="Chronological regime and volatility state transitions")
    data: List[RegimeDataPoint] = Field(..., description="Daily time series data points")
