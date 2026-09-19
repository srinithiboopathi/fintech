from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Quantitative Researcher")
    tier = Column(String(50), default="Enterprise Institutional")
    created_at = Column(DateTime, default=datetime.utcnow)

    backtests = relationship("BacktestRun", back_populates="user")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(50), primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    asset_type = Column(String(50), nullable=False) # e.g. "Commodity", "Crypto", "Equity"
    created_at = Column(DateTime, default=datetime.utcnow)

    prices = relationship("MarketPrice", back_populates="asset", cascade="all, delete-orphan")
    backtests = relationship("BacktestRun", back_populates="asset")

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(50), ForeignKey("assets.id"), index=True, nullable=False)
    date = Column(String(20), index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    asset = relationship("Asset", back_populates="prices")

    __table_args__ = (
        Index("idx_asset_date", "asset_id", "date", unique=True),
    )

class StrategyRecord(Base):
    __tablename__ = "strategies"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="Trend Following")
    default_params = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("BacktestRun", back_populates="strategy_rel")

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=True)
    asset_id = Column(String(50), ForeignKey("assets.id"), nullable=True, index=True)
    strategy_id = Column(String(50), ForeignKey("strategies.id"), nullable=True)
    strategy = Column(String(100), nullable=False)
    initial_capital = Column(Float, nullable=False, default=100000.0)
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    transaction_cost = Column(Float, nullable=False, default=0.0)
    final_value = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    number_of_trades = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Extended metrics & curves for rich UI
    parameters = Column(JSON, nullable=True)
    equity_curve = Column(JSON, nullable=True)

    user = relationship("User", back_populates="backtests")
    asset = relationship("Asset", back_populates="backtests")
    strategy_rel = relationship("StrategyRecord", back_populates="runs")
    trades = relationship("BacktestTrade", back_populates="backtest", cascade="all, delete-orphan")

# Alias for backward compatibility
BacktestRunRecord = BacktestRun

class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(String(50), primary_key=True, index=True)
    backtest_id = Column(String(50), ForeignKey("backtest_runs.id"), index=True, nullable=False)
    date = Column(String(20), nullable=False)
    action = Column(String(20), nullable=False) # "BUY" or "SELL"
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    portfolio_value = Column(Float, nullable=False)

    backtest = relationship("BacktestRun", back_populates="trades")
