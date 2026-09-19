"""
Unit and Integration Tests for Data Ingestion, Cleaning, and Normalization Pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from backend.app.data.loader import DataLoader
from backend.app.data.aggregator import DataAggregator
from backend.app.data.cleaner import DataCleaner
from backend.app.data.validator import DataValidator
from backend.app.data.normalizer import DataNormalizer
from backend.app.data.pipeline import run_pipeline


@pytest.fixture
def sample_minute_bitcoin_df():
    """Fixture creating small controlled minute data for 2 days."""
    dates = [
        "2017-01-01 00:01:00",
        "2017-01-01 12:00:00",
        "2017-01-01 23:59:00",
        "2017-01-02 00:01:00",
        "2017-01-02 23:59:00",
    ]
    return pd.DataFrame({
        "unix": [1483228860, 1483272000, 1483315140, 1483315260, 1483401540],
        "date": dates,
        "symbol": ["BTC/USD"] * 5,
        "open": [100.0, 105.0, 110.0, 120.0, 125.0],
        "high": [102.0, 115.0, 112.0, 130.0, 128.0],
        "low": [98.0, 104.0, 108.0, 118.0, 122.0],
        "close": [101.0, 110.0, 111.0, 124.0, 126.0],
        "Volume BTC": [10.0, 20.0, 30.0, 15.0, 25.0],
        "Volume USD": [1000.0, 2200.0, 3300.0, 1800.0, 3100.0]
    })


@pytest.fixture
def sample_daily_raw_df():
    """Fixture creating raw daily data with an envelope inconsistency."""
    return pd.DataFrame({
        "Date": ["2023-01-03 00:00:00-05:00", "2023-01-04 00:00:00-05:00"],
        "Open": [100.0, 105.0],
        "High": [99.0, 110.0],   # Row 0 has High < Open (envelope inconsistency)
        "Low": [95.0, 108.0],    # Row 1 has Low > Open (envelope inconsistency)
        "Close": [98.0, 109.0],
        "Volume": [1000, 1500],
        "ticker": ["TEST", "TEST"],
        "name": ["Test Asset", "Test Asset"]
    })


class TestDataLoader:
    def test_raw_files_exist(self):
        loader = DataLoader()
        paths = loader.get_raw_file_paths()
        assert paths["Gold"].exists(), f"Missing Gold raw file at {paths['Gold']}"
        assert paths["Bitcoin"].exists(), f"Missing Bitcoin raw file at {paths['Bitcoin']}"
        assert paths["NVIDIA"].exists(), f"Missing NVIDIA raw file at {paths['NVIDIA']}"

    def test_inspect_file_structure(self):
        loader = DataLoader()
        paths = loader.get_raw_file_paths()
        gold_info = loader.inspect_file(paths["Gold"])
        assert gold_info["row_count"] == 6358
        assert "Date" in gold_info["columns"]
        assert "Close" in gold_info["columns"]
        assert gold_info["file_size_bytes"] > 0


class TestDataAggregator:
    def test_bitcoin_minute_aggregation(self, sample_minute_bitcoin_df):
        agg_df, stats = DataAggregator.aggregate_bitcoin_minutes_to_daily(sample_minute_bitcoin_df)
        assert len(agg_df) == 2
        assert list(agg_df.columns) == ['date', 'asset', 'open', 'high', 'low', 'close', 'volume']
        
        # Day 1: 2017-01-01
        day1 = agg_df[agg_df['date'] == '2017-01-01'].iloc[0]
        assert day1['open'] == 100.0   # First open
        assert day1['high'] == 115.0   # Max high
        assert day1['low'] == 98.0     # Min low
        assert day1['close'] == 111.0  # Last close
        assert day1['volume'] == 60.0  # 10 + 20 + 30
        assert day1['asset'] == 'Bitcoin'

        # Day 2: 2017-01-02
        day2 = agg_df[agg_df['date'] == '2017-01-02'].iloc[0]
        assert day2['open'] == 120.0
        assert day2['high'] == 130.0
        assert day2['low'] == 118.0
        assert day2['close'] == 126.0
        assert day2['volume'] == 40.0


class TestDataCleaner:
    def test_clean_daily_asset_envelope_alignment(self, sample_daily_raw_df):
        cleaned_df, stats = DataCleaner.clean_daily_asset(sample_daily_raw_df, asset_name="TestAsset")
        assert len(cleaned_df) == 2
        assert stats["ohlc_inconsistencies_adjusted"] == 2
        
        # Row 0: High was 99, Open 100 -> High adjusted to 100.0
        row0 = cleaned_df.iloc[0]
        assert row0['high'] >= row0['open']
        assert row0['high'] >= row0['close']
        assert row0['low'] <= row0['open']
        assert row0['low'] <= row0['close']

        # Row 1: Low was 108, Open 105 -> Low adjusted to 105.0
        row1 = cleaned_df.iloc[1]
        assert row1['low'] <= row1['open']
        assert row1['high'] >= row1['close']


class TestDataValidator:
    def test_valid_dataframe_passes(self):
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02'],
            'asset': ['Gold', 'Gold'],
            'open': [100.0, 102.0],
            'high': [105.0, 106.0],
            'low': [98.0, 101.0],
            'close': [102.0, 104.0],
            'volume': [1000.0, 1200.0]
        })
        is_valid, errors = DataValidator.validate_normalized_dataframe(df, "Gold")
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_ohlc_fails(self):
        df = pd.DataFrame({
            'date': ['2023-01-01'],
            'asset': ['Gold'],
            'open': [100.0],
            'high': [95.0],   # Invalid: High < Open
            'low': [90.0],
            'close': [92.0],
            'volume': [100.0]
        })
        is_valid, errors = DataValidator.validate_normalized_dataframe(df, "Gold")
        assert is_valid is False
        assert any("high < open" in err for err in errors)


class TestFullPipeline:
    def test_pipeline_execution_and_artifacts(self):
        result_dfs, report = run_pipeline()
        
        assert "gold_daily" in result_dfs
        assert "bitcoin_daily" in result_dfs
        assert "nvidia_daily" in result_dfs
        assert "market_data" in result_dfs

        # Check exact row counts
        assert len(result_dfs["gold_daily"]) == 6358
        assert len(result_dfs["bitcoin_daily"]) == 365
        assert len(result_dfs["nvidia_daily"]) == 6778
        assert len(result_dfs["market_data"]) == 13501

        # Check schema conformity
        required_cols = ['date', 'asset', 'open', 'high', 'low', 'close', 'volume']
        for name, df in result_dfs.items():
            assert list(df.columns) == required_cols
            assert not df.isnull().any().any(), f"Found NaNs in {name}"
            # Check price positivity
            assert (df['open'] > 0).all()
            assert (df['high'] > 0).all()
            assert (df['low'] > 0).all()
            assert (df['close'] > 0).all()
            # Check OHLC logic
            assert (df['high'] >= df['low']).all()
            assert (df['high'] >= df['open']).all()
            assert (df['high'] >= df['close']).all()
            assert (df['low'] <= df['open']).all()
            assert (df['low'] <= df['close']).all()
