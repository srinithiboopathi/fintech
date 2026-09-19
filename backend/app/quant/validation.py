"""
Quantitative Parameter and Input Validation Module.
Ensures calculations receive valid mathematical parameters and guards against logical errors.
"""
from typing import Optional
from datetime import datetime


def validate_positive_integer(value: int, name: str = "parameter", min_value: int = 1) -> int:
    """Validates that a period/window is a positive integer >= min_value."""
    if not isinstance(value, int) or value < min_value:
        raise ValueError(f"{name} must be a positive integer greater than or equal to {min_value}, got {value}")
    return value


def validate_date_order(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates date format and ensures start_date <= end_date."""
    if start_date:
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid start_date format '{start_date}'. Expected YYYY-MM-DD.")
    if end_date:
        try:
            d_end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid end_date format '{end_date}'. Expected YYYY-MM-DD.")
            
    if start_date and end_date and start_date > end_date:
        raise ValueError(f"start_date '{start_date}' cannot be after end_date '{end_date}'")
