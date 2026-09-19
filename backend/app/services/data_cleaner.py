from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional, Union
import math
import pandas as pd

from app.models.schemas import (
    HistoricalPoint,
    CleanHistoricalPoint,
    DataQualityReport,
    DataSummaryResponse,
)
from app.utils.logging import logger

def normalize_timestamp_to_utc_iso(ts_val: Any) -> Optional[str]:
    """
    Normalizes any timestamp input (date, datetime, ISO string, timestamp int)
    strictly to UTC ISO-8601 string: 'YYYY-MM-DDTHH:MM:SSZ'.
    Returns None if missing or unparseable.
    """
    if ts_val is None:
        return None

    cleaned = str(ts_val).strip()
    if not cleaned or cleaned.lower() in ("none", "nan", "null", ""):
        return None

    # If already ISO-8601 UTC
    if cleaned.endswith("Z"):
        try:
            # Validate parseable
            dt = datetime.fromisoformat(cleaned[:-1]).replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    return None

class DataCleaningService:
    """
    Reusable data cleaning and validation engine for quantitative financial intelligence.
    Transforms raw OHLCV market points into pristine, validated historical series
    suitable for technical indicators, volatility, risk ratios, and backtesting.
    """

    def clean_historical_records(
        self,
        raw_records: List[Union[HistoricalPoint, Dict[str, Any]]],
        asset_name: str,
        symbol: str,
        source: str
    ) -> Tuple[List[CleanHistoricalPoint], DataQualityReport]:
        """
        Cleans and validates historical records:
        - Removes duplicate timestamps (preserves first occurrence)
        - Sorts records chronologically (oldest to newest)
        - Drops records with missing timestamps, non-numeric, or non-positive prices
        - Validates OHLC bounds (high >= max(O,C), low <= min(O,C), high >= low)
        - Preserves volume as None (null) for crypto/gold without coercing to 0
        - Generates comprehensive DataQualityReport
        """
        raw_count = len(raw_records)
        seen_timestamps: set = set()
        cleaned_points: List[CleanHistoricalPoint] = []
        issues: List[str] = []

        duplicates_removed = 0
        invalid_records_dropped = 0
        missing_close_count = 0
        missing_volume_count = 0
        ohlc_anomalies_detected = 0

        for idx, rec in enumerate(raw_records):
            # Extract dict or model fields
            if isinstance(rec, HistoricalPoint):
                r_dict = rec.model_dump()
            elif isinstance(rec, dict):
                r_dict = rec
            else:
                try:
                    r_dict = dict(rec)
                except Exception:
                    invalid_records_dropped += 1
                    issues.append(f"Record #{idx}: Unparseable record structure.")
                    continue

            # 1. Timestamp validation & UTC normalization
            raw_ts = r_dict.get("timestamp") or r_dict.get("datetime") or r_dict.get("date")
            utc_ts = normalize_timestamp_to_utc_iso(raw_ts)
            if not utc_ts:
                invalid_records_dropped += 1
                issues.append(f"Record #{idx}: Dropped due to missing or invalid timestamp '{raw_ts}'.")
                continue

            # 2. Duplicate detection
            if utc_ts in seen_timestamps:
                duplicates_removed += 1
                issues.append(f"Dropped duplicate record for timestamp: {utc_ts}")
                continue
            seen_timestamps.add(utc_ts)

            # 3. Numeric & Price validation
            raw_close = r_dict.get("close")
            if raw_close is None or str(raw_close).strip() in ("", "nan", "None", "."):
                missing_close_count += 1
                invalid_records_dropped += 1
                issues.append(f"Record #{idx} ({utc_ts}): Dropped due to missing close price.")
                continue

            try:
                close_val = float(raw_close)
                if math.isnan(close_val) or math.isinf(close_val) or close_val <= 0:
                    invalid_records_dropped += 1
                    issues.append(f"Record #{idx} ({utc_ts}): Dropped due to non-positive/NaN close price: {close_val}")
                    continue
            except (ValueError, TypeError):
                invalid_records_dropped += 1
                issues.append(f"Record #{idx} ({utc_ts}): Dropped due to non-numeric close price: {raw_close}")
                continue

            # Validate open, high, low
            try:
                open_val = float(r_dict.get("open", close_val)) if r_dict.get("open") is not None else close_val
                high_val = float(r_dict.get("high", max(open_val, close_val))) if r_dict.get("high") is not None else max(open_val, close_val)
                low_val = float(r_dict.get("low", min(open_val, close_val))) if r_dict.get("low") is not None else min(open_val, close_val)

                if open_val <= 0 or high_val <= 0 or low_val <= 0:
                    invalid_records_dropped += 1
                    issues.append(f"Record #{idx} ({utc_ts}): Dropped due to non-positive OHLC prices (O:{open_val}, H:{high_val}, L:{low_val}).")
                    continue
            except (ValueError, TypeError) as num_err:
                invalid_records_dropped += 1
                issues.append(f"Record #{idx} ({utc_ts}): Dropped due to non-numeric OHLC values: {num_err}")
                continue

            # 4. OHLC Relationship Validation
            if high_val < low_val:
                ohlc_anomalies_detected += 1
                issues.append(f"Record #{idx} ({utc_ts}): High ({high_val}) was lower than Low ({low_val}); inverted bounds.")
                high_val, low_val = low_val, high_val

            if high_val < max(open_val, close_val):
                ohlc_anomalies_detected += 1
                high_val = max(open_val, close_val, high_val)

            if low_val > min(open_val, close_val):
                ohlc_anomalies_detected += 1
                low_val = min(open_val, close_val, low_val)

            # 5. Volume handling: strictly preserve None when absent or null
            raw_vol = r_dict.get("volume")
            vol_val: Optional[float] = None
            if raw_vol is not None and str(raw_vol).strip() != "" and str(raw_vol).lower() not in ("none", "nan", "null"):
                try:
                    parsed_vol = float(raw_vol)
                    if not math.isnan(parsed_vol) and parsed_vol >= 0:
                        vol_val = parsed_vol
                    else:
                        vol_val = None
                        missing_volume_count += 1
                except (ValueError, TypeError):
                    vol_val = None
                    missing_volume_count += 1
            else:
                missing_volume_count += 1

            rec_source = r_dict.get("source") or source
            cleaned_points.append(CleanHistoricalPoint(
                timestamp=utc_ts,
                open=round(open_val, 6),
                high=round(high_val, 6),
                low=round(low_val, 6),
                close=round(close_val, 6),
                volume=vol_val,
                asset=asset_name,
                symbol=symbol,
                source=rec_source,
                is_valid=True
            ))

        # 6. Chronological Sorting (oldest to newest)
        cleaned_points.sort(key=lambda p: p.timestamp)

        # 7. Quality Assessment
        earliest_ts = cleaned_points[0].timestamp if cleaned_points else None
        latest_ts = cleaned_points[-1].timestamp if cleaned_points else None

        if invalid_records_dropped == 0 and duplicates_removed == 0 and ohlc_anomalies_detected == 0:
            quality_status = "pristine"
        elif invalid_records_dropped == 0:
            quality_status = "good"
        elif len(cleaned_points) > 0:
            quality_status = "acceptable"
        else:
            quality_status = "degraded"

        report = DataQualityReport(
            total_records=len(cleaned_points),
            raw_records=raw_count,
            duplicates_removed=duplicates_removed,
            invalid_records_dropped=invalid_records_dropped,
            missing_close_count=missing_close_count,
            missing_volume_count=missing_volume_count,
            ohlc_anomalies_detected=ohlc_anomalies_detected,
            earliest_timestamp=earliest_ts,
            latest_timestamp=latest_ts,
            quality_status=quality_status,
            issues=issues
        )

        logger.info(
            f"DataCleaner: Processed {raw_count} raw points for {asset_name} -> "
            f"{len(cleaned_points)} clean points (Status: {quality_status}, Duplicates dropped: {duplicates_removed})"
        )

        return cleaned_points, report

    def build_summary(
        self,
        asset_name: str,
        symbol: str,
        source: str,
        clean_points: List[CleanHistoricalPoint],
        report: DataQualityReport
    ) -> DataSummaryResponse:
        """
        Creates concise executive summary matching requirements of GET /market/{asset}/data/summary.
        """
        latest_close = clean_points[-1].close if clean_points else None

        return DataSummaryResponse(
            asset=asset_name,
            symbol=symbol,
            source=source,
            total_records=report.total_records,
            earliest_timestamp=report.earliest_timestamp,
            latest_timestamp=report.latest_timestamp,
            missing_value_count={
                "close": report.missing_close_count,
                "volume": report.missing_volume_count,
                "invalid_dropped": report.invalid_records_dropped
            },
            duplicate_count=report.duplicates_removed,
            latest_close=latest_close,
            data_quality=report.quality_status,
            data_status="clean_verified"
        )

    def to_dataframe(self, clean_points: List[CleanHistoricalPoint]) -> pd.DataFrame:
        """
        Converts a list of CleanHistoricalPoint into a typed, indexed pandas DataFrame
        optimized for technical indicators (SMA, EMA), returns, volatility, Sharpe ratio,
        correlation, and vector backtesting.
        """
        if not clean_points:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "asset", "symbol", "source"])

        data = [p.model_dump() for p in clean_points]
        df = pd.DataFrame(data)

        # Convert timestamp to UTC DatetimeIndex
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df.set_index("timestamp", inplace=True)

        # Enforce float64 types for mathematical precision
        numeric_cols = ["open", "high", "low", "close", "volume"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Sort chronologically
        df.sort_index(ascending=True, inplace=True)
        return df

data_cleaning_service = DataCleaningService()
