"""
Pydantic Schemas for Backtesting and Portfolio Simulation Endpoints (Phase 7).
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Payload to initiate a portfolio backtest simulation."""
    asset: str = Field(..., description="Asset identifier (e.g. Gold, Bitcoin, NVIDIA)", examples=["Gold"])
    strategy: str = Field(..., description="Strategy name: sma_crossover, ema_trend, momentum, mean_reversion", examples=["sma_crossover"])
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)", examples=["2024-01-01"])
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)", examples=["2024-12-31"])
    initial_capital: float = Field(100000.0, gt=0, description="Starting capital in USD", examples=[100000.0])
    position_size: float = Field(1.0, gt=0.0, le=1.0, description="Fraction of available cash to allocate per trade (0.0 < size <= 1.0)", examples=[1.0])
    transaction_cost: float = Field(0.001, ge=0.0, description="Transaction fee on entry/exit (e.g. 0.001 for 0.1%)", examples=[0.001])
    risk_free_rate: float = Field(0.0, ge=0.0, description="Annualized risk-free rate for Sharpe calculation", examples=[0.0])
    strategy_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Strategy-specific parameters", examples=[{"fast_period": 20, "slow_period": 50}])


class BacktestMeta(BaseModel):
    """Metadata regarding the executed backtest run."""
    asset: str = Field(..., description="Asset analyzed", examples=["Gold"])
    start_date: str = Field(..., description="Analysis start date", examples=["2024-01-02"])
    end_date: str = Field(..., description="Analysis end date", examples=["2024-12-31"])
    records: int = Field(..., description="Number of trading sessions simulated", examples=[252])
    initial_capital: float = Field(..., description="Initial cash in USD", examples=[100000.0])
    position_size: float = Field(..., description="Configured position size ratio", examples=[1.0])
    transaction_cost: float = Field(..., description="Configured transaction cost ratio", examples=[0.001])
    risk_free_rate: float = Field(..., description="Configured annual risk-free rate", examples=[0.0])


class StrategyMeta(BaseModel):
    """Strategy identifier and hyperparameters used in the simulation."""
    name: str = Field(..., description="Strategy name", examples=["sma_crossover"])
    parameters: Dict[str, Any] = Field(..., description="Applied hyperparameters", examples=[{"fast_period": 20, "slow_period": 50}])


class BacktestPerformance(BaseModel):
    """Statistical and portfolio performance metrics for the active strategy."""
    initial_capital: float = Field(..., description="Starting portfolio capital in USD", examples=[100000.0])
    final_portfolio_value: float = Field(..., description="Final marked-to-market equity value in USD", examples=[118420.50])
    total_return: float = Field(..., description="Total percentage return over simulation", examples=[0.1842])
    annualized_return: float = Field(..., description="Compound Annual Growth Rate (CAGR)", examples=[0.1842])
    annualized_volatility: float = Field(..., description="Annualized portfolio volatility", examples=[0.1420])
    sharpe_ratio: float = Field(..., description="Annualized Sharpe ratio", examples=[1.297])
    maximum_drawdown: float = Field(..., description="Maximum peak-to-trough equity drawdown", examples=[-0.0654])
    number_of_trades: int = Field(..., description="Total completed round-trip trades", examples=[4])
    winning_trades: int = Field(..., description="Count of profitable trades", examples=[3])
    losing_trades: int = Field(..., description="Count of unprofitable trades", examples=[1])
    win_rate: float = Field(..., description="Ratio of winning trades (0.0 to 1.0)", examples=[0.75])
    gross_profit: float = Field(..., description="Sum of gains on winning trades in USD", examples=[21000.0])
    gross_loss: float = Field(..., description="Sum of losses on losing trades in USD", examples=[2579.50])
    net_profit: float = Field(..., description="Net trading profit after costs in USD", examples=[18420.50])
    average_trade_return: float = Field(..., description="Mean percentage return per trade", examples=[0.0460])


class BenchmarkPerformance(BaseModel):
    """Performance metrics for passive Buy-and-Hold benchmark over identical window."""
    initial_capital: float = Field(..., description="Starting capital in USD", examples=[100000.0])
    final_value: float = Field(..., description="Final Buy-and-Hold equity value in USD", examples=[112350.00])
    total_return: float = Field(..., description="Total Buy-and-Hold return", examples=[0.1235])
    annualized_return: float = Field(..., description="Buy-and-Hold CAGR", examples=[0.1235])
    annualized_volatility: float = Field(..., description="Buy-and-Hold annualized volatility", examples=[0.1780])
    sharpe_ratio: float = Field(..., description="Buy-and-Hold Sharpe ratio", examples=[0.6938])
    maximum_drawdown: float = Field(..., description="Buy-and-Hold maximum drawdown", examples=[-0.1240])


class BacktestComparison(BaseModel):
    """Arithmetic differentials comparing strategy performance against benchmark."""
    return_difference: float = Field(..., description="Strategy return minus Benchmark return", examples=[0.0607])
    annualized_return_difference: float = Field(..., description="Strategy CAGR minus Benchmark CAGR", examples=[0.0607])
    volatility_difference: float = Field(..., description="Strategy Volatility minus Benchmark Volatility", examples=[-0.0360])
    sharpe_difference: float = Field(..., description="Strategy Sharpe minus Benchmark Sharpe", examples=[0.6032])
    mdd_difference: float = Field(..., description="Strategy MDD minus Benchmark MDD", examples=[0.0586])


class EquityCurvePoint(BaseModel):
    """Daily equity valuation observation."""
    date: str = Field(..., description="ISO 8601 date (YYYY-MM-DD)", examples=["2024-01-02"])
    cash: float = Field(..., description="Available cash at end of day", examples=[100000.0])
    position_quantity: float = Field(..., description="Asset units held", examples=[0.0])
    position_value: float = Field(..., description="Mark-to-market value of open position", examples=[0.0])
    portfolio_value: float = Field(..., description="Total portfolio value (cash + position)", examples=[100000.0])
    daily_return: Optional[float] = Field(None, description="Daily percentage change in portfolio value", examples=[0.0])
    cumulative_return: Optional[float] = Field(None, description="Cumulative percentage growth from initial capital", examples=[0.0])
    drawdown: Optional[float] = Field(None, description="Current drawdown percentage from high-water mark", examples=[0.0])


class TradeRecord(BaseModel):
    """Complete record of a realized round-trip trade."""
    trade_id: int = Field(..., description="Unique sequential trade identifier", examples=[1])
    asset: str = Field(..., description="Asset traded", examples=["Gold"])
    strategy: str = Field(..., description="Strategy triggering trade", examples=["sma_crossover"])
    entry_date: str = Field(..., description="Date position was opened", examples=["2024-02-01"])
    exit_date: str = Field(..., description="Date position was closed", examples=["2024-04-15"])
    entry_price: float = Field(..., description="Execution price on entry", examples=[2050.50])
    exit_price: float = Field(..., description="Execution price on exit", examples=[2380.00])
    quantity: float = Field(..., description="Quantity traded", examples=[48.718])
    entry_notional: float = Field(..., description="Total gross value at entry", examples=[99900.10])
    exit_notional: float = Field(..., description="Total gross value at exit", examples=[115948.84])
    entry_cost: float = Field(..., description="Transaction fees paid on entry", examples=[99.90])
    exit_cost: float = Field(..., description="Transaction fees paid on exit", examples=[115.95])
    gross_pnl: float = Field(..., description="Gross profit/loss before fees", examples=[16048.74])
    net_pnl: float = Field(..., description="Net profit/loss after fees", examples=[15832.89])
    return_pct: float = Field(..., description="Net percentage return on trade", examples=[0.1583])
    holding_period_days: int = Field(..., description="Calendar duration in days", examples=[74])


class OpenPosition(BaseModel):
    """Details of an active open position at backtest termination."""
    asset: str = Field(..., description="Asset held", examples=["Gold"])
    quantity: float = Field(..., description="Quantity held", examples=[42.5])
    entry_date: str = Field(..., description="Date position opened", examples=["2024-11-10"])
    entry_price: float = Field(..., description="Entry execution price", examples=[2600.00])
    current_price: float = Field(..., description="Latest marked closing price", examples=[2650.00])
    entry_notional: float = Field(..., description="Original entry value", examples=[110500.0])
    current_notional: float = Field(..., description="Marked-to-market position value", examples=[112625.0])
    unrealized_pnl: float = Field(..., description="Unrealized dollar profit/loss", examples=[2125.0])
    unrealized_return_pct: float = Field(..., description="Unrealized percentage return", examples=[0.0192])


class BacktestResponse(BaseModel):
    """Complete structured response for a portfolio backtest simulation."""
    backtest: BacktestMeta = Field(..., description="Backtest configuration metadata")
    strategy: StrategyMeta = Field(..., description="Strategy configuration")
    performance: BacktestPerformance = Field(..., description="Strategy performance analytics")
    benchmark: BenchmarkPerformance = Field(..., description="Buy-and-Hold benchmark analytics")
    comparison: BacktestComparison = Field(..., description="Strategy vs Benchmark relative metrics")
    equity_curve: List[EquityCurvePoint] = Field(..., description="Daily time series of portfolio valuation")
    trades: List[TradeRecord] = Field(..., description="List of completed round-trip trades")
    open_position: Optional[OpenPosition] = Field(None, description="Open position details if held at end of simulation")


class StrategyInfo(BaseModel):
    """Metadata describing a supported quantitative trading strategy."""
    name: str = Field(..., description="Strategy identifier", examples=["sma_crossover"])
    display_name: str = Field(..., description="Human-readable title", examples=["SMA Crossover"])
    description: str = Field(..., description="Strategy description", examples=["Captures trend transitions via Fast and Slow Moving Average crossings."])
    default_parameters: Dict[str, Any] = Field(..., description="Default hyperparameter dictionary", examples=[{"fast_period": 20, "slow_period": 50}])


class StrategyInfoListResponse(BaseModel):
    """Response payload listing all available strategies."""
    strategies: List[StrategyInfo] = Field(..., description="List of supported strategies")
