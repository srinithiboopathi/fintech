"""
backend/tests/test_strategies.py

Comprehensive Test Suite for Step 9: Quantitative Trading Strategies.
Tests strategy dispatching, mathematical signal generation, zero look-ahead bias,
input validation, REST API routes, and integration with the Step 8 backtesting engine:
1. SMA Crossover
2. EMA Trend
3. Momentum
4. Mean Reversion
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import CleanHistoricalPoint
from app.services.strategies import (
    strategy_service,
    SMACrossoverStrategy,
    EMATrendStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
)
from app.utils.exceptions import (
    UnsupportedStrategyError,
    InvalidStrategyParameterError,
)

client = TestClient(app)


def make_clean_points(
    prices: list[float],
    start_date: str = "2026-01-01",
    asset: str = "TestAsset",
    symbol: str = "TEST"
) -> list[CleanHistoricalPoint]:
    """Helper to generate deterministic CleanHistoricalPoint instances."""
    base_dt = datetime.strptime(start_date, "%Y-%m-%d")
    points = []
    for i, p in enumerate(prices):
        dt_str = (base_dt + timedelta(days=i)).strftime("%Y-%m-%dT00:00:00Z")
        points.append(
            CleanHistoricalPoint(
                timestamp=dt_str,
                open=p,
                high=p * 1.01,
                low=p * 0.99,
                close=p,
                volume=1000.0,
                asset=asset,
                symbol=symbol,
                source="Twelve Data",
            )
        )
    return points


# ==============================================================================
# GENERAL STRATEGY TESTS (1 - 7)
# ==============================================================================
def test_strategy_dispatcher():
    """1. Verifies strategy dispatcher initializes all 4 core strategies."""
    supported = strategy_service.supported_strategies
    assert "sma_crossover" in supported
    assert "ema_trend" in supported
    assert "momentum" in supported
    assert "mean_reversion" in supported


def test_valid_strategy_names():
    """2. Verifies dispatcher retrieves instances for all valid strategy names."""
    assert isinstance(strategy_service.get_strategy("sma_crossover"), SMACrossoverStrategy)
    assert isinstance(strategy_service.get_strategy("ema_trend"), EMATrendStrategy)
    assert isinstance(strategy_service.get_strategy("momentum"), MomentumStrategy)
    assert isinstance(strategy_service.get_strategy("mean_reversion"), MeanReversionStrategy)


def test_invalid_strategy_name():
    """3. Verifies invalid strategy names raise UnsupportedStrategyError (HTTP 400)."""
    with pytest.raises(UnsupportedStrategyError) as exc:
        strategy_service.get_strategy("arbitrary_strategy")
    assert exc.value.status_code == 400
    assert exc.value.error_type == "UNSUPPORTED_STRATEGY"


def test_chronological_signals():
    """4. Verifies generated signal timestamps strictly preserve input ordering."""
    prices = [100.0 + i for i in range(15)]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("momentum", pts, {"lookback": 3})

    assert len(signals) == len(pts)
    for i in range(len(pts)):
        assert signals[i].timestamp == pts[i].timestamp


def test_allowed_signal_values():
    """5. Verifies every emitted signal directive is strictly in {'BUY', 'SELL', 'HOLD'}."""
    prices = [100.0, 102.0, 98.0, 105.0, 95.0, 110.0, 90.0, 100.0]
    pts = make_clean_points(prices)

    for strat in ["sma_crossover", "ema_trend", "momentum", "mean_reversion"]:
        signals, _ = strategy_service.generate_signals(strat, pts, {"short_period": 2, "long_period": 4, "ema_period": 3, "lookback": 3})
        for s in signals:
            assert s.signal in {"BUY", "SELL", "HOLD"}, f"Invalid signal {s.signal} in {strat}"


def test_insufficient_data():
    """6. Verifies insufficient observations safely emit HOLD without generating exceptions."""
    pts = make_clean_points([100.0, 105.0])
    signals, _ = strategy_service.generate_signals("sma_crossover", pts, {"short_period": 20, "long_period": 50})
    assert len(signals) == 2
    assert signals[0].signal == "HOLD"
    assert signals[1].signal == "HOLD"


def test_look_ahead_protection_general():
    """7. Verifies modifying future prices does NOT alter earlier signals."""
    base_prices = [100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 109.0, 107.0]
    pts_base = make_clean_points(base_prices)
    signals_base, _ = strategy_service.generate_signals("momentum", pts_base, {"lookback": 2})

    # Mutate prices at future indices (6 and 7)
    mutated_prices = list(base_prices)
    mutated_prices[6] = 500.0
    mutated_prices[7] = 10.0
    pts_mutated = make_clean_points(mutated_prices)
    signals_mutated, _ = strategy_service.generate_signals("momentum", pts_mutated, {"lookback": 2})

    # Signals for indices 0 to 5 MUST remain strictly identical
    for i in range(6):
        assert signals_base[i].signal == signals_mutated[i].signal
        assert signals_base[i].indicators == signals_mutated[i].indicators


# ==============================================================================
# SMA CROSSOVER TESTS (8 - 12)
# ==============================================================================
def test_sma_crossover_known_buy():
    """8. Verifies BUY is generated exactly when short SMA crosses above long SMA."""
    # Construct sequence where short SMA starts below long SMA, then crosses above
    # Short = 2, Long = 4
    # t0..t3=100 -> SMA2=100, SMA4=100
    # t4=90  -> SMA2=95, SMA4=97.5 (crosses below -> SELL)
    # t5=85  -> SMA2=87.5, SMA4=93.75 (stays below -> HOLD)
    # t6=120 -> SMA2=102.5, SMA4=98.75 (short crosses above long -> BUY)
    prices = [100.0, 100.0, 100.0, 100.0, 90.0, 85.0, 120.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "sma_crossover", pts, {"short_period": 2, "long_period": 4}
    )

    assert signals[5].signal == "HOLD"  # Short stayed below Long, no crossover
    assert signals[6].signal == "BUY"   # Short crossed above Long!


def test_sma_crossover_known_sell():
    """9. Verifies SELL is generated exactly when short SMA crosses below long SMA."""
    # Short = 2, Long = 4
    # t0..t3=100
    # t4=120 -> SMA2=110, SMA4=105 (short > long)
    # t5=80  -> SMA2=100, SMA4=100 (or below -> SELL)
    prices = [100.0, 100.0, 100.0, 100.0, 120.0, 70.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "sma_crossover", pts, {"short_period": 2, "long_period": 4}
    )

    assert signals[5].signal == "SELL"  # Short crossed below Long!


def test_sma_crossover_no_false_crossover():
    """10. Verifies HOLD is emitted when short SMA stays above long SMA without crossing."""
    # Continuously rising prices where short SMA is always above long SMA after initial cross
    prices = [100.0, 100.0, 100.0, 100.0, 110.0, 120.0, 130.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "sma_crossover", pts, {"short_period": 2, "long_period": 4}
    )

    assert signals[4].signal == "BUY"   # The crossing event
    assert signals[5].signal == "HOLD"  # Remains above; MUST NOT emit BUY again!
    assert signals[6].signal == "HOLD"  # Remains above; MUST NOT emit BUY again!


def test_sma_invalid_periods():
    """11. Verifies invalid periods (< 1 or < 2) raise HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("sma_crossover", pts, {"short_period": 0, "long_period": 10})

    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("sma_crossover", pts, {"short_period": 5, "long_period": 1})


def test_sma_short_less_than_long():
    """12. Verifies short_period >= long_period raises HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("sma_crossover", pts, {"short_period": 20, "long_period": 20})

    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("sma_crossover", pts, {"short_period": 30, "long_period": 10})


# ==============================================================================
# EMA TREND TESTS (13 - 16)
# ==============================================================================
def test_ema_trend_buy():
    """13. Verifies close > EMA emits BUY signal."""
    # EMA period = 3
    # Seed at index 2: SMA(100, 100, 100) = 100.0
    # index 3: price jumps to 110.0 -> close (110) > EMA -> BUY
    prices = [100.0, 100.0, 100.0, 110.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("ema_trend", pts, {"ema_period": 3})

    assert signals[3].signal == "BUY"
    assert signals[3].indicators["ema"] is not None
    assert signals[3].close > signals[3].indicators["ema"]


def test_ema_trend_sell():
    """14. Verifies close < EMA emits SELL signal."""
    prices = [100.0, 100.0, 100.0, 90.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("ema_trend", pts, {"ema_period": 3})

    assert signals[3].signal == "SELL"
    assert signals[3].close < signals[3].indicators["ema"]


def test_ema_trend_equal_hold():
    """15. Verifies close == EMA emits HOLD signal."""
    prices = [100.0, 100.0, 100.0, 100.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("ema_trend", pts, {"ema_period": 3})

    assert signals[3].signal == "HOLD"
    assert signals[3].close == signals[3].indicators["ema"]


def test_ema_invalid_period():
    """16. Verifies ema_period <= 0 raises HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("ema_trend", pts, {"ema_period": 0})


# ==============================================================================
# MOMENTUM TESTS (17 - 20)
# ==============================================================================
def test_momentum_buy():
    """17. Verifies positive momentum (close_t > close_{t-lookback}) emits BUY."""
    # Lookback = 2
    # t0=100, t1=100, t2=110 -> momentum = 110/100 - 1 = +0.10 -> BUY
    prices = [100.0, 100.0, 110.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("momentum", pts, {"lookback": 2})

    assert signals[2].signal == "BUY"
    assert signals[2].indicators["momentum"] == 0.10


def test_momentum_sell():
    """18. Verifies negative momentum (close_t < close_{t-lookback}) emits SELL."""
    prices = [100.0, 100.0, 90.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("momentum", pts, {"lookback": 2})

    assert signals[2].signal == "SELL"
    assert signals[2].indicators["momentum"] == -0.10


def test_momentum_zero_hold():
    """19. Verifies zero momentum (close_t == close_{t-lookback}) emits HOLD."""
    prices = [100.0, 100.0, 100.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals("momentum", pts, {"lookback": 2})

    assert signals[2].signal == "HOLD"
    assert signals[2].indicators["momentum"] == 0.0


def test_momentum_invalid_lookback():
    """20. Verifies lookback <= 0 raises HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("momentum", pts, {"lookback": 0})


# ==============================================================================
# MEAN REVERSION TESTS (21 - 26)
# ==============================================================================
def test_mean_reversion_lower_threshold_buy():
    """21. Verifies z_score <= -entry_threshold emits BUY (oversold)."""
    # lookback = 4, threshold = 1.0
    # prices: [100, 100, 100, 70]
    # mean = (100+100+100+70)/4 = 92.5
    # diffs = [7.5, 7.5, 7.5, -22.5]
    # var = (3 * 56.25 + 506.25) / 3 = (168.75 + 506.25)/3 = 225 -> std = 15.0
    # z = (70 - 92.5) / 15.0 = -22.5 / 15 = -1.5 <= -1.0 -> BUY
    prices = [100.0, 100.0, 100.0, 70.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "mean_reversion", pts, {"lookback": 4, "entry_threshold": 1.0}
    )

    assert signals[3].signal == "BUY"
    assert signals[3].indicators["z_score"] == -1.5


def test_mean_reversion_upper_threshold_sell():
    """22. Verifies z_score >= entry_threshold emits SELL (overbought)."""
    # prices: [100, 100, 100, 130] -> z = +1.5 >= 1.0 -> SELL
    prices = [100.0, 100.0, 100.0, 130.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "mean_reversion", pts, {"lookback": 4, "entry_threshold": 1.0}
    )

    assert signals[3].signal == "SELL"
    assert signals[3].indicators["z_score"] == 1.5


def test_mean_reversion_inside_threshold_hold():
    """23. Verifies -threshold < z_score < threshold emits HOLD."""
    prices = [100.0, 100.0, 100.0, 102.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "mean_reversion", pts, {"lookback": 4, "entry_threshold": 2.0}
    )

    assert signals[3].signal == "HOLD"
    assert signals[3].indicators["z_score"] == 1.5


def test_mean_reversion_zero_std_handling():
    """24. Verifies flat series with zero standard deviation emits HOLD safely."""
    prices = [100.0, 100.0, 100.0, 100.0]
    pts = make_clean_points(prices)
    signals, _ = strategy_service.generate_signals(
        "mean_reversion", pts, {"lookback": 4, "entry_threshold": 1.0}
    )

    assert signals[3].signal == "HOLD"
    assert signals[3].indicators["z_score"] == 0.0


def test_mean_reversion_invalid_lookback():
    """25. Verifies lookback < 2 raises HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("mean_reversion", pts, {"lookback": 1, "entry_threshold": 1.0})


def test_mean_reversion_invalid_threshold():
    """26. Verifies entry_threshold <= 0 raises HTTP 400."""
    pts = make_clean_points([100.0, 105.0])
    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("mean_reversion", pts, {"lookback": 4, "entry_threshold": 0.0})

    with pytest.raises(InvalidStrategyParameterError):
        strategy_service.generate_signals("mean_reversion", pts, {"lookback": 4, "entry_threshold": -0.5})


# ==============================================================================
# API ROUTE TESTS (27 - 33)
# ==============================================================================
def test_api_strategy_signals_endpoint():
    """27. Verifies POST /market/{asset}/strategy/signals endpoint returns HTTP 200."""
    payload = {
        "strategy": "momentum",
        "parameters": {"lookback": 5}
    }
    r = client.post("/market/nvidia/strategy/signals", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["asset"] == "NVIDIA"
    assert data["symbol"] == "NVDA"
    assert data["strategy"] == "momentum"
    assert len(data["signals"]) > 0


def test_api_sma_strategy():
    """28. Verifies SMA Crossover strategy signal generation via API."""
    payload = {
        "strategy": "sma_crossover",
        "parameters": {"short_period": 5, "long_period": 15}
    }
    r = client.post("/market/nvidia/strategy/signals", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "sma_crossover"
    assert data["parameters"]["short_period"] == 5
    assert data["parameters"]["long_period"] == 15


def test_api_ema_strategy():
    """29. Verifies EMA Trend strategy signal generation via API."""
    payload = {
        "strategy": "ema_trend",
        "parameters": {"ema_period": 10}
    }
    r = client.post("/market/bitcoin/strategy/signals", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "ema_trend"
    assert data["symbol"] == "BTC/USD"


def test_api_momentum_strategy():
    """30. Verifies Momentum strategy signal generation via API."""
    payload = {
        "strategy": "momentum",
        "parameters": {"lookback": 5}
    }
    r = client.post("/market/gold/strategy/signals", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "momentum"
    assert data["symbol"] == "XAU/USD"


def test_api_mean_reversion_strategy():
    """31. Verifies Mean Reversion strategy signal generation via API."""
    payload = {
        "strategy": "mean_reversion",
        "parameters": {"lookback": 10, "entry_threshold": 1.2}
    }
    r = client.post("/market/nvidia/strategy/signals", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "mean_reversion"
    assert data["parameters"]["entry_threshold"] == 1.2


def test_api_invalid_strategy_400():
    """32. Verifies invalid strategy returns HTTP 400."""
    payload = {
        "strategy": "non_existent_strat",
        "parameters": {}
    }
    r = client.post("/market/nvidia/strategy/signals", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "UNSUPPORTED_STRATEGY"


def test_api_invalid_parameters_400():
    """33. Verifies invalid strategy parameters return HTTP 400."""
    payload = {
        "strategy": "sma_crossover",
        "parameters": {"short_period": 50, "long_period": 20}  # short >= long
    }
    r = client.post("/market/nvidia/strategy/signals", json=payload)
    assert r.status_code == 400
    assert r.json()["error"] == "INVALID_STRATEGY_PARAMETER"


# ==============================================================================
# BACKTEST INTEGRATION TESTS (34 - 40)
# ==============================================================================
def test_sma_backtest_integration():
    """34. Verifies SMA Crossover backtest through Step 8 engine."""
    payload = {
        "strategy": "sma_crossover",
        "parameters": {"short_period": 5, "long_period": 15},
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0
    }
    r = client.post("/market/nvidia/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "sma_crossover"
    assert data["performance"]["initial_capital"] == 100000.0
    assert data["performance"]["final_portfolio_value"] > 0
    assert len(data["equity_curve"]) > 0


def test_ema_backtest_integration():
    """35. Verifies EMA Trend backtest through Step 8 engine."""
    payload = {
        "strategy": "ema_trend",
        "parameters": {"ema_period": 10},
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0
    }
    r = client.post("/market/bitcoin/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "ema_trend"
    assert data["symbol"] == "BTC/USD"
    assert data["performance"]["final_portfolio_value"] > 0


def test_momentum_backtest_integration():
    """36. Verifies Momentum backtest through Step 8 engine."""
    payload = {
        "strategy": "momentum",
        "parameters": {"lookback": 5},
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0
    }
    r = client.post("/market/gold/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "momentum"
    assert data["symbol"] == "XAU/USD"


def test_mean_reversion_backtest_integration():
    """37. Verifies Mean Reversion backtest through Step 8 engine."""
    payload = {
        "strategy": "mean_reversion",
        "parameters": {"lookback": 10, "entry_threshold": 1.0},
        "initial_capital": 100000.0,
        "transaction_cost_rate": 0.001,
        "allocation_fraction": 1.0
    }
    r = client.post("/market/nvidia/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["strategy"] == "mean_reversion"
    assert data["performance"]["total_trades"] >= 0


def test_backtest_benchmark_returned():
    """38. Verifies Buy & Hold benchmark is returned in strategy backtest."""
    payload = {
        "strategy": "momentum",
        "parameters": {"lookback": 5},
    }
    r = client.post("/market/nvidia/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "benchmark" in data
    assert data["benchmark"]["benchmark_name"] == "Buy & Hold"
    assert len(data["benchmark"]["equity_curve"]) > 0


def test_backtest_transaction_costs_applied():
    """39. Verifies transaction fees are tracked and deducted in strategy backtest."""
    payload = {
        "strategy": "ema_trend",
        "parameters": {"ema_period": 5},
        "transaction_cost_rate": 0.005,  # 0.5%
    }
    r = client.post("/market/nvidia/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    if data["performance"]["total_trades"] > 0:
        assert data["performance"]["total_fees_paid"] > 0


def test_backtest_next_observation_execution_preserved():
    """40. Verifies signals at t are executed causally at t+1 by Step 8 engine."""
    payload = {
        "strategy": "momentum",
        "parameters": {"lookback": 5},
    }
    r = client.post("/market/nvidia/strategy/backtest", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "Next-Observation" in data["execution_model"]
    # First observation action MUST be NONE because no trade can execute at t=0
    assert data["equity_curve"][0]["executed_action"] == "NONE"
