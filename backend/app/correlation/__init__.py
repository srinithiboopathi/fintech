"""
Correlation and Cross-Asset Analytics Package for QUANTLAB.
Provides pure, deterministic mathematical algorithms for:
- Date Alignment across heterogeneous market calendars
- Pairwise Pearson Correlation
- Cross-Asset Correlation Matrix
- Rolling Multi-Window Correlation
- Comparative Performance Analytics
"""
from backend.app.correlation.alignment import align_asset_returns, align_two_asset_returns
from backend.app.correlation.matrix import (
    calculate_correlation_matrix,
    calculate_pairwise_correlation,
)
from backend.app.correlation.rolling import calculate_rolling_correlation
from backend.app.correlation.validation import (
    validate_correlation_assets,
    validate_window_size,
)

__all__ = [
    "align_asset_returns",
    "align_two_asset_returns",
    "calculate_correlation_matrix",
    "calculate_pairwise_correlation",
    "calculate_rolling_correlation",
    "validate_correlation_assets",
    "validate_window_size",
]
