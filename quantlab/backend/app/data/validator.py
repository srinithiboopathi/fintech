from typing import List, Dict, Tuple, Any

class DataValidator:
    REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

    @classmethod
    def validate_ohlcv_series(cls, bars: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        errors = []
        if not bars:
            return False, ["Dataset is empty."]

        prev_date = None
        for idx, bar in enumerate(bars):
            # Check required columns
            for col in cls.REQUIRED_COLUMNS:
                if col not in bar:
                    errors.append(f"Row {idx}: Missing mandatory column '{col}'.")

            d = bar.get("date")
            if not d:
                errors.append(f"Row {idx}: Missing date value.")
            elif prev_date and d <= prev_date:
                errors.append(f"Row {idx} ({d}): Date is not chronologically ascending after ({prev_date}).")
            prev_date = d

            try:
                o = float(bar.get("open", 0))
                h = float(bar.get("high", 0))
                l = float(bar.get("low", 0))
                c = float(bar.get("close", 0))

                if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                    errors.append(f"Row {idx} ({d}): Non-positive price values detected (O:{o}, H:{h}, L:{l}, C:{c}).")
                if h < l:
                    errors.append(f"Row {idx} ({d}): High ({h}) is strictly less than Low ({l}).")
                if h < max(o, c):
                    errors.append(f"Row {idx} ({d}): High ({h}) is less than Open/Close.")
                if l > min(o, c):
                    errors.append(f"Row {idx} ({d}): Low ({l}) is greater than Open/Close.")
            except (ValueError, TypeError) as e:
                errors.append(f"Row {idx} ({d}): Non-numeric price values encountered: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors[:15]
