"""
backend/app/services/correlation.py

Quantitative Correlation & Rolling Correlation Analysis Engine.
Calculates pairwise Pearson correlation matrices and rolling correlation time series
strictly from cleaned historical market records produced by Step 3.

Mathematical Specifications:
1. Daily Return Formulation:
   daily_return_t = (Close_t / Close_(t-1)) - 1
   For each asset, returns are indexed by UTC date (YYYY-MM-DD).

2. Date Alignment:
   - Aligns return series strictly on matching timestamps/dates.
   - Only overlapping observations are included (inner join).
   - Zero forward-filling of returns; missing observations are never invented.

3. Pearson Correlation:
   r_{xy} = sum((x_i - mean(x)) * (y_i - mean(y))) / sqrt(sum((x_i - mean(x))^2) * sum((y_i - mean(y))^2))
   - Strictly symmetric: r_{xy} == r_{yx}.
   - Diagonal values equal 1.0.
   - Evaluates to None if variance is zero or fewer than 2 observations exist.

4. Rolling Correlation:
   For window W >= 2:
   - Observation i < W - 1: Evaluates strictly to None (warmup).
   - Observation i >= W - 1: Evaluates to Pearson r over observations [i - W + 1 : i + 1].
   - Strictly causal: Zero look-ahead bias. Future observations never influence prior values.
"""

import math
from typing import List, Dict, Optional, Tuple, Any
from app.config import SUPPORTED_ASSETS, resolve_asset_config
from app.models.schemas import (
    CleanHistoricalPoint,
    CorrelationMatrixResponse,
    RollingCorrelationPoint,
    RollingPairSeries,
    RollingCorrelationResponse,
)
from app.utils.exceptions import InvalidCorrelationWindowError


def compute_pearson_correlation(
    x: List[float],
    y: List[float],
    precision: Optional[int] = 4
) -> Optional[float]:
    """
    Computes Pearson product-moment correlation coefficient between two series.

    Formula:
        r = sum((x_i - bar{x}) * (y_i - bar{y})) / (sqrt(sum((x_i - bar{x})^2)) * sqrt(sum((y_i - bar{y})^2)))

    Args:
        x: First series of numeric observations.
        y: Second series of numeric observations (must match len(x)).
        precision: Decimal rounding precision (default 4).

    Returns:
        float in [-1.0, 1.0], or None if n < 2 or variance is zero.
    """
    n = len(x)
    if n != len(y) or n < 2:
        return None

    # Exact identity optimization
    if x == y:
        # Verify variance is non-zero
        mean_x = sum(x) / n
        var_x = sum((xi - mean_x) ** 2 for xi in x)
        return 1.0 if var_x > 1e-15 else None

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    ss_xx = sum((xi - mean_x) ** 2 for xi in x)
    ss_yy = sum((yi - mean_y) ** 2 for yi in y)

    # Zero variance check
    if ss_xx < 1e-15 or ss_yy < 1e-15:
        return None

    ss_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))

    denominator = math.sqrt(ss_xx * ss_yy)
    if denominator == 0.0:
        return None

    r = ss_xy / denominator

    # Numerical boundary clamping to [-1.0, 1.0]
    r = max(-1.0, min(1.0, r))

    return round(r, precision) if precision is not None else r


def extract_daily_returns(clean_points: List[CleanHistoricalPoint]) -> Dict[str, float]:
    """
    Extracts daily percentage returns keyed by UTC date string (YYYY-MM-DD).

    Formula:
        Return_t = (Close_t / Close_(t-1)) - 1

    Input must be chronologically sorted ascending.
    """
    returns: Dict[str, float] = {}
    n = len(clean_points)
    if n < 2:
        return returns

    for i in range(1, n):
        prev_close = clean_points[i - 1].close
        curr_close = clean_points[i].close
        if prev_close <= 0:
            continue

        date_key = clean_points[i].timestamp[:10]
        ret = (curr_close - prev_close) / prev_close
        returns[date_key] = ret

    return returns


def align_return_series(
    returns_map: Dict[str, Dict[str, float]],
    asset_keys: List[str]
) -> Tuple[List[str], Dict[str, List[float]]]:
    """
    Aligns multiple asset return series on strictly common overlapping dates.

    Guarantees:
    - Inner join across all specified assets.
    - Ascending chronological order.
    - No forward-filling or invented values.

    Returns:
        (common_dates, aligned_returns_dict)
    """
    if not asset_keys:
        return [], {}

    # Intersection of all dates
    common_dates_set = set(returns_map[asset_keys[0]].keys())
    for key in asset_keys[1:]:
        common_dates_set &= set(returns_map[key].keys())

    common_dates = sorted(common_dates_set)

    aligned: Dict[str, List[float]] = {
        key: [returns_map[key][d] for d in common_dates]
        for key in asset_keys
    }

    return common_dates, aligned


def calculate_rolling_correlation(
    x: List[float],
    y: List[float],
    dates: List[str],
    window: int = 20,
    precision: int = 4
) -> List[RollingCorrelationPoint]:
    """
    Calculates rolling Pearson correlation series over a lookback window W.

    Args:
        x: First aligned series of returns.
        y: Second aligned series of returns.
        dates: List of matching date strings.
        window: Lookback window in observations (must be >= 2).
        precision: Decimal rounding precision (default 4).

    Returns:
        List of RollingCorrelationPoint objects.
        Indices 0 to window - 2 evaluate strictly to None.
    """
    if window < 2:
        raise InvalidCorrelationWindowError()

    n = len(dates)
    points: List[RollingCorrelationPoint] = []

    for i in range(n):
        date_str = dates[i]
        if i < window - 1:
            points.append(RollingCorrelationPoint(timestamp=date_str, correlation=None))
        else:
            sub_x = x[i - window + 1 : i + 1]
            sub_y = y[i - window + 1 : i + 1]
            corr = compute_pearson_correlation(sub_x, sub_y, precision=precision)
            points.append(RollingCorrelationPoint(timestamp=date_str, correlation=corr))

    return points


class CorrelationService:
    """
    Production-grade quantitative correlation service for multi-asset analytics.
    """

    def compute_correlation_matrix(
        self,
        clean_points_map: Dict[str, List[CleanHistoricalPoint]],
        symbols_map: Dict[str, str],
        asset_names_map: Dict[str, str],
        precision: int = 4
    ) -> CorrelationMatrixResponse:
        """
        Calculates symmetric Pearson correlation matrix across multi-asset returns.
        """
        asset_keys = list(clean_points_map.keys())

        # Extract daily returns
        returns_map = {
            key: extract_daily_returns(clean_points_map[key])
            for key in asset_keys
        }

        # Align on mutual overlapping dates
        common_dates, aligned = align_return_series(returns_map, asset_keys)
        obs_count = len(common_dates)
        start_date = common_dates[0] if common_dates else None
        end_date = common_dates[-1] if common_dates else None

        symbols = [symbols_map.get(k, k) for k in asset_keys]
        assets = [asset_names_map.get(k, k) for k in asset_keys]

        # Compute pairwise symmetric matrix
        matrix: Dict[str, Dict[str, Optional[float]]] = {}
        for i, key_i in enumerate(asset_keys):
            sym_i = symbols_map.get(key_i, key_i)
            matrix[sym_i] = {}
            for j, key_j in enumerate(asset_keys):
                sym_j = symbols_map.get(key_j, key_j)
                if i == j:
                    matrix[sym_i][sym_j] = 1.0
                elif sym_j in matrix and sym_i in matrix[sym_j]:
                    # Symmetry guarantee
                    matrix[sym_i][sym_j] = matrix[sym_j][sym_i]
                else:
                    corr = compute_pearson_correlation(
                        aligned[key_i],
                        aligned[key_j],
                        precision=precision
                    )
                    matrix[sym_i][sym_j] = corr

        return CorrelationMatrixResponse(
            assets=assets,
            symbols=symbols,
            matrix=matrix,
            observation_count=obs_count,
            start_date=start_date,
            end_date=end_date,
            source="Twelve Data",
            data_status="calculated",
            methodology="Pearson correlation on aligned daily percentage returns ((close_t / close_{t-1}) - 1)"
        )

    def compute_rolling_correlation(
        self,
        clean_points_map: Dict[str, List[CleanHistoricalPoint]],
        symbols_map: Dict[str, str],
        asset_names_map: Dict[str, str],
        window: int = 20,
        asset1: Optional[str] = None,
        asset2: Optional[str] = None,
        precision: int = 4
    ) -> RollingCorrelationResponse:
        """
        Calculates pairwise rolling correlation time series across asset combinations.
        """
        if window < 2:
            raise InvalidCorrelationWindowError()

        asset_keys = list(clean_points_map.keys())

        # Extract returns
        returns_map = {
            key: extract_daily_returns(clean_points_map[key])
            for key in asset_keys
        }

        # Determine pairs to evaluate
        pairs_to_evaluate: List[Tuple[str, str]] = []
        if asset1 and asset2:
            pairs_to_evaluate.append((asset1, asset2))
        else:
            for i in range(len(asset_keys)):
                for j in range(i + 1, len(asset_keys)):
                    pairs_to_evaluate.append((asset_keys[i], asset_keys[j]))

        pair_series_list: List[RollingPairSeries] = []

        for k1, k2 in pairs_to_evaluate:
            sym1 = symbols_map.get(k1, k1)
            sym2 = symbols_map.get(k2, k2)
            pair_name = f"{sym1} vs {sym2}"

            # Align specifically for this pair on pairwise overlapping dates
            pair_dates, pair_aligned = align_return_series(returns_map, [k1, k2])
            obs_count = len(pair_dates)

            series = calculate_rolling_correlation(
                x=pair_aligned.get(k1, []),
                y=pair_aligned.get(k2, []),
                dates=pair_dates,
                window=window,
                precision=precision
            )

            valid_values = [p.correlation for p in series if p.correlation is not None]
            valid_count = len(valid_values)
            latest_corr = valid_values[-1] if valid_values else None

            pair_series_list.append(
                RollingPairSeries(
                    pair=pair_name,
                    asset1=sym1,
                    asset2=sym2,
                    window=window,
                    observation_count=obs_count,
                    valid_correlation_count=valid_count,
                    latest_correlation=latest_corr,
                    series=series
                )
            )

        assets = [asset_names_map.get(k, k) for k in asset_keys]

        return RollingCorrelationResponse(
            window=window,
            assets=assets,
            source="Twelve Data",
            data_status="calculated",
            pairs=pair_series_list
        )


correlation_service = CorrelationService()
