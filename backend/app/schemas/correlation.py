"""
Pydantic Schemas for Cross-Asset Comparison and Correlation Endpoints (Phase 5).
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class PairCorrelationResponse(BaseModel):
    asset_a: str = Field(..., description="First asset identifier", examples=["Gold"])
    asset_b: str = Field(..., description="Second asset identifier", examples=["Bitcoin"])
    correlation: Optional[float] = Field(None, description="Pearson sample correlation coefficient [-1.0, 1.0]", examples=[0.1245])
    observations: int = Field(..., description="Count of overlapping daily return observations", examples=[250])
    start_date: str = Field(..., description="Earliest overlapping date", examples=["2017-01-01"])
    end_date: str = Field(..., description="Latest overlapping date", examples=["2017-12-31"])


class CorrelationMatrixResponse(BaseModel):
    assets: List[str] = Field(..., description="List of analyzed assets in deterministic matrix order", examples=[["Gold", "Bitcoin", "NVIDIA"]])
    matrix: Dict[str, Dict[str, Optional[float]]] = Field(..., description="Symmetric Pearson correlation coefficient matrix")
    observation_counts: Dict[str, Dict[str, int]] = Field(..., description="Matrix of pairwise observation counts")
    start_date: str = Field(..., description="Earliest common analysis date", examples=["2017-01-01"])
    end_date: str = Field(..., description="Latest common analysis date", examples=["2017-12-31"])


class RollingCorrelationPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 observation date (YYYY-MM-DD)", examples=["2017-06-30"])
    correlation: Optional[float] = Field(None, description="Rolling Pearson correlation value [-1.0, 1.0]", examples=[-0.082])


class RollingCorrelationResponse(BaseModel):
    asset_a: str = Field(..., description="First asset identifier", examples=["Gold"])
    asset_b: str = Field(..., description="Second asset identifier", examples=["Bitcoin"])
    window: int = Field(..., description="Lookback window size in days", examples=[30])
    count: int = Field(..., description="Total points in time-series", examples=[250])
    data: List[RollingCorrelationPoint] = Field(..., description="Rolling correlation time-series")


class AssetComparisonMetrics(BaseModel):
    asset: str = Field(..., description="Asset identifier", examples=["NVIDIA"])
    start_date: str = Field(..., description="Start observation date", examples=["2017-01-01"])
    end_date: str = Field(..., description="End observation date", examples=["2017-12-31"])
    records: int = Field(..., description="Count of trading records", examples=[251])
    total_return: Optional[float] = Field(None, description="Compounded cumulative total return over period", examples=[0.812])
    annualized_return: Optional[float] = Field(None, description="Compound annualized growth rate (CAGR)", examples=[0.812])
    annualized_volatility: Optional[float] = Field(None, description="Annualized standard deviation of daily returns", examples=[0.425])
    sharpe_ratio: Optional[float] = Field(None, description="Annualized Sharpe ratio (r_f = 0.0)", examples=[1.91])
    maximum_drawdown: Optional[float] = Field(None, description="Maximum peak-to-trough drawdown", examples=[-0.198])


class AssetComparisonResponse(BaseModel):
    assets: List[AssetComparisonMetrics] = Field(..., description="Comparative performance metrics per asset")
    start_date: str = Field(..., description="Overall start date across comparisons", examples=["2017-01-01"])
    end_date: str = Field(..., description="Overall end date across comparisons", examples=["2017-12-31"])
    aligned_records: Optional[int] = Field(None, description="Number of strictly aligned dates if joint period evaluated", examples=[250])
