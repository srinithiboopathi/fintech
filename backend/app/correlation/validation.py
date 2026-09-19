"""
Validation Helper Module for Correlation and Cross-Asset Engine.
"""
from typing import List, Optional
from datetime import datetime


def validate_correlation_assets(assets: List[str], min_count: int = 2) -> List[str]:
    """Validates that at least min_count distinct assets are specified."""
    if not assets or len(assets) < min_count:
        raise ValueError(f"Correlation analysis requires at least {min_count} assets, got {len(assets) if assets else 0}")
    
    # Remove duplicates while preserving order
    unique_assets = list(dict.fromkeys(assets))
    if len(unique_assets) < min_count:
        raise ValueError(f"Correlation analysis requires at least {min_count} distinct assets, got {len(unique_assets)}")
        
    return unique_assets


def validate_window_size(window: int, min_value: int = 2, max_value: int = 500) -> int:
    """Validates that a rolling correlation window is within valid mathematical bounds."""
    if not isinstance(window, int) or window < min_value or window > max_value:
        raise ValueError(f"Rolling window must be an integer between {min_value} and {max_value}, got {window}")
    return window


def validate_date_strings(start_date: Optional[str], end_date: Optional[str]) -> None:
    """Validates ISO date strings (YYYY-MM-DD) and order."""
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid start_date format '{start_date}'. Expected YYYY-MM-DD.")
            
    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid end_date format '{end_date}'. Expected YYYY-MM-DD.")
            
    if start_date and end_date and start_date > end_date:
        raise ValueError(f"start_date '{start_date}' cannot be greater than end_date '{end_date}'.")
