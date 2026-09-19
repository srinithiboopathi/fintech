from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class BacktestRequest(BaseModel):
    strategy_id: Optional[str] = "sma_crossover"
    strategy: Optional[str] = None
    symbol: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    initial_capital: float = 100000.0
    position_sizing: str = "percent_equity" # "fixed_amount", "percent_equity", "volatility_parity"
    position_size_value: float = 0.95
    commission_bps: float = 5.0 # 5 basis points
    slippage_pct: float = 0.001 # 0.1%
    start_date: Optional[str] = "2021-01-04"
    end_date: Optional[str] = "2024-09-02"

class EquityPoint(BaseModel):
    date: str
    equity: float
    benchmark_equity: float
    drawdown_pct: float
    cash: float
    holdings_value: float

class TradeRecordDTO(BaseModel):
    trade_id: str
    symbol: str
    side: str # "LONG" or "SHORT"
    action: Optional[str] = "BUY" # "BUY" or "SELL"
    date: Optional[str] = None
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    quantity: float
    price: Optional[float] = 0.0
    portfolio_value: Optional[float] = 0.0
    pnl_usd: float
    pnl_pct: float
    commission: float
    slippage: float
    duration_days: int
    exit_reason: str # "SIGNAL_REVERSAL", "STOP_LOSS", "TAKE_PROFIT"

class BenchmarkMetrics(BaseModel):
    initial_capital: float
    final_value: float
    total_return_pct: float
    cagr: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown_pct: float

class StrategyMetrics(BaseModel):
    initial_capital: float
    final_value: float
    total_return_pct: float
    cagr: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int

class BacktestResult(BaseModel):
    run_id: str
    strategy_id: str
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_equity: float
    total_return_pct: float
    benchmark_return_pct: float
    cagr: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_pnl_pct: float
    max_win_pct: float
    max_loss_pct: float
    equity_curve: List[EquityPoint]
    trades: List[TradeRecordDTO]
    parameters: Dict[str, Any]
    benchmark_comparison: Optional[Dict[str, Any]] = None
