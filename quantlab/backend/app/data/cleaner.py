import re
from datetime import datetime
from typing import List, Dict, Any, Optional

class DataCleaner:
    @staticmethod
    def normalize_column_name(col: str) -> str:
        c = col.strip().lower().replace(" ", "_").replace("-", "_")
        if c in ["date", "timestamp", "time", "datetime"]:
            return "date"
        if c in ["open", "o", "open_price"]:
            return "open"
        if c in ["high", "h", "high_price"]:
            return "high"
        if c in ["low", "l", "low_price"]:
            return "low"
        if c in ["close", "c", "close_price"]:
            return "close"
        if c in ["adj_close", "adjclose", "adjusted_close"]:
            return "adj_close"
        if c in ["volume", "vol", "v", "contracts"]:
            return "volume"
        return c

    @staticmethod
    def parse_date_string(date_val: Any) -> Optional[str]:
        if not date_val:
            return None
        date_str = str(date_val).strip()
        # Common formats
        formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Reject invalid future dates beyond year 2035
                if dt.year < 1970 or dt.year > 2035:
                    return None
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Regex check for YYYY-MM-DD
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", date_str)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return None

    @classmethod
    def clean_raw_records(cls, raw_rows: List[Dict[str, Any]], symbol: str = "") -> List[Dict[str, Any]]:
        """
        Processes and harmonizes raw rows:
        1. Normalizes column headers
        2. Validates and parses dates
        3. Converts and sanitizes numerical OHLCV
        4. Removes duplicates by date (keeping latest valid)
        5. Sorts chronologically
        6. Imputes missing fields and computes daily arithmetic returns without look-ahead bias
        """
        date_map = {}

        for row in raw_rows:
            # Map normalized headers
            norm_row = {}
            for k, v in row.items():
                if k is not None:
                    norm_row[cls.normalize_column_name(k)] = v

            parsed_date = cls.parse_date_string(norm_row.get("date"))
            if not parsed_date:
                continue

            try:
                # Safe numeric parsing
                c_str = str(norm_row.get("close", "")).replace(",", "").replace("$", "")
                c = float(c_str)
                if c <= 0 or not (c == c): # check for NaN
                    continue

                o_str = str(norm_row.get("open", c)).replace(",", "").replace("$", "")
                o = float(o_str) if o_str else c

                h_str = str(norm_row.get("high", max(o, c))).replace(",", "").replace("$", "")
                h = float(h_str) if h_str else max(o, c)

                l_str = str(norm_row.get("low", min(o, c))).replace(",", "").replace("$", "")
                l = float(l_str) if l_str else min(o, c)

                adj_str = str(norm_row.get("adj_close", c)).replace(",", "").replace("$", "")
                adj = float(adj_str) if adj_str else c

                v_str = str(norm_row.get("volume", 0.0)).replace(",", "").replace("$", "")
                v = float(v_str) if v_str else 0.0

                # Ensure high is maximum, low is minimum
                h = max(h, o, c)
                l = min(l, o, c)

                date_map[parsed_date] = {
                    "date": parsed_date,
                    "symbol": symbol.upper() if symbol else norm_row.get("symbol", "").upper(),
                    "open": round(o, 4),
                    "high": round(h, 4),
                    "low": round(l, 4),
                    "close": round(c, 4),
                    "adj_close": round(adj, 4),
                    "volume": round(v, 2),
                }
            except (ValueError, TypeError):
                continue

        # Sort chronologically by date
        sorted_dates = sorted(date_map.keys())
        cleaned_bars = []
        prev_close = None

        for d in sorted_dates:
            bar = date_map[d]
            c = bar["close"]
            # No lookahead: return is computed strictly from prior bar's close
            ret = (c - prev_close) / prev_close if prev_close is not None and prev_close > 0 else 0.0
            prev_close = c
            bar["daily_return"] = round(ret, 6)
            cleaned_bars.append(bar)

        return cleaned_bars

    @classmethod
    def remove_missing_and_impute(cls, bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return cls.clean_raw_records(bars)
