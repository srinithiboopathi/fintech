"""
QuantLab Database Seeder
Initializes the SQLite schema and seeds:
1. Asset records (Gold, Bitcoin, NVIDIA).
2. Historical MarketPrice records from processed CSVs.
3. Preconfigured quantitative strategies.
4. Demo researcher user account.
Avoids duplicate records.
"""

import os
import sys
import csv

# Add backend directory to python path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
PROCESSED_DIR = os.path.join(DATASET_ROOT, "processed")

sys.path.insert(0, BACKEND_DIR)

from app.database.connection import engine, Base, SessionLocal
from app.database.models import User, Asset, MarketPrice, StrategyRecord
from app.database.repositories import AssetRepository, MarketPriceRepository, StrategyRepository

ASSET_DEFINITIONS = [
    {
        "symbol": "GC=F",
        "name": "Gold Continuous Contract",
        "asset_type": "Commodity",
        "csv_file": "gold_daily.csv"
    },
    {
        "symbol": "BTC-USD",
        "name": "Bitcoin USD",
        "asset_type": "Crypto",
        "csv_file": "bitcoin_daily.csv"
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "asset_type": "Equity",
        "csv_file": "nvidia_daily.csv"
    }
]

STRATEGY_DEFINITIONS = [
    {
        "name": "Dual SMA Golden Cross",
        "slug": "sma_crossover",
        "description": "Momentum crossover tracking short-term vs long-term moving averages with stop loss & take profit controls.",
        "category": "Trend Following",
        "default_params": {
            "fast_period": 20,
            "slow_period": 50,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15
        }
    },
    {
        "name": "Triple EMA Trend Ribbon",
        "slug": "ema_trend",
        "description": "Multi-timeframe exponential moving average trend-following model with MACD momentum confirmation.",
        "category": "Trend Following",
        "default_params": {
            "fast_ema": 9,
            "mid_ema": 21,
            "slow_ema": 55,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.12
        }
    },
    {
        "name": "Bollinger Bands Mean Reversion",
        "slug": "mean_reversion",
        "description": "Statistical mean-reversion buying oversold dips at the 2.0σ Lower Bollinger Band and RSI < 35.",
        "category": "Mean Reversion",
        "default_params": {
            "bb_period": 20,
            "bb_std": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 35.0,
            "rsi_overbought": 70.0
        }
    },
    {
        "name": "Momentum Breakout System",
        "slug": "momentum",
        "description": "Donchian 20-day high breakout model coupled with RSI momentum validation.",
        "category": "Breakout",
        "default_params": {
            "lookback": 20,
            "rsi_filter": 50.0
        }
    }
]

def load_csv_bars(csv_path: str):
    bars = []
    if not os.path.exists(csv_path):
        return bars
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                bars.append({
                    "date": row["date"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0.0))
                })
            except (ValueError, KeyError):
                continue
    return bars

def seed():
    print("=== QuantLab Database Seeder ===")
    print("1. Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Demo User
        if not db.query(User).filter(User.username == "quant_trader").first():
            demo_user = User(
                id="u-001",
                username="quant_trader",
                name="Alex Vance",
                email="alex.vance@quantlab.internal",
                hashed_password="hashed_demo_pw",
                role="Lead Quantitative Researcher",
                tier="Enterprise Institutional"
            )
            db.add(demo_user)
            db.commit()
            print("  - Seeded demo researcher user: 'quant_trader'")

        # 2. Seed Strategies
        for strat in STRATEGY_DEFINITIONS:
            StrategyRepository.create_or_get(
                db,
                name=strat["name"],
                slug=strat["slug"],
                description=strat["description"],
                category=strat["category"],
                default_params=strat["default_params"]
            )
        print(f"  - Seeded {len(STRATEGY_DEFINITIONS)} quantitative strategy templates.")

        # 3. Seed Assets and Historical Market Data
        total_prices_seeded = 0
        for asset_def in ASSET_DEFINITIONS:
            asset = AssetRepository.create_or_get(
                db,
                symbol=asset_def["symbol"],
                name=asset_def["name"],
                asset_type=asset_def["asset_type"]
            )
            csv_path = os.path.join(PROCESSED_DIR, asset_def["csv_file"])
            bars = load_csv_bars(csv_path)
            if bars:
                count = MarketPriceRepository.bulk_insert_prices(db, asset.id, bars)
                total_prices_seeded += count
                print(f"  - Asset '{asset.symbol}' ({asset.name}): seeded {count} market price bars (Total in CSV: {len(bars)}).")
            else:
                print(f"  - Asset '{asset.symbol}': no CSV found at {csv_path}.")

        print(f"=== Database Seeding Complete! Seeded {total_prices_seeded} total price records. ===")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
