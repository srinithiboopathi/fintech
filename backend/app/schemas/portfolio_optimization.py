"""
Pydantic Schemas for Portfolio Optimization & Efficient Frontier API.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PortfolioOptimizationRequest(BaseModel):
    assets: List[str] = Field(
        ...,
        min_length=2,
        description="List of asset names for portfolio optimization (Gold, Bitcoin, NVIDIA). Minimum 2 assets.",
        json_schema_extra={"example": ["Gold", "Bitcoin", "NVIDIA"]},
    )
    start_date: Optional[str] = Field(
        None,
        description="Evaluation start date (YYYY-MM-DD).",
        json_schema_extra={"example": "2017-01-01"},
    )
    end_date: Optional[str] = Field(
        None,
        description="Evaluation end date (YYYY-MM-DD).",
        json_schema_extra={"example": "2017-12-31"},
    )
    risk_free_rate: float = Field(
        0.02,
        ge=0.0,
        description="Annualized risk-free rate for Sharpe ratio calculation (e.g. 0.02 for 2%).",
        json_schema_extra={"example": 0.02},
    )
    min_weight: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum allocation weight constraint per asset (0.0 to 1.0).",
        json_schema_extra={"example": 0.0},
    )
    max_weight: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Maximum allocation weight constraint per asset (0.0 to 1.0).",
        json_schema_extra={"example": 1.0},
    )
    random_portfolios: int = Field(
        5000,
        ge=100,
        le=10000,
        description="Number of feasible random portfolios to generate for visualization (100 to 10,000).",
        json_schema_extra={"example": 5000},
    )
    frontier_points: int = Field(
        50,
        ge=10,
        le=100,
        description="Number of target return points on the Markowitz Efficient Frontier curve (10 to 100).",
        json_schema_extra={"example": 50},
    )
    random_seed: int = Field(
        42,
        description="Deterministic random seed for reproducible random portfolio sampling.",
        json_schema_extra={"example": 42},
    )
    user_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Optional custom portfolio weights provided by user to evaluate against optimal portfolios.",
        json_schema_extra={"example": {"Gold": 0.4, "Bitcoin": 0.3, "NVIDIA": 0.3}},
    )


class OptimalPortfolioPoint(BaseModel):
    portfolio_type: str = Field(..., description="Descriptive identifier of the portfolio strategy.")
    weights: Dict[str, float] = Field(..., description="Normalized asset allocation weights summing to 1.0.")
    expected_return: float = Field(..., description="Annualized expected portfolio return (252-day factor).")
    variance: float = Field(..., description="Annualized portfolio variance.")
    volatility: float = Field(..., description="Annualized portfolio volatility (standard deviation).")
    sharpe_ratio: float = Field(..., description="Risk-adjusted Sharpe ratio relative to risk-free rate.")


class EfficientFrontierPoint(BaseModel):
    target_return: float = Field(..., description="Target annualized expected return swept by solver.")
    expected_return: float = Field(..., description="Achieved annualized expected portfolio return.")
    variance: float = Field(..., description="Annualized portfolio variance.")
    volatility: float = Field(..., description="Annualized portfolio volatility.")
    sharpe_ratio: float = Field(..., description="Risk-adjusted Sharpe ratio.")
    weights: Dict[str, float] = Field(..., description="Optimal allocation weights for this frontier point.")


class RandomPortfolioPoint(BaseModel):
    expected_return: float = Field(..., description="Annualized expected return.")
    volatility: float = Field(..., description="Annualized volatility.")
    sharpe_ratio: float = Field(..., description="Sharpe ratio.")
    weights: Dict[str, float] = Field(..., description="Allocation weights.")


class OptimalPortfoliosContainer(BaseModel):
    max_sharpe: OptimalPortfolioPoint = Field(..., description="Maximum Sharpe ratio optimal portfolio.")
    min_volatility: OptimalPortfolioPoint = Field(..., description="Global Minimum Variance (GMV) portfolio.")
    equal_weight: OptimalPortfolioPoint = Field(..., description="1/N equal weight benchmark portfolio.")
    user_portfolio: Optional[OptimalPortfolioPoint] = Field(None, description="User supplied portfolio if provided.")


class PortfolioComparisonItem(BaseModel):
    name: str = Field(..., description="Portfolio designation.")
    weights: Dict[str, float] = Field(..., description="Allocation weights.")
    expected_return: float = Field(..., description="Annualized expected return.")
    volatility: float = Field(..., description="Annualized volatility.")
    sharpe_ratio: float = Field(..., description="Sharpe ratio.")


class PortfolioOptimizationResponse(BaseModel):
    assets: List[str] = Field(..., description="Canonical asset universe.")
    start_date: str = Field(..., description="First synchronized evaluation date.")
    end_date: str = Field(..., description="Last synchronized evaluation date.")
    observations: int = Field(..., description="Number of aligned overlapping trading days.")
    risk_free_rate: float = Field(..., description="Annualized risk-free rate used.")
    min_weight: float = Field(..., description="Lower allocation bound enforced.")
    max_weight: float = Field(..., description="Upper allocation bound enforced.")
    asset_expected_returns: Dict[str, float] = Field(..., description="Individual asset annualized expected returns.")
    covariance_matrix: Dict[str, Dict[str, float]] = Field(..., description="Annualized covariance matrix.")
    optimal_portfolios: OptimalPortfoliosContainer = Field(..., description="Summary optimal portfolios.")
    efficient_frontier: List[EfficientFrontierPoint] = Field(..., description="Markowitz Efficient Frontier curve points.")
    random_portfolios: List[RandomPortfolioPoint] = Field(..., description="Feasible sampled portfolios for cloud scatter.")
    comparison: List[PortfolioComparisonItem] = Field(..., description="Descriptive unranked comparative summary.")
