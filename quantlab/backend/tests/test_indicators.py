import pytest
from app.quant.indicators import QuantIndicators

def test_sma_calculation():
    prices = [10.0, 20.0, 30.0, 40.0, 50.0]
    sma_3 = QuantIndicators.sma(prices, 3)
    assert len(sma_3) == 5
    assert sma_3[0] is None
    assert sma_3[1] is None
    assert sma_3[2] == 20.0
    assert sma_3[3] == 30.0
    assert sma_3[4] == 40.0

def test_sma_configurable_periods():
    prices = [float(i) for i in range(1, 250)]
    sma_20 = QuantIndicators.sma(prices, 20)
    sma_50 = QuantIndicators.sma(prices, 50)
    sma_200 = QuantIndicators.sma(prices, 200)
    
    assert sma_20[18] is None
    assert sma_20[19] is not None
    assert sma_50[49] is not None
    assert sma_200[199] is not None
    assert len(sma_20) == len(prices)

def test_ema_calculation():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0]
    ema_3 = QuantIndicators.ema(prices, 3)
    assert len(ema_3) == 6
    assert ema_3[2] == 11.0 # Initial SMA seed
    assert ema_3[3] is not None
    assert ema_3[3] > 11.0
    # Values should strictly follow exponential smoothing
    assert ema_3[-1] > ema_3[-2]

def test_rsi_bounds():
    prices = [10.0 + i * 0.5 for i in range(30)]
    rsi_vals = QuantIndicators.rsi(prices, 14)
    valid_rsi = [v for v in rsi_vals if v is not None]
    assert len(valid_rsi) > 0
    for val in valid_rsi:
        assert 0.0 <= val <= 100.0

def test_bollinger_bands():
    prices = [100.0 + (i % 5) for i in range(30)]
    bb = QuantIndicators.bollinger_bands(prices, 20, 2.0)
    assert "upper" in bb and "lower" in bb and "middle" in bb
    for i in range(20, 30):
        assert bb["upper"][i] >= bb["middle"][i] >= bb["lower"][i]

def test_macd():
    prices = [100.0 + (i * 0.5) for i in range(50)]
    macd_res = QuantIndicators.macd(prices, 12, 26, 9)
    assert "macd" in macd_res and "signal" in macd_res and "hist" in macd_res
    assert len(macd_res["macd"]) == 50
    assert len(macd_res["signal"]) == 50

def test_atr():
    bars = []
    for i in range(30):
        bars.append({
            "high": 105.0 + i,
            "low": 95.0 + i,
            "close": 100.0 + i
        })
    atr_vals = QuantIndicators.atr(bars, 14)
    assert len(atr_vals) == 30
    assert atr_vals[14] is not None
    assert atr_vals[14] > 0.0
