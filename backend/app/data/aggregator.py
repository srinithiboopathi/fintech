"""
Data Aggregator Module for QUANTLAB.
Aggregates intraday/minute-level market data into daily OHLCV bars.
"""
from typing import Dict, Any, Tuple
import pandas as pd


class DataAggregator:
    @staticmethod
    def aggregate_bitcoin_minutes_to_daily(df_btc_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Aggregates raw 1-minute Bitcoin records into daily OHLCV observations.
        
        Aggregation Rules:
        - Open: First minute open of the day (chronological)
        - High: Maximum minute high of the day
        - Low: Minimum minute low of the day
        - Close: Last minute close of the day (chronological)
        - Volume: Sum of Volume BTC for the day
        """
        raw_row_count = len(df_btc_raw)
        
        # Make a copy to avoid mutating original
        df = df_btc_raw.copy()
        
        # Parse timestamps into datetime
        if 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'unix' in df.columns:
            df['datetime'] = pd.to_datetime(df['unix'], unit='s')
        else:
            raise ValueError("No recognizable date/time column in Bitcoin raw data")
            
        # Ensure chronological ascending sort
        df = df.sort_values('datetime', ascending=True).reset_index(drop=True)
        
        # Extract calendar date (YYYY-MM-DD)
        df['date_only'] = df['datetime'].dt.strftime('%Y-%m-%d')
        
        # Group by calendar date and compute OHLCV
        # Use Volume BTC as the standard tradable asset unit volume
        volume_col = 'Volume BTC' if 'Volume BTC' in df.columns else 'volume'
        
        grouped = df.groupby('date_only', as_index=False).agg(
            open=('open', 'first'),
            high=('high', 'max'),
            low=('low', 'min'),
            close=('close', 'last'),
            volume=(volume_col, 'sum'),
            minutes_count=('close', 'count')
        )
        
        # Rename date_only to date
        grouped = grouped.rename(columns={'date_only': 'date'})
        grouped['asset'] = 'Bitcoin'
        
        # Reorder columns
        aggregated_df = grouped[['date', 'asset', 'open', 'high', 'low', 'close', 'volume']]
        
        stats = {
            "source_minutes_count": raw_row_count,
            "daily_bars_count": len(aggregated_df),
            "date_range_start": aggregated_df['date'].min(),
            "date_range_end": aggregated_df['date'].max(),
            "avg_minutes_per_day": round(df.groupby('date_only')['close'].count().mean(), 2),
        }
        
        return aggregated_df, stats
