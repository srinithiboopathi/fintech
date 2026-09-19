import pytest
from app.quant.volatility import VolatilityMetrics
from app.quant.sharpe import RiskAdjustedMetrics
from app.quant.drawdown import DrawdownAnalysis

def test_volatility_metrics():
    rets = [0.01, -0.005, 0.02, -0.01, 0.015, 0.008, -0.002, 0.012]
    ann_vol = VolatilityMetrics.annualized_volatility(rets)
    downside_vol = VolatilityMetrics.downside_volatility(rets)
    assert ann_vol > 0.0
    assert downside_vol >= 0.0
    assert downside_vol <= ann_vol

def test_sharpe_and_sortino():
    rets = [0.01, -0.005, 0.02, -0.01, 0.015, 0.008, -0.002, 0.012]
    sharpe_default = RiskAdjustedMetrics.sharpe_ratio(rets, risk_free_rate=0.035)
    sharpe_zero_rf = RiskAdjustedMetrics.sharpe_ratio(rets, risk_free_rate=0.0)
    sortino = RiskAdjustedMetrics.sortino_ratio(rets, risk_free_rate=0.035)
    
    assert isinstance(sharpe_default, float)
    assert isinstance(sharpe_zero_rf, float)
    assert sharpe_zero_rf > sharpe_default # Higher Sharpe with zero Rf
    assert isinstance(sortino, float)

def test_drawdown_calculation():
    equity = [100.0, 105.0, 110.0, 99.0, 95.0, 102.0, 115.0]
    underwater, max_dd, duration = DrawdownAnalysis.calculate_drawdowns(equity)
    assert len(underwater) == 7
    expected_dd = (110.0 - 95.0) / 110.0
    assert round(max_dd, 4) == round(expected_dd, 4)
    assert duration >= 1

def test_calmar_ratio():
    calmar = RiskAdjustedMetrics.calmar_ratio(cagr=0.20, max_drawdown=0.10)
    assert round(calmar, 2) == 2.0

def test_historical_var_and_cvar():
    rets = [-0.05, -0.03, -0.01, 0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
    var_95 = VolatilityMetrics.value_at_risk_historical(rets, confidence=0.95)
    cvar_95 = VolatilityMetrics.conditional_var_historical(rets, confidence=0.95)
    assert var_95 > 0.0
    assert cvar_95 >= var_95
