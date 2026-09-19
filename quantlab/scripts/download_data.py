"""
QuantLab Market Data Downloader Script
Downloads real historical daily market data for Gold (GC=F), Bitcoin (BTC-USD),
and NVIDIA (NVDA) from Yahoo Finance using the yfinance library.
"""

import os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Base directory paths for datasets
DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
RAW_DIR = os.path.join(DATASET_ROOT, "raw")

# Asset configuration mapping tickers to output destinations
ASSETS = {
    "gold": {
        "symbol": "GC=F",
        "subfolder": "gold",
        "filename": "gold_raw.csv",
        "name": "Gold"
    },
    "bitcoin": {
        "symbol": "BTC-USD",
        "subfolder": "bitcoin",
        "filename": "bitcoin_raw.csv",
        "name": "Bitcoin"
    },
    "nvidia": {
        "symbol": "NVDA",
        "subfolder": "nvidia",
        "filename": "nvidia_raw.csv",
        "name": "NVIDIA"
    }
}

START_DATE = "2021-01-01"


def download_and_save_asset_data(symbol: str, output_path: str, start_date: str, end_date: str) -> bool:
    """
    Downloads historical daily market data for a given symbol using yfinance,
    cleans and validates the data, and saves it to a CSV file.

    Required CSV format: Date,Open,High,Low,Close,Adj Close,Volume
    """
    print(f"\nDownloading data for {symbol} ({start_date} to {end_date})...")

    # Download historical daily data from Yahoo Finance via yfinance
    # auto_adjust=False ensures both 'Close' and 'Adj Close' are retrieved
    df = yf.download(
        tickers=symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        progress=False,
        auto_adjust=False
    )

    if df is None or df.empty:
        raise ValueError(f"No data returned for ticker {symbol}.")

    # Handle MultiIndex columns if returned by newer yfinance versions
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure Date is a regular column (reset index if Date is in the DatetimeIndex)
    if "Date" not in df.columns:
        df = df.reset_index()
        # Rename Datetime or index column to Date if needed
        if "Date" not in df.columns:
            if "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "Date"})
            elif "index" in df.columns:
                df = df.rename(columns={"index": "Date"})

    # Convert Date column to standard YYYY-MM-DD string format
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    # If 'Adj Close' column is missing, fallback to 'Close'
    if "Adj Close" not in df.columns and "Close" in df.columns:
        df["Adj Close"] = df["Close"]

    # If 'Volume' column is missing, default to 0
    if "Volume" not in df.columns:
        df["Volume"] = 0

    # Ensure numeric columns are properly converted
    numeric_cols = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove rows with missing OHLC values
    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    if df.empty:
        raise ValueError(f"All downloaded records contained missing OHLC values for {symbol}.")

    # Ensure Volume is formatted as an integer
    df["Volume"] = df["Volume"].fillna(0).astype("int64")

    # Remove duplicate dates (keeping the most recent entry)
    df = df.drop_duplicates(subset=["Date"], keep="last")

    # Sort records chronologically in ascending order
    df = df.sort_values(by="Date", ascending=True)

    # Select and order the exact required columns
    columns_order = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    df = df[columns_order]

    # Create destination output directory automatically if it does not exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write cleaned dataframe to CSV
    df.to_csv(output_path, index=False)

    # Print a clear summary
    num_rows = len(df)
    first_date = df["Date"].iloc[0]
    last_date = df["Date"].iloc[-1]
    print(f"✓ Successfully processed {symbol}:")
    print(f"  - Number of rows: {num_rows}")
    print(f"  - First date:     {first_date}")
    print(f"  - Last date:      {last_date}")
    print(f"  - Output path:    {output_path}")

    return True


def main():
    print("=" * 60)
    print("QuantLab Real Historical Market Data Downloader (yfinance)")
    print("=" * 60)

    # End date: upper bound set to include today's latest available trading session
    end_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    for key, info in ASSETS.items():
        symbol = info["symbol"]
        out_dir = os.path.join(RAW_DIR, info["subfolder"])
        file_path = os.path.join(out_dir, info["filename"])

        try:
            download_and_save_asset_data(
                symbol=symbol,
                output_path=file_path,
                start_date=START_DATE,
                end_date=end_date
            )
        except Exception as e:
            print(f"✗ Failed to download data for {symbol} ({info['name']}): {e}")
            print("  Continuing with remaining assets...\n")

    print("\nData download process completed.")


if __name__ == "__main__":
    main()
