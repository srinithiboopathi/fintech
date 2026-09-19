from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.correlation.matrix import compute_cross_asset_correlation_matrix

router = APIRouter(prefix="/market", tags=["Market"])

DATA_ROOT = Path(__file__).resolve().parents[3] / "datasets" / "raw"

ASSETS = {
    "gold": DATA_ROOT / "gold" / "gold_raw.csv",
    "bitcoin": DATA_ROOT / "bitcoin" / "bitcoin_raw.csv",
    "nvidia": DATA_ROOT / "nvidia" / "nvidia_raw.csv",
}


def load_asset(asset: str) -> pd.DataFrame:
    asset = asset.lower()

    if asset not in ASSETS:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown asset: {asset}. Use gold, bitcoin, or nvidia.",
        )

    file_path = ASSETS[asset]

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset not found: {file_path}",
        )

    df = pd.read_csv(file_path)

    if "Date" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail="Dataset does not contain a Date column.",
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")

    return df


@router.get("/health")
def market_health():
    return {"status": "market api is running"}


@router.get("/assets")
def available_assets():
    return {
        "assets": [
            {
                "name": asset,
                "available": path.exists(),
            }
            for asset, path in ASSETS.items()
        ]
    }


@router.get("/overview")
def get_market_overview():
    overview = []

    for asset, file_path in ASSETS.items():
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found: {file_path}",
            )

        df = pd.read_csv(file_path)

        if "Date" not in df.columns or "Close" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=f"{asset} dataset must contain Date and Close columns.",
            )

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

        df = df.dropna(subset=["Date", "Close"])
        df = df.sort_values("Date")
        df = df.drop_duplicates(subset=["Date"], keep="last")

        if df.empty:
            continue

        latest = df.iloc[-1]

        latest_price = float(latest["Close"])

        if len(df) >= 2:
            previous_price = float(df.iloc[-2]["Close"])

            if previous_price != 0:
                daily_change = (
                    (latest_price - previous_price)
                    / previous_price
                )
            else:
                daily_change = 0.0
        else:
            previous_price = latest_price
            daily_change = 0.0

        overview.append(
            {
                "asset": asset.upper(),
                "latest_price": round(latest_price, 4),
                "previous_price": round(previous_price, 4),
                "daily_change": round(float(daily_change), 6),
                "date": str(latest["Date"].date()),
                "data_points": int(len(df)),
            }
        )

    return {
        "assets": overview,
    }


@router.get("/correlation")
def get_correlation():
    prices = {}

    for asset, file_path in ASSETS.items():
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Dataset not found: {file_path}",
            )

        df = pd.read_csv(file_path)

        if "Date" not in df.columns or "Close" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=f"{asset} dataset must contain Date and Close columns.",
            )

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

        df = df.dropna(subset=["Date", "Close"])
        df = df.sort_values("Date")
        df = df.drop_duplicates(subset=["Date"], keep="last")

        prices[asset.upper()] = df.set_index("Date")["Close"]

    correlation = compute_cross_asset_correlation_matrix(
        prices,
        join="inner",
        method="pearson",
        min_periods=2,
    )

    matrix = []

    for asset in correlation.index:
        row = {
            "asset": asset,
        }

        for column in correlation.columns:
            value = correlation.loc[asset, column]

            row[column] = (
                None
                if pd.isna(value)
                else round(float(value), 4)
            )

        matrix.append(row)

    return {
        "assets": list(correlation.columns),
        "matrix": matrix,
    }


@router.get("/{asset}")
def get_market_data(
    asset: str,
    limit: int = Query(default=100, ge=1, le=5000),
    start: str | None = None,
    end: str | None = None,
):
    df = load_asset(asset)

    if start:
        start_date = pd.to_datetime(start, errors="coerce")

        if pd.isna(start_date):
            raise HTTPException(
                status_code=400,
                detail="Invalid start date.",
            )

        df = df[df["Date"] >= start_date]

    if end:
        end_date = pd.to_datetime(end, errors="coerce")

        if pd.isna(end_date):
            raise HTTPException(
                status_code=400,
                detail="Invalid end date.",
            )

        df = df[df["Date"] <= end_date]

    df = df.tail(limit)

    records = df.astype(object).where(
        pd.notnull(df),
        None,
    ).to_dict(orient="records")

    return {
        "asset": asset.lower(),
        "count": len(records),
        "data": records,
    }@router.get("/portfolio")
def get_portfolio_analysis(
    gold: float = Query(default=33.33, ge=0, le=100),
    bitcoin: float = Query(default=33.33, ge=0, le=100),
    nvidia: float = Query(default=33.34, ge=0, le=100),
):
    total = gold + bitcoin + nvidia

    if abs(total - 100.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Portfolio weights must total 100%. Current total: {total:.2f}%",
        )

    return {
        "weights": {
            "GOLD": round(gold, 2),
            "BITCOIN": round(bitcoin, 2),
            "NVIDIA": round(nvidia, 2),
        },
        "total_weight": round(total, 2),
        "message": "Portfolio allocation is valid.",
    }