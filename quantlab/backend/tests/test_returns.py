import pytest
import math
from app.quant.returns import ReturnMetrics

def test_daily_percentage_returns():
    prices = [100.0, 105.0, 102.0, 110.0]
    rets = ReturnMetrics.daily_returns(prices)
    assert len(rets) == 4
    assert rets[0] == 0.0
    assert round(rets[1], 4) == 0.05
    assert round(rets[2], 4) == round((102.0 - 105.0) / 105.0, 4)
    assert round(rets[3], 4) == round((110.0 - 102.0) / 102.0, 4)

def test_log_returns():
    prices = [100.0, 110.0, 121.0]
    log_rets = ReturnMetrics.log_returns(prices)
    assert len(log_rets) == 3
    assert log_rets[0] == 0.0
    assert round(log_rets[1], 4) == round(math.log(1.1), 4)

def test_cumulative_return():
    prices = [100.0, 120.0, 150.0]
    total_cum = ReturnMetrics.cumulative_return(prices)
    assert round(total_cum, 4) == 0.50

def test_cumulative_returns_series():
    rets = [0.0, 0.10, -0.05, 0.20]
    cum_series = ReturnMetrics.cumulative_returns_series(rets)
    assert len(cum_series) == 4
    assert cum_series[0] == 0.0
    assert round(cum_series[1], 4) == 0.10
    assert round(cum_series[2], 4) == round((1.10 * 0.95) - 1.0, 4)

def test_cagr():
    # Double in 504 trading days (~2 years)
    cagr_val = ReturnMetrics.cagr(100.0, 200.0, 504)
    expected = (200.0 / 100.0) ** (252.0 / 504.0) - 1.0
    assert round(cagr_val, 4) == round(expected, 4)
