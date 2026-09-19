import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import User, Asset, MarketPrice, StrategyRecord, BacktestRun, BacktestTrade

class UserRepository:
    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, username: str, name: str, email: str, hashed_pw: str, role: str = "Quant Researcher") -> User:
        user = User(
            id=f"u-{uuid.uuid4().hex[:8]}",
            username=username,
            name=name,
            email=email,
            hashed_password=hashed_pw,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

class AssetRepository:
    @staticmethod
    def list_all(db: Session) -> List[Asset]:
        return db.query(Asset).all()

    @staticmethod
    def get_by_symbol(db: Session, symbol: str) -> Optional[Asset]:
        sym_clean = symbol.upper().strip()
        asset = db.query(Asset).filter(Asset.symbol == sym_clean).first()
        if not asset:
            # Fuzzy match
            if "BTC" in sym_clean:
                asset = db.query(Asset).filter(Asset.symbol.like("%BTC%")).first()
            elif "GOLD" in sym_clean or "GC" in sym_clean:
                asset = db.query(Asset).filter(Asset.symbol.like("%GC%")).first()
            elif "NVDA" in sym_clean:
                asset = db.query(Asset).filter(Asset.symbol.like("%NVDA%")).first()
        return asset

    @staticmethod
    def create_or_get(db: Session, symbol: str, name: str, asset_type: str) -> Asset:
        existing = AssetRepository.get_by_symbol(db, symbol)
        if existing:
            return existing
        asset = Asset(
            id=f"asset-{symbol.lower().replace('=', '').replace('-', '')}",
            symbol=symbol.upper(),
            name=name,
            asset_type=asset_type
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

class MarketPriceRepository:
    @staticmethod
    def get_prices_for_asset(
        db: Session,
        asset_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[MarketPrice]:
        query = db.query(MarketPrice).filter(MarketPrice.asset_id == asset_id)
        if start_date:
            query = query.filter(MarketPrice.date >= start_date)
        if end_date:
            query = query.filter(MarketPrice.date <= end_date)
        return query.order_by(MarketPrice.date.asc()).all()

    @staticmethod
    def bulk_insert_prices(db: Session, asset_id: str, bars: List[Dict[str, Any]]) -> int:
        count = 0
        for b in bars:
            d = b["date"]
            exists = db.query(MarketPrice).filter(
                MarketPrice.asset_id == asset_id,
                MarketPrice.date == d
            ).first()
            if not exists:
                price = MarketPrice(
                    asset_id=asset_id,
                    date=d,
                    open=float(b["open"]),
                    high=float(b["high"]),
                    low=float(b["low"]),
                    close=float(b["close"]),
                    volume=float(b.get("volume", 0.0))
                )
                db.add(price)
                count += 1
        db.commit()
        return count

class StrategyRepository:
    @staticmethod
    def list_all(db: Session) -> List[StrategyRecord]:
        return db.query(StrategyRecord).all()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[StrategyRecord]:
        return db.query(StrategyRecord).filter(StrategyRecord.slug == slug).first()

    @staticmethod
    def create_or_get(db: Session, name: str, slug: str, description: str, category: str, default_params: dict) -> StrategyRecord:
        existing = db.query(StrategyRecord).filter(StrategyRecord.slug == slug).first()
        if existing:
            return existing
        strat = StrategyRecord(
            id=f"strat-{slug.replace('_', '-')}",
            name=name,
            slug=slug,
            description=description,
            category=category,
            default_params=default_params
        )
        db.add(strat)
        db.commit()
        db.refresh(strat)
        return strat

class BacktestRepository:
    @staticmethod
    def list_recent(db: Session, limit: int = 20) -> List[BacktestRun]:
        return db.query(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, run_id: str) -> Optional[BacktestRun]:
        return db.query(BacktestRun).filter(BacktestRun.id == run_id).first()

    @staticmethod
    def save_run(db: Session, data: Dict[str, Any], trades: Optional[List[Dict[str, Any]]] = None) -> BacktestRun:
        run_id = data.get("run_id") or data.get("id") or f"run-{uuid.uuid4().hex[:8]}"
        record = BacktestRun(
            id=run_id,
            user_id=data.get("user_id"),
            asset_id=data.get("asset_id"),
            strategy_id=data.get("strategy_id"),
            strategy=data.get("strategy_name") or data.get("strategy", "Custom Strategy"),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            initial_capital=float(data.get("initial_capital", 100000.0)),
            final_value=float(data.get("final_equity", data.get("final_value", 100000.0))),
            total_return=float(data.get("total_return_pct", data.get("total_return", 0.0))),
            sharpe_ratio=float(data.get("sharpe_ratio", 0.0)),
            max_drawdown=float(data.get("max_drawdown_pct", data.get("max_drawdown", 0.0))),
            number_of_trades=int(data.get("total_trades", data.get("number_of_trades", 0))),
            transaction_cost=float(data.get("transaction_cost", 0.0)),
            parameters=data.get("parameters", {}),
            equity_curve=data.get("equity_curve", [])
        )
        db.add(record)

        if trades:
            for t in trades:
                tr_id = t.get("trade_id") or f"tr-{uuid.uuid4().hex[:6]}"
                trade_record = BacktestTrade(
                    id=tr_id,
                    backtest_id=run_id,
                    date=t.get("date") or t.get("exit_date", ""),
                    action=t.get("action") or t.get("side", "BUY"),
                    price=float(t.get("price") or t.get("exit_price", 0.0)),
                    quantity=float(t.get("quantity", 0.0)),
                    portfolio_value=float(t.get("portfolio_value", 0.0))
                )
                db.add(trade_record)

        db.commit()
        db.refresh(record)
        return record
