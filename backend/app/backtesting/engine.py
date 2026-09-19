"""
QuantLab - Core Backtesting Simulation Engine

Runs discrete-event time-series backtests with transaction costs,
mark-to-market accounting, position sizing, and benchmark comparison.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Union
import pandas as pd

from backend.app.strategies.base import BaseStrategy
from backend.app.backtesting.transaction_costs import TransactionCostModel
from backend.app.backtesting.position_sizing import BasePositionSizer, FullCapitalSizer
from backend.app.backtesting.execution import ExecutionHandler, Trade
from backend.app.backtesting.portfolio import PortfolioTracker
from backend.app.quant.drawdown import calculate_max_drawdown


@dataclass
class BenchmarkResult:
    """
    Performance output for Buy & Hold benchmark.
    """
    equity_curve: pd.Series
    final_value: float
    total_return: float
    maximum_drawdown: float


@dataclass
class BacktestResult:
    """
    Comprehensive output payload for strategy backtests.
    """
    strategy_name: str
    equity_curve: pd.Series
    trades: List[Trade]
    final_portfolio_value: float
    total_return: float
    maximum_drawdown: float
    number_of_trades: int
    transaction_costs_paid: float
    portfolio_history: pd.DataFrame
    benchmark: Optional[BenchmarkResult] = None


class BacktestEngine:
    """
    Discrete-event backtest simulation engine.

    Parameters
    ----------
    initial_capital : float, default 100000.0
        Initial portfolio cash.
    transaction_cost : float, default 0.001
        Proportional transaction fee per trade notional (e.g. 0.001 = 10 bps).
    position_sizer : Optional[BasePositionSizer], default None
        Position sizing algorithm. Defaults to FullCapitalSizer(fraction=1.0).
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_cost: float = 0.001,
        position_sizer: Optional[BasePositionSizer] = None
    ):
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, received: {initial_capital}")

        self.initial_capital = float(initial_capital)
        self.cost_model = TransactionCostModel(cost_pct=transaction_cost)
        self.position_sizer = position_sizer or FullCapitalSizer(fraction=1.0)
        self.execution_handler = ExecutionHandler(cost_model=self.cost_model)

    def run(
        self,
        df: pd.DataFrame,
        strategy: BaseStrategy,
        price_col: str = "Close",
        run_benchmark: bool = True
    ) -> BacktestResult:
        """
        Execute full backtest simulation on historical OHLCV data.

        Parameters
        ----------
        df : pd.DataFrame
            Historical market data containing price column.
        strategy : BaseStrategy
            Quantitative strategy instance.
        price_col : str, default 'Close'
            Column name used for trade execution and valuation.
        run_benchmark : bool, default True
            Whether to simulate standard Buy & Hold benchmark alongside strategy.

        Returns
        -------
        BacktestResult
            Backtest performance metrics, equity curves, and trade log.
        """
        if df.empty or len(df) == 0:
            return BacktestResult(
                strategy_name=strategy.name,
                equity_curve=pd.Series(dtype=float),
                trades=[],
                final_portfolio_value=self.initial_capital,
                total_return=0.0,
                maximum_drawdown=0.0,
                number_of_trades=0,
                transaction_costs_paid=0.0,
                portfolio_history=pd.DataFrame(),
                benchmark=None
            )

        if price_col not in df.columns:
            raise ValueError(f"Required price column '{price_col}' not found in DataFrame.")

        # Clean and sort DataFrame
        data = df.copy()
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"])
            data.sort_values("Date", inplace=True)
            dates = data["Date"].dt.strftime("%Y-%m-%d").tolist()
        else:
            dates = [str(idx) for idx in data.index]

        prices = data[price_col].astype(float).values
        signals = strategy.generate_signals(data)

        # Align signals with data length
        if len(signals) != len(data):
            signals = signals.reindex(data.index, fill_value=0)

        signals_array = signals.fillna(0).astype(int).values

        portfolio = PortfolioTracker(initial_capital=self.initial_capital)
        trades: List[Trade] = []
        total_costs_paid = 0.0

        for i in range(len(prices)):
            date = dates[i]
            price = prices[i]
            target_pos = signals_array[i]

            # Determine capital allocation for target position
            target_alloc = self.position_sizer.calculate_allocation(
                current_equity=portfolio.cash + (portfolio.quantity * price),
                available_cash=portfolio.cash,
                signal=target_pos,
                price=price
            )

            # Execute trade if position transitioned
            new_pos, new_qty, new_cash, trade = self.execution_handler.execute(
                date=date,
                current_position=portfolio.position,
                target_position=target_pos,
                current_quantity=portfolio.quantity,
                current_cash=portfolio.cash,
                price=price,
                target_allocation=target_alloc
            )

            portfolio.position = new_pos
            portfolio.quantity = new_qty
            portfolio.cash = new_cash

            if trade is not None:
                trades.append(trade)
                total_costs_paid += trade.transaction_cost

            # Mark to market at bar close
            portfolio.update(date, price)

        history_df = portfolio.to_dataframe()
        equity_curve = history_df["equity"]
        final_value = float(equity_curve.iloc[-1])
        total_return = float((final_value - self.initial_capital) / self.initial_capital)
        max_dd = float(calculate_max_drawdown(equity_curve))

        benchmark_result = None
        if run_benchmark:
            benchmark_result = self.run_buy_and_hold(df, price_col=price_col)

        return BacktestResult(
            strategy_name=strategy.name,
            equity_curve=equity_curve,
            trades=trades,
            final_portfolio_value=final_value,
            total_return=total_return,
            maximum_drawdown=max_dd,
            number_of_trades=len(trades),
            transaction_costs_paid=float(total_costs_paid),
            portfolio_history=history_df,
            benchmark=benchmark_result
        )

    def run_buy_and_hold(
        self,
        df: pd.DataFrame,
        price_col: str = "Close"
    ) -> BenchmarkResult:
        """
        Simulate standard Buy & Hold benchmark starting with initial capital on bar 0.
        """
        if df.empty or len(df) == 0:
            return BenchmarkResult(
                equity_curve=pd.Series(dtype=float),
                final_value=self.initial_capital,
                total_return=0.0,
                maximum_drawdown=0.0
            )

        data = df.copy()
        if "Date" in data.columns:
            data["Date"] = pd.to_datetime(data["Date"])
            data.sort_values("Date", inplace=True)
            index = data["Date"]
        else:
            index = pd.to_datetime(data.index)

        prices = data[price_col].astype(float)
        p0 = prices.iloc[0]

        # Allocate capital on day 0 with entry transaction cost
        trade_val = self.initial_capital / (1.0 + self.cost_model.cost_pct)
        shares = trade_val / p0
        cash_left = self.initial_capital - trade_val - (trade_val * self.cost_model.cost_pct)

        benchmark_equity = (shares * prices + cash_left)
        benchmark_equity.index = index

        final_val = float(benchmark_equity.iloc[-1])
        total_ret = float((final_val - self.initial_capital) / self.initial_capital)
        max_dd = float(calculate_max_drawdown(benchmark_equity))

        return BenchmarkResult(
            equity_curve=benchmark_equity,
            final_value=final_val,
            total_return=total_ret,
            maximum_drawdown=max_dd
        )


def run_backtest(
    df: pd.DataFrame,
    strategy: BaseStrategy,
    initial_capital: float = 100000.0,
    transaction_cost: float = 0.001,
    position_sizer: Optional[BasePositionSizer] = None,
    price_col: str = "Close"
) -> BacktestResult:
    """
    Convenience functional interface to execute a backtest.
    """
    engine = BacktestEngine(
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
        position_sizer=position_sizer
    )
    return engine.run(df=df, strategy=strategy, price_col=price_col)
