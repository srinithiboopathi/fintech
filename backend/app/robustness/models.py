"""
Data Models for Strategy Robustness and Sensitivity Analysis.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class BacktestConfig:
    """Represents an individual backtest parameter configuration."""
    parameters: Dict[str, Any]
    transaction_cost: float
    start_date: Optional[str]
    end_date: Optional[str]
    initial_capital: float = 100000.0
    position_size: float = 1.0
    risk_free_rate: float = 0.0


@dataclass
class RobustnessResult:
    """Performance outcome for an individual parameter configuration."""
    parameters: Dict[str, Any]
    transaction_cost: float
    start_date: str
    end_date: str
    initial_capital: float
    final_portfolio_value: float
    total_return: float
    annualized_return: float
    annualized_volatility: float
    sharpe_ratio: float
    maximum_drawdown: float
    number_of_trades: int
    win_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameters": self.parameters,
            "transaction_cost": self.transaction_cost,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": round(self.initial_capital, 2),
            "final_portfolio_value": round(self.final_portfolio_value, 2),
            "total_return": round(self.total_return, 6),
            "annualized_return": round(self.annualized_return, 6),
            "annualized_volatility": round(self.annualized_volatility, 6),
            "sharpe_ratio": round(self.sharpe_ratio, 6),
            "maximum_drawdown": round(self.maximum_drawdown, 6),
            "number_of_trades": self.number_of_trades,
            "win_rate": round(self.win_rate, 4),
        }
