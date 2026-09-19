"""
QuantLab - Historical Market Data Ingestion Module

Downloads daily historical OHLCV market data using yfinance for:
- Gold Futures (GC=F)
- Bitcoin USD (BTC-USD)
- NVIDIA Corporation (NVDA)

Saves raw data into respective directories under datasets/raw/ after rigorous validation.
"""

from pathlib import Path
import sys
import pandas as pd
import yfinance as yf

# Configuration for assets to download
ASSET_CONFIG = {
    "Gold Futures": {
        "ticker": "GC=F",
        "output_path": Path("datasets/raw/gold/gold_raw.csv")
    },
    "Bitcoin": {
        "ticker": "BTC-USD",
        "output_path": Path("datasets/raw/bitcoin/bitcoin_raw.csv")
    },
    "NVIDIA": {
        "ticker": "NVDA",
        "output_path": Path("datasets/raw/nvidia/nvidia_raw.csv")
    }
}

REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]


def validate_market_data(df: pd.DataFrame, asset_name: str, ticker: str) -> None:
    """
    Validates downloaded market data against institutional data quality rules:
    - Dataset is not empty
    - Required OHLCV columns exist
    - Date column is valid and parseable
    - Rows are not duplicated on Date
    - Close values are non-null and positive
    """
    if df is None or df.empty or len(df) == 0:
        raise ValueError(f"[{asset_name} ({ticker})] Dataset is empty. No rows downloaded.")

    # 1. Required columns check
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"[{asset_name} ({ticker})] Missing required columns: {missing}")

    # 2. Date validity check
    parsed_dates = pd.to_datetime(df["Date"], errors="coerce")
    if parsed_dates.isna().any():
        num_invalid = parsed_dates.isna().sum()
        raise ValueError(f"[{asset_name} ({ticker})] Found {num_invalid} invalid or unparseable Date values.")

    # 3. Duplicate rows check
    duplicates = df.duplicated(subset=["Date"]).sum()
    if duplicates > 0:
        raise ValueError(f"[{asset_name} ({ticker})] Found {duplicates} duplicate date rows.")

    # 4. Close values validity check
    if df["Close"].isna().any():
        num_nans = df["Close"].isna().sum()
        raise ValueError(f"[{asset_name} ({ticker})] Close price contains {num_nans} NaN values.")

    # Close values must be strictly positive (> 0)
    non_positive = (df["Close"] <= 0).sum()
    if non_positive > 0:
        raise ValueError(f"[{asset_name} ({ticker})] Found {non_positive} non-positive values in Close column.")


def download_asset_data(asset_name: str, ticker: str) -> pd.DataFrame:
    """
    Downloads maximum historical daily OHLCV data using yfinance.
    Normalizes index/columns while strictly preserving original numerical values.
    """
    print(f"--> Initiating download for {asset_name} (Ticker: {ticker}) [period='max', interval='1d']...")

    # Fetch data using yfinance Ticker history to maximize reliability
    t = yf.Ticker(ticker)
    df = t.history(period="max", interval="1d", auto_adjust=False)

    if df is None or df.empty:
        # Fallback to yf.download in case Ticker.history has empty cache
        print(f"    Notice: history() returned empty, attempting yf.download for {ticker}...")
        df = yf.download(ticker, period="max", interval="1d", auto_adjust=False, progress=False)

    if df is None or df.empty:
        raise RuntimeError(f"Failed to retrieve data for {asset_name} ({ticker}) from yfinance.")

    # Handle multi-level columns if returned by yf.download in newer versions
    if isinstance(df.columns, pd.MultiIndex):
        # Extract the metric level (Open, High, Low, Close, Volume, etc.)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    # Normalize Date from index to column
    if "Date" not in df.columns:
        if df.index.name in ["Date", "Datetime"] or isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            if "Datetime" in df.columns and "Date" not in df.columns:
                df.rename(columns={"Datetime": "Date"}, inplace=True)

    # Format Date as clean YYYY-MM-DD string while preserving temporal ordering
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None).dt.strftime("%Y-%m-%d")

    # Drop any non-trading rows where all OHLC values are NaN
    df = df.dropna(subset=["Open", "High", "Low", "Close"], how="all")

    # Sort strictly by date ascending
    df = df.sort_values("Date").reset_index(drop=True)

    return df


def main():
    print("=" * 70)
    print("QuantLab — Real Historical Market Data Downloader")
    print("=" * 70)

    # Ensure running from project root or find root
    root_dir = Path(__file__).resolve().parent.parent
    success_count = 0
    results_summary = []

    for asset_name, config in ASSET_CONFIG.items():
        ticker = config["ticker"]
        out_file = root_dir / config["output_path"]

        try:
            df = download_asset_data(asset_name, ticker)
            validate_market_data(df, asset_name, ticker)

            # Ensure parent directory exists
            out_file.parent.mkdir(parents=True, exist_ok=True)

            # Save strictly preserved data to CSV without artificial modifications
            df.to_csv(out_file, index=False)

            row_count = len(df)
            start_date = df["Date"].iloc[0]
            end_date = df["Date"].iloc[-1]
            print(f"[SUCCESS] {asset_name} ({ticker}): {row_count:,} rows downloaded.")
            print(f"          Date range: {start_date} to {end_date}")
            print(f"          Saved to: {out_file.relative_to(root_dir)}\n")

            results_summary.append({
                "Asset": asset_name,
                "Ticker": ticker,
                "Rows": row_count,
                "Start Date": start_date,
                "End Date": end_date,
                "Path": str(out_file.relative_to(root_dir))
            })
            success_count += 1

        except Exception as e:
            print(f"[ERROR] Failed to download or validate {asset_name} ({ticker}): {e}", file=sys.stderr)
            print(f"        No fake or synthetic data will be generated.\n", file=sys.stderr)

    print("=" * 70)
    print(f"Download Summary: {success_count}/{len(ASSET_CONFIG)} assets downloaded and validated successfully.")
    print("=" * 70)

    if success_count < len(ASSET_CONFIG):
        sys.exit(1)


if __name__ == "__main__":
    main()
