"""
backend/tests/test_strategy_comparison.py

Comprehensive Test Suite for Step 10: Strategy Comparison & Robustness Analysis.
Covers:
1. All four strategies included
2. Identical backtest assumptions
3. Comparison output schema and factual reporting (no 'best/winner' labels)
4. Benchmark comparison
5. Excess return calculation
6. SMA parameter combinations
7. EMA parameter combinations
8. Momentum parameter combinations
9. Mean Reversion parameter combinations
10. Invalid parameters handling
11. Invalid strategy rejection
12. Bounded parameter ranges limit enforcement
13. Deterministic repeatability
14. Zero look-ahead bias protection
15. Insufficient data handling
16. Live data endpoint: NVDA comparison
17. Live data endpoint: BTC/USD comparison
18. Live data endpoint: XAU/USD comparison
19. Live data endpoint: Robustness API
20. Robustness API parameter validation (HTTP 400)
"""

import copy
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    CleanHistoricalPoint,
    StrategyComparisonRequest,
    RobustnessAnalysisRequest,
)
from app.services.strategy_comparison import (
    strategy_comparison_service,
    MAX_ROBUSTNESS_COMBINATIONS,
)
from app.utils.exceptions import (
    UnsupportedStrategyError,
    InvalidComparisonRequestError,
    InvalidRobustnessParameterError,
    InvalidBacktestParameterError,
    InsufficientHistoricalDataError,
)

client = TestClient(app)


def make_clean_points(prices, start_date="2026-01-01"):
    """Helper creating deterministic CleanHistoricalPoint sequence."""
    base_dt = datetime.fromisoformat(f"{start_date}T00:00:00")
    points = []
    for i, p in enumerate(prices):
        dt = base_dt + timedelta(days=i)
        ts = dt.strftime("%Y-%m-%dT00:00:00Z")
        points.append(
            CleanHistoricalPoint(
                timestamp=ts,
                open=p,
                high=p * 1.02,
                low=p * 0.98,
                close=p,
                volume=1000.0,
                asset="NVIDIA",
                symbol="NVDA",
                source="Twelve Data",
            )
        )
    return points


# ==============================================================================
# 1. ALL FOUR STRATEGIES INCLUDED
# ==============================================================================
def test_comparison_includes_all_four_strategies():
    """1. Verifies default comparison evaluates all 4 canonical strategies."""
    prices = [100.0 + (i % 5) * 2.0 for i in range(30)]
    pts = make_clean_points(prices)
    req = StrategyComparisonRequest()
    res = strategy_comparison_service.compare_strategies(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    strat_names = [s.strategy for s in res.strategies]
    assert len(strat_names) == 4
    assert set(strat_names) == {"sma_crossover", "ema_trend", "momentum", "mean_reversion"}


# ==============================================================================
# 2. IDENTICAL BACKTEST ASSUMPTIONS
# ==============================================================================
def test_comparison_identical_backtest_assumptions():
    """2. Verifies all strategies are tested under identical financial and temporal conditions."""
    prices = [100.0 + (i % 7) * 3.0 for i in range(35)]
    pts = make_clean_points(prices)
    req = StrategyComparisonRequest(
        initial_capital=50000.0,
        transaction_cost_rate=0.002,
        allocation=0.8,
    )
    res = strategy_comparison_service.compare_strategies(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.observation_count == len(pts)
    assert res.start_date == pts[0].timestamp
    assert res.end_date == pts[-1].timestamp
    assert res.benchmark.initial_value == 50000.0

    for s in res.strategies:
        assert s.initial_capital == 50000.0
        assert s.final_portfolio_value > 0.0


# ==============================================================================
# 3. COMPARISON OUTPUT SCHEMA & FACTUAL REPORTING
# ==============================================================================
def test_comparison_output_schema_and_factual_reporting():
    """3. Verifies schema fields are strictly factual without subjective 'winner' or 'best' labels."""
    prices = [100.0, 102.0, 101.0, 105.0, 108.0, 103.0, 107.0, 110.0, 106.0, 112.0]
    pts = make_clean_points(prices)
    req = StrategyComparisonRequest()
    res = strategy_comparison_service.compare_strategies(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    data_dict = res.model_dump()
    json_str = str(data_dict).lower()
    # Factual invariant: platform never labels strategies as winner or best
    assert "winner" not in json_str
    assert "best" not in json_str
    assert "loser" not in json_str

    for s in res.strategies:
        assert isinstance(s.final_portfolio_value, (int, float))
        assert isinstance(s.total_return, (int, float))
        assert isinstance(s.number_of_trades, int)
        assert isinstance(s.maximum_drawdown, (int, float))
        assert isinstance(s.benchmark_return, (int, float))
        assert isinstance(s.excess_return_vs_benchmark, (int, float))


# ==============================================================================
# 4. BENCHMARK COMPARISON
# ==============================================================================
def test_comparison_benchmark_returned():
    """4. Verifies identical baseline Buy & Hold benchmark is generated and shared."""
    prices = [100.0, 105.0, 110.0, 115.0, 120.0]
    pts = make_clean_points(prices)
    req = StrategyComparisonRequest(initial_capital=100000.0, transaction_cost_rate=0.001)
    res = strategy_comparison_service.compare_strategies(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.benchmark.benchmark_name == "Buy & Hold"
    assert res.benchmark.initial_value == 100000.0
    assert res.benchmark.final_value > 0.0
    # Every strategy references the exact same benchmark_return
    for s in res.strategies:
        assert s.benchmark_return == res.benchmark.total_return_pct


# ==============================================================================
# 5. EXCESS RETURN CALCULATION
# ==============================================================================
def test_comparison_excess_return_calculation():
    """5. Verifies excess_return_vs_benchmark is exactly (total_return - benchmark_return)."""
    prices = [100.0 + i * 2.0 for i in range(25)]
    pts = make_clean_points(prices)
    req = StrategyComparisonRequest()
    res = strategy_comparison_service.compare_strategies(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    for s in res.strategies:
        expected_excess = round(s.total_return - s.benchmark_return, 4)
        assert s.excess_return_vs_benchmark == expected_excess


# ==============================================================================
# 6. SMA PARAMETER COMBINATIONS
# ==============================================================================
def test_robustness_sma_parameter_combinations():
    """6. Verifies SMA parameter grid generates valid combinations where short < long."""
    prices = [100.0 + (i % 6) * 2.0 for i in range(30)]
    pts = make_clean_points(prices)
    grid = {
        "short_period": [5, 10],
        "long_period": [10, 15, 20],
    }
    # Combinations where short < long:
    # (5, 10), (5, 15), (5, 20), (10, 15), (10, 20) -> 5 valid combinations
    req = RobustnessAnalysisRequest(strategy="sma_crossover", parameter_grid=grid)
    res = strategy_comparison_service.analyze_robustness(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.total_combinations_tested == 5
    assert len(res.results) == 5
    for r in res.results:
        assert r.parameters["short_period"] < r.parameters["long_period"]
        assert r.strategy == "sma_crossover"


# ==============================================================================
# 7. EMA PARAMETER COMBINATIONS
# ==============================================================================
def test_robustness_ema_parameter_combinations():
    """7. Verifies EMA parameter grid evaluates all supplied periods."""
    prices = [100.0 + (i % 5) * 2.0 for i in range(25)]
    pts = make_clean_points(prices)
    grid = {"ema_period": [5, 10, 15, 20]}
    req = RobustnessAnalysisRequest(strategy="ema_trend", parameter_grid=grid)
    res = strategy_comparison_service.analyze_robustness(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.total_combinations_tested == 4
    tested_periods = [r.parameters["ema_period"] for r in res.results]
    assert tested_periods == [5, 10, 15, 20]


# ==============================================================================
# 8. MOMENTUM PARAMETER COMBINATIONS
# ==============================================================================
def test_robustness_momentum_parameter_combinations():
    """8. Verifies Momentum parameter grid evaluates all lookback periods."""
    prices = [100.0 + (i % 4) * 3.0 for i in range(25)]
    pts = make_clean_points(prices)
    grid = {"lookback": [3, 5, 10]}
    req = RobustnessAnalysisRequest(strategy="momentum", parameter_grid=grid)
    res = strategy_comparison_service.analyze_robustness(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.total_combinations_tested == 3
    tested_lb = [r.parameters["lookback"] for r in res.results]
    assert tested_lb == [3, 5, 10]


# ==============================================================================
# 9. MEAN REVERSION PARAMETER COMBINATIONS
# ==============================================================================
def test_robustness_mean_reversion_parameter_combinations():
    """9. Verifies Mean Reversion evaluates Cartesian product of lookback and threshold."""
    prices = [100.0 + (i % 8) * 1.5 for i in range(30)]
    pts = make_clean_points(prices)
    grid = {
        "lookback": [5, 10],
        "entry_threshold": [0.5, 1.0, 1.5],
    }
    # 2 x 3 = 6 combinations
    req = RobustnessAnalysisRequest(strategy="mean_reversion", parameter_grid=grid)
    res = strategy_comparison_service.analyze_robustness(
        clean_points=pts,
        request=req,
        asset_name="NVIDIA",
        symbol="NVDA",
    )

    assert res.total_combinations_tested == 6
    assert len(res.results) == 6


# ==============================================================================
# 10. INVALID PARAMETERS HANDLING
# ==============================================================================
def test_robustness_invalid_parameters():
    """10. Verifies negative, zero, or non-numeric grid values raise HTTP 400."""
    pts = make_clean_points([100.0, 102.0, 105.0])

    # Zero / negative period in EMA
    with pytest.raises(InvalidRobustnessParameterError):
        req = RobustnessAnalysisRequest(strategy="ema_trend", parameter_grid={"ema_period": [0, 10]})
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")

    # Negative threshold in Mean Reversion
    with pytest.raises(InvalidRobustnessParameterError):
        req = RobustnessAnalysisRequest(
            strategy="mean_reversion",
            parameter_grid={"lookback": [10], "entry_threshold": [-1.0]},
        )
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")

    # Empty parameter list
    with pytest.raises(InvalidRobustnessParameterError):
        req = RobustnessAnalysisRequest(strategy="momentum", parameter_grid={"lookback": []})
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")

    # SMA where all short >= long
    with pytest.raises(InvalidRobustnessParameterError):
        req = RobustnessAnalysisRequest(
            strategy="sma_crossover",
            parameter_grid={"short_period": [20, 30], "long_period": [10]},
        )
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")


# ==============================================================================
# 11. INVALID STRATEGY REJECTION
# ==============================================================================
def test_robustness_invalid_strategy():
    """11. Verifies unknown strategy raises UnsupportedStrategyError (HTTP 400)."""
    pts = make_clean_points([100.0, 102.0, 105.0])
    with pytest.raises(UnsupportedStrategyError):
        req = RobustnessAnalysisRequest(strategy="arbitrage", parameter_grid={"period": [10]})
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")


# ==============================================================================
# 12. BOUNDED PARAMETER RANGES LIMIT ENFORCEMENT
# ==============================================================================
def test_robustness_bounded_parameter_ranges():
    """12. Verifies parameter grids with > 50 combinations are rejected to prevent DoS."""
    pts = make_clean_points([100.0, 102.0, 105.0])
    # 10 short x 10 long = up to 100 combinations (> 50)
    grid = {
        "short_period": list(range(1, 11)),
        "long_period": list(range(20, 30)),
    }
    with pytest.raises(InvalidRobustnessParameterError) as excinfo:
        req = RobustnessAnalysisRequest(strategy="sma_crossover", parameter_grid=grid)
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")

    assert "exceeding the maximum allowed limit" in str(excinfo.value.message)


# ==============================================================================
# 13. DETERMINISTIC REPEATABILITY
# ==============================================================================
def test_comparison_and_robustness_deterministic():
    """13. Verifies multiple executions on identical data produce strictly identical metrics."""
    prices = [100.0, 102.0, 99.0, 105.0, 108.0, 104.0, 107.0, 112.0]
    pts = make_clean_points(prices)

    req_comp = StrategyComparisonRequest()
    res1 = strategy_comparison_service.compare_strategies(pts, req_comp, "NVIDIA", "NVDA")
    res2 = strategy_comparison_service.compare_strategies(pts, req_comp, "NVIDIA", "NVDA")

    assert res1.model_dump() == res2.model_dump()

    req_rob = RobustnessAnalysisRequest(strategy="momentum", parameter_grid={"lookback": [2, 4]})
    rob1 = strategy_comparison_service.analyze_robustness(pts, req_rob, "NVIDIA", "NVDA")
    rob2 = strategy_comparison_service.analyze_robustness(pts, req_rob, "NVIDIA", "NVDA")

    assert rob1.model_dump() == rob2.model_dump()


# ==============================================================================
# 14. ZERO LOOK-AHEAD BIAS PROTECTION
# ==============================================================================
def test_look_ahead_protection_robustness():
    """14. Verifies modifying future prices does NOT alter signals or performance at observation t."""
    base_prices = [100.0, 102.0, 104.0, 103.0, 105.0, 106.0, 108.0]
    pts_base = make_clean_points(base_prices)

    # Modified prices where future (after t=4) is completely altered
    perturbed_prices = [100.0, 102.0, 104.0, 103.0, 105.0, 200.0, 300.0]
    pts_perturbed = make_clean_points(perturbed_prices)

    # Test EMA trend over t=0..4
    from app.services.strategies import strategy_service
    signals_base, _ = strategy_service.generate_signals("ema_trend", pts_base, {"ema_period": 3})
    signals_pert, _ = strategy_service.generate_signals("ema_trend", pts_perturbed, {"ema_period": 3})

    for i in range(5):
        assert signals_base[i].signal == signals_pert[i].signal
        assert signals_base[i].indicators["ema"] == signals_pert[i].indicators["ema"]


# ==============================================================================
# 15. INSUFFICIENT DATA HANDLING
# ==============================================================================
def test_insufficient_data_handling():
    """15. Verifies comparison and robustness raise error when data points < 2."""
    pts = make_clean_points([100.0])

    with pytest.raises(InsufficientHistoricalDataError):
        req = StrategyComparisonRequest()
        strategy_comparison_service.compare_strategies(pts, req, "NVIDIA", "NVDA")

    with pytest.raises(InsufficientHistoricalDataError):
        req = RobustnessAnalysisRequest(strategy="momentum", parameter_grid={"lookback": [1]})
        strategy_comparison_service.analyze_robustness(pts, req, "NVIDIA", "NVDA")


# ==============================================================================
# 16. LIVE DATA ENDPOINT: NVDA COMPARISON
# ==============================================================================
def test_api_comparison_nvidia():
    """16. Verifies POST /market/nvidia/strategy/compare returns valid comparison for NVIDIA."""
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation": 1.0,
    }
    r = client.post("/market/nvidia/strategy/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["asset"] == "NVIDIA"
    assert data["symbol"] == "NVDA"
    assert len(data["strategies"]) == 4
    for s in data["strategies"]:
        assert s["final_portfolio_value"] > 0
        assert s["benchmark_return"] is not None


# ==============================================================================
# 17. LIVE DATA ENDPOINT: BTC/USD COMPARISON
# ==============================================================================
def test_api_comparison_bitcoin():
    """17. Verifies POST /market/bitcoin/strategy/compare returns valid comparison for Bitcoin."""
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation": 1.0,
    }
    r = client.post("/market/bitcoin/strategy/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "BTC/USD"
    assert len(data["strategies"]) == 4


# ==============================================================================
# 18. LIVE DATA ENDPOINT: XAU/USD COMPARISON
# ==============================================================================
def test_api_comparison_gold():
    """18. Verifies POST /market/gold/strategy/compare returns valid comparison for Gold."""
    payload = {
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation": 1.0,
    }
    r = client.post("/market/gold/strategy/compare", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["symbol"] == "XAU/USD"
    assert len(data["strategies"]) == 4


# ==============================================================================
# 19. LIVE DATA ENDPOINT: ROBUSTNESS API
# ==============================================================================
def test_api_robustness_endpoint():
    """19. Verifies POST /market/nvidia/strategy/robustness executes parameter grid."""
    payload = {
        "strategy": "ema_trend",
        "parameter_grid": {
            "ema_period": [10, 20, 30]
        },
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation": 1.0,
    }
    r = client.post("/market/nvidia/strategy/robustness", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "ema_trend"
    assert data["total_combinations_tested"] == 3
    assert len(data["results"]) == 3
    for res in data["results"]:
        assert res["parameters"]["ema_period"] in [10, 20, 30]
        assert res["final_portfolio_value"] > 0


# ==============================================================================
# 20. ROBUSTNESS API PARAMETER VALIDATION (HTTP 400)
# ==============================================================================
def test_api_robustness_invalid_request_400():
    """20. Verifies API rejects invalid capital, unsupported strategy, or invalid parameters."""
    # Negative capital
    r1 = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "momentum", "parameter_grid": {"lookback": [5]}, "initial_capital": -100.0},
    )
    assert r1.status_code == 400

    # Unsupported strategy
    r2 = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "deep_learning", "parameter_grid": {"layers": [3]}},
    )
    assert r2.status_code == 400

    # Empty grid
    r3 = client.post(
        "/market/nvidia/strategy/robustness",
        json={"strategy": "momentum", "parameter_grid": {}},
    )
    assert r3.status_code == 400
