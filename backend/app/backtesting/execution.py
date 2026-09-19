"""
Execution Engine Module for Order Fills, Notional Calculation, and Fee Accounting.
"""
from typing import Tuple
from datetime import datetime

from backend.app.backtesting.enums import PositionStatus
from backend.app.backtesting.models import Position, TradeRecordInternal


def execute_buy(
    available_cash: float,
    open_price: float,
    position_size: float,
    transaction_cost_pct: float,
    entry_date: str,
) -> Tuple[Position, float]:
    """
    Executes a BUY order on market OPEN.

    Calculates:
        Target allocation = available_cash * position_size
        Quantity = target_allocation / (open_price * (1 + transaction_cost_pct))
        Notional = Quantity * open_price
        Cost = Notional * transaction_cost_pct
        Total deducted from cash = Notional + Cost

    Returns:
        (Position, cash_deducted)
    """
    if open_price <= 0 or available_cash <= 0 or position_size <= 0:
        return Position(status=PositionStatus.FLAT), 0.0

    target_cash = available_cash * position_size
    effective_unit_cost = open_price * (1.0 + transaction_cost_pct)
    
    quantity = target_cash / effective_unit_cost
    entry_notional = quantity * open_price
    entry_cost = entry_notional * transaction_cost_pct
    total_spent = entry_notional + entry_cost

    new_position = Position(
        status=PositionStatus.LONG,
        quantity=quantity,
        entry_price=open_price,
        entry_date=entry_date,
        entry_cost=entry_cost,
        entry_notional=entry_notional,
    )
    return new_position, total_spent


def execute_sell(
    position: Position,
    open_price: float,
    transaction_cost_pct: float,
    exit_date: str,
    asset: str,
    strategy: str,
    trade_id: int,
) -> Tuple[TradeRecordInternal, float, Position]:
    """
    Executes a SELL order on market OPEN, closing the open position.

    Calculates:
        Exit Notional = Quantity * open_price
        Exit Cost = Exit Notional * transaction_cost_pct
        Net Cash Received = Exit Notional - Exit Cost
        Gross PnL = Exit Notional - Entry Notional
        Net PnL = Gross PnL - (Entry Cost + Exit Cost)
        Return Pct = Net PnL / (Entry Notional + Entry Cost)

    Returns:
        (TradeRecordInternal, net_cash_received, Position.FLAT)
    """
    exit_notional = position.quantity * open_price
    exit_cost = exit_notional * transaction_cost_pct
    net_cash_received = exit_notional - exit_cost

    gross_pnl = exit_notional - position.entry_notional
    total_fees = position.entry_cost + exit_cost
    net_pnl = gross_pnl - total_fees

    total_invested = position.entry_notional + position.entry_cost
    return_pct = net_pnl / total_invested if total_invested > 0 else 0.0

    # Calculate calendar holding period
    try:
        d_entry = datetime.strptime(position.entry_date, "%Y-%m-%d")
        d_exit = datetime.strptime(exit_date, "%Y-%m-%d")
        holding_days = max(0, (d_exit - d_entry).days)
    except Exception:
        holding_days = 0

    trade = TradeRecordInternal(
        trade_id=trade_id,
        asset=asset,
        strategy=strategy,
        entry_date=position.entry_date,
        exit_date=exit_date,
        entry_price=position.entry_price,
        exit_price=open_price,
        quantity=position.quantity,
        entry_notional=position.entry_notional,
        exit_notional=exit_notional,
        entry_cost=position.entry_cost,
        exit_cost=exit_cost,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        return_pct=return_pct,
        holding_period_days=holding_days,
    )

    flat_position = Position(status=PositionStatus.FLAT)
    return trade, net_cash_received, flat_position
