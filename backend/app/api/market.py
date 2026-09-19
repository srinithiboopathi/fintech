from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

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
            raise HTTPException(status_code=400, detail="Invalid start date.")
        df = df[df["Date"] >= start_date]

    if end:
        end_date = pd.to_datetime(end, errors="coerce")
        if pd.isna(end_date):
            raise HTTPException(status_code=400, detail="Invalid end date.")
        df = df[df["Date"] <= end_date]

    df = df.tail(limit)

    records = df.astype(object).where(pd.notnull(df), None).to_dict(
        orient="records"
    )

    return {
        "asset": asset.lower(),
        "count": len(records),
        "data": records,
    }