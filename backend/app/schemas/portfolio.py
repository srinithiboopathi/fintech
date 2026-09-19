"""
Portfolio Analytics Schemas for QUANTLAB API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PortfolioAnalysisRequest(BaseModel):
    weights: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping asset names (Gold, Bitcoin, NVIDIA) to allocation weights summing to 1.0 (100%).",
        json_schema_extra={"example": {"Gold": 0.4, "Bitcoin": 0.3, "NVIDIA": 0.3}},
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date for portfolio evaluation window (YYYY-MM-DD).",
        json_schema_extra={"example": "2017-01-01"},
    )
    end_date: Optional[str] = Field(
        None,
        description="End date for portfolio evaluation window (YYYY-MM-DD).",
        json_schema_extra={"example": "2017-12-31"},
    )
    initial_capital: float = Field(
        100000.0,
        gt=0,
        description="Initial investment capital in USD.",
        json_schema_extra={"example": 100000.0},
    )
    risk_free_rate: float = Field(
        0.02,
        ge=0,
        description="Annualized risk-free rate for Sharpe ratio calculation (e.g. 0.02 for 2%).",
        json_schema_extra={"example": 0.02},
    )


class AssetPerformanceContribution(BaseModel):
    asset: str = Field(..., description="Canonical asset name")
    weight: float = Field(..., description="Asset allocation weight in portfolio (0 to 1)")
    total_return: float = Field(..., description="Asset standalone cumulative return over evaluation period")
    weighted_contribution: float = Field(..., description="Weight * standalone return contribution to total return")
    contribution_percentage: Optional[float] = Field(None, description="Percentage of total weighted portfolio return")


class AssetRiskContribution(BaseModel):
    asset: str = Field(..., description="Canonical asset name")
    weight: float = Field(..., description="Asset allocation weight")
    annualized_volatility: float = Field(..., description="Asset standalone annualized volatility")
    marginal_risk_contribution: float = Field(..., description="Marginal Contribution to Risk (d sigma_p / d w_i)")
    component_risk_contribution: float = Field(..., description="Component Contribution to Risk (w_i * MCR_i, sums to total vol)")
    percentage_risk_contribution: float = Field(..., description="Percentage Contribution to Portfolio Risk (%CR_i, sums to 100%)")


class PortfolioSummaryMetrics(BaseModel):
    initial_capital: float = Field(..., description="Starting investment capital")
    final_value: float = Field(..., description="Ending portfolio value")
    total_return: float = Field(..., description="Cumulative portfolio return")
    annualized_return: float = Field(..., description="Annualized compound return (CAGR)")
    annualized_volatility: float = Field(..., description="Annualized portfolio volatility (252-day factor)")
    sharpe_ratio: float = Field(..., description="Risk-adjusted Sharpe ratio")
    maximum_drawdown: float = Field(..., description="Maximum peak-to-trough drawdown")
    observations: int = Field(..., description="Number of aligned trading days")
    start_date: str = Field(..., description="First aligned evaluation date")
    end_date: str = Field(..., description="Last aligned evaluation date")


class PortfolioDataPoint(BaseModel):
    date: str = Field(..., description="Trading date (YYYY-MM-DD)")
    portfolio_return: float = Field(..., description="Daily portfolio return")
    cumulative_return: float = Field(..., description="Cumulative portfolio return from inception")
    portfolio_value: float = Field(..., description="Portfolio equity value in USD")
    drawdown: float = Field(..., description="Current underwater drawdown from historical peak")


class PortfolioComparisonPoint(BaseModel):
    date: str = Field(..., description="Trading date (YYYY-MM-DD)")
    portfolio: float = Field(..., description="Normalized portfolio growth (Base = 100.0)")
    assets: Dict[str, float] = Field(..., description="Normalized asset growth series (Base = 100.0)")


class PortfolioAnalysisResponse(BaseModel):
    weights: Dict[str, float] = Field(..., description="Normalized active portfolio asset weights")
    summary: PortfolioSummaryMetrics = Field(..., description="Summary quantitative performance metrics")
    performance_contributions: List[AssetPerformanceContribution] = Field(..., description="Return contribution breakdown per asset")
    risk_contributions: List[AssetRiskContribution] = Field(..., description="Euler risk decomposition breakdown per asset")
    covariance_matrix: Dict[str, Dict[str, float]] = Field(..., description="Annualized covariance matrix of active assets")
    data: List[PortfolioDataPoint] = Field(..., description="Chronological daily return, value, and drawdown time series")
    comparison: List[PortfolioComparisonPoint] = Field(..., description="Normalized base-100 performance comparison series")
