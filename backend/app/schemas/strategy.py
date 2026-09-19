"""
Pydantic Models and Schemas for Strategy Signal Endpoints (Phase 6).
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.strategies.enums import SignalType


class StrategySignalPoint(BaseModel):
    """Standardized Strategy Signal Record."""
    date: str = Field(..., description="ISO 8601 observation date (YYYY-MM-DD)", examples=["2025-01-10"])
    asset: str = Field(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)", examples=["Gold"])
    close: float = Field(..., description="Closing price in USD", examples=[2650.20])
    strategy: str = Field(..., description="Strategy identifier", examples=["sma_crossover"])
    signal: SignalType = Field(..., description="Standardized trading signal (BUY, HOLD, SELL)", examples=[SignalType.BUY])
    fast_sma: Optional[float] = Field(None, description="Fast SMA value (if applicable)", examples=[2640.50])
    slow_sma: Optional[float] = Field(None, description="Slow SMA value (if applicable)", examples=[2635.10])
    short_ema: Optional[float] = Field(None, description="Short EMA value (if applicable)", examples=[2642.10])
    long_ema: Optional[float] = Field(None, description="Long EMA value (if applicable)", examples=[2630.80])
    momentum: Optional[float] = Field(None, description="Momentum rate-of-change value (if applicable)", examples=[0.045])
    moving_average: Optional[float] = Field(None, description="Central Moving Average baseline (if applicable)", examples=[2600.00])
    deviation: Optional[float] = Field(None, description="Percentage deviation from Moving Average (if applicable)", examples=[-0.025])


class SignalCounts(BaseModel):
    """Aggregate distribution of generated strategy signals."""
    buy: int = Field(..., description="Total BUY signals generated", examples=[14])
    sell: int = Field(..., description="Total SELL signals generated", examples=[13])
    hold: int = Field(..., description="Total HOLD signals generated", examples=[1250])
    total: int = Field(..., description="Total signal observations", examples=[1277])


class StrategyResponse(BaseModel):
    """Response payload for quantitative trading strategy signal queries."""
    asset: str = Field(..., description="Asset identifier", examples=["Gold"])
    strategy: str = Field(..., description="Applied strategy name", examples=["sma_crossover"])
    parameters: Dict[str, Any] = Field(..., description="Configured strategy hyperparameters", examples=[{"fast_period": 20, "slow_period": 50}])
    start_date: Optional[str] = Field(None, description="Start date filter applied (YYYY-MM-DD)", examples=["2020-01-01"])
    end_date: Optional[str] = Field(None, description="End date filter applied (YYYY-MM-DD)", examples=["2025-12-31"])
    count: int = Field(..., description="Number of signal records returned", examples=[1277])
    summary: SignalCounts = Field(..., description="Signal frequency summary breakdown")
    data: List[StrategySignalPoint] = Field(..., description="Time-series list of standardized signal points")
