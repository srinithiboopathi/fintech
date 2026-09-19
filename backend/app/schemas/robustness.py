"""
Pydantic Schemas for Strategy Robustness and Sensitivity Analysis (Phase 8).
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RobustnessPeriod(BaseModel):
    """Backtest date range slice for period sensitivity sweeps."""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)", examples=["2022-01-01"])
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)", examples=["2024-12-31"])


class RobustnessRequest(BaseModel):
    """Request payload for running parameter grid sweeps and sensitivity analysis."""
    asset: str = Field(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)", examples=["Gold"])
    strategy: str = Field(..., description="Strategy name: sma_crossover, ema_trend, momentum, mean_reversion", examples=["sma_crossover"])
    start_date: Optional[str] = Field(None, description="Global start date filter (YYYY-MM-DD)", examples=["2020-01-01"])
    end_date: Optional[str] = Field(None, description="Global end date filter (YYYY-MM-DD)", examples=["2025-12-31"])
    periods: Optional[List[RobustnessPeriod]] = Field(None, description="List of explicit backtest date windows to test")
    initial_capital: float = Field(100000.0, gt=0, description="Starting capital in USD", examples=[100000.0])
    position_size: float = Field(1.0, gt=0.0, le=1.0, description="Fraction of available cash deployed per trade", examples=[1.0])
    transaction_costs: Optional[List[float]] = Field(None, description="List of transaction fee percentages to test (e.g. [0.0, 0.001, 0.002])", examples=[[0.0, 0.001, 0.002]])
    risk_free_rate: float = Field(0.0, ge=0.0, description="Annualized risk-free rate", examples=[0.0])
    strategy_parameter_grid: Optional[Dict[str, List[Any]]] = Field(default_factory=dict, description="Hyperparameter lists for grid exploration", examples=[{"fast_period": [10, 20], "slow_period": [40, 50]}])
    max_configurations: Optional[int] = Field(100, gt=0, le=500, description="Maximum allowed configuration combinations limit", examples=[100])


class RobustnessConfigResult(BaseModel):
    """Execution performance outcome for an individual parameter combination."""
    parameters: Dict[str, Any] = Field(..., description="Hyperparameter settings applied")
    transaction_cost: float = Field(..., description="Transaction fee applied", examples=[0.001])
    start_date: str = Field(..., description="Backtest start date", examples=["2020-01-02"])
    end_date: str = Field(..., description="Backtest end date", examples=["2025-12-31"])
    initial_capital: float = Field(..., description="Initial capital in USD", examples=[100000.0])
    final_portfolio_value: float = Field(..., description="Final equity value in USD", examples=[135400.0])
    total_return: float = Field(..., description="Total cumulative return ratio", examples=[0.354])
    annualized_return: float = Field(..., description="CAGR ratio", examples=[0.052])
    annualized_volatility: float = Field(..., description="Annualized portfolio volatility", examples=[0.145])
    sharpe_ratio: float = Field(..., description="Annualized Sharpe ratio", examples=[0.82])
    maximum_drawdown: float = Field(..., description="Maximum peak-to-trough drawdown", examples=[-0.125])
    number_of_trades: int = Field(..., description="Total completed trades", examples=[14])
    win_rate: float = Field(..., description="Win rate ratio (0.0 to 1.0)", examples=[0.6429])


class MetricMinMax(BaseModel):
    min: float = Field(..., description="Minimum observed value", examples=[0.05])
    max: float = Field(..., description="Maximum observed value", examples=[0.42])


class TradesMinMax(BaseModel):
    min: int = Field(..., description="Minimum trade count", examples=[4])
    max: int = Field(..., description="Maximum trade count", examples=[28])


class RobustnessMetricRanges(BaseModel):
    """Descriptive performance ranges observed across all tested combinations."""
    return_range: MetricMinMax = Field(..., description="Range of total return ratios")
    sharpe_range: MetricMinMax = Field(..., description="Range of Sharpe ratios")
    drawdown_range: MetricMinMax = Field(..., description="Range of maximum drawdowns")
    trades_range: TradesMinMax = Field(..., description="Range of completed trade counts")
    win_rate_range: MetricMinMax = Field(..., description="Range of win rates")


class RobustnessSummary(BaseModel):
    """Aggregate sensitivity summary across all tested grid combinations."""
    total_configurations: int = Field(..., description="Total number of backtests executed", examples=[18])
    parameter_ranges: Dict[str, Any] = Field(..., description="Input parameter grid evaluated")
    transaction_costs: List[float] = Field(..., description="Transaction costs tested", examples=[[0.0, 0.001, 0.002]])
    periods_tested: List[Dict[str, Optional[str]]] = Field(..., description="Backtest windows tested")
    metrics_ranges: RobustnessMetricRanges = Field(..., description="Observed descriptive min/max ranges")


class RobustnessResponse(BaseModel):
    """Response payload containing full sensitivity grid results and summary ranges."""
    asset: str = Field(..., description="Asset analyzed", examples=["Gold"])
    strategy: str = Field(..., description="Strategy evaluated", examples=["sma_crossover"])
    summary: RobustnessSummary = Field(..., description="Aggregate sensitivity metrics")
    results: List[RobustnessConfigResult] = Field(..., description="List of all tested configuration outcomes")
