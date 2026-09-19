"""
QuantLab Cross-Asset Correlation Engine
"""

from .matrix import (
    align_price_series,
    calculate_multi_asset_returns,
    calculate_correlation_matrix,
    compute_cross_asset_correlation_matrix,
)
from .rolling import (
    calculate_rolling_pairwise_correlation,
    calculate_multi_asset_rolling_correlations,
)

__all__ = [
    "align_price_series",
    "calculate_multi_asset_returns",
    "calculate_correlation_matrix",
    "compute_cross_asset_correlation_matrix",
    "calculate_rolling_pairwise_correlation",
    "calculate_multi_asset_rolling_correlations",
]
