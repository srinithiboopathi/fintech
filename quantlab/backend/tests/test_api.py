import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    resp_api = client.get("/api/health")
    assert resp_api.status_code == 200
    assert resp_api.json() == {"status": "ok"}

def test_market_assets():
    response = client.get("/api/market/assets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    symbols = [item["symbol"] for item in data]
    assert "GC=F" in symbols
    assert "BTC-USD" in symbols
    assert "NVDA" in symbols

def test_market_history():
    response = client.get("/api/market/NVDA/history")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "bars" in data
    assert data["total_bars"] > 0
    first_bar = data["bars"][0]
    assert "open" in first_bar and "close" in first_bar and "high" in first_bar and "low" in first_bar

def test_analytics_sma():
    response = client.get("/api/analytics/NVDA/sma?period=20")
    assert response.status_code == 200
    data = response.json()
    assert data["indicator"] == "SMA"
    assert data["period"] == 20
    assert len(data["series"]) > 0

def test_analytics_ema():
    response = client.get("/api/analytics/NVDA/ema?period=20")
    assert response.status_code == 200
    data = response.json()
    assert data["indicator"] == "EMA"
    assert data["period"] == 20
    assert len(data["series"]) > 0

def test_analytics_returns():
    response = client.get("/api/analytics/NVDA/returns")
    assert response.status_code == 200
    data = response.json()
    assert "total_cumulative_return" in data
    assert "cagr" in data
    assert len(data["series"]) > 0

def test_analytics_volatility():
    response = client.get("/api/analytics/NVDA/volatility?window=30")
    assert response.status_code == 200
    data = response.json()
    assert "annualized_volatility" in data
    assert "downside_volatility" in data
    assert data["window"] == 30

def test_analytics_sharpe():
    response = client.get("/api/analytics/NVDA/sharpe?risk_free_rate=0.035&window=60")
    assert response.status_code == 200
    data = response.json()
    assert "sharpe_ratio" in data
    assert "sortino_ratio" in data
    assert "calmar_ratio" in data

def test_analytics_drawdown():
    response = client.get("/api/analytics/NVDA/drawdown")
    assert response.status_code == 200
    data = response.json()
    assert "max_drawdown_pct" in data
    assert "max_drawdown_duration_days" in data
    assert len(data["series"]) > 0

def test_analytics_indicators():
    response = client.get("/api/analytics/indicators/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert "sma_20" in data
    assert "rsi" in data
    assert "bb_upper" in data
    assert "macd" in data

def test_analytics_risk():
    response = client.get("/api/analytics/risk/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert "annualized_volatility" in data
    assert "sharpe_ratio" in data
    assert "var_95" in data
    assert "cvar_95" in data

def test_correlation_matrix():
    response = client.get("/api/correlation/matrix?method=pearson")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    assert "matrix" in data
    assert len(data["matrix"]) == 3
    assert len(data["matrix"][0]) == 3
    assert data["matrix"][0][0] == 1.0

def test_correlation_rolling():
    response = client.get("/api/correlation/rolling?asset_a=BTC-USD&asset_b=GC=F&window=30")
    assert response.status_code == 200
    data = response.json()
    assert data["asset_a"] == "BTC-USD"
    assert data["asset_b"] == "GC=F"
    assert data["window"] == 30
    assert len(data["series"]) > 0

def test_strategies_list():
    response = client.get("/api/strategies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    strategy_ids = [s["id"] for s in data]
    assert "sma_crossover" in strategy_ids
    assert "ema_trend" in strategy_ids
    assert "momentum" in strategy_ids
    assert "mean_reversion" in strategy_ids

def test_backtest_run():
    payload = {
        "symbol": "NVDA",
        "strategy_id": "sma_crossover",
        "initial_capital": 100000.0,
        "parameters": {
            "fast_period": 20,
            "slow_period": 50,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15
        },
        "position_sizing": "percent_equity",
        "position_size_value": 0.95,
        "commission_bps": 5.0,
        "slippage_pct": 0.0005
    }
    response = client.post("/api/backtest/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_return_pct" in data
    assert "sharpe_ratio" in data
    assert "max_drawdown_pct" in data
    assert "equity_curve" in data
    assert "benchmark" in data
    assert data["benchmark"]["total_return_pct"] is not None
    assert "alpha_excess_return_pct" in data["benchmark"]

def test_research_report():
    response = client.get("/api/reports/generate/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "performance_metrics" in data
    assert "correlation_profile" in data
    assert "baseline_backtest" in data

def test_market_regimes():
    response = client.get("/api/regimes/detect/NVDA")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NVDA"
    assert "current_regime" in data
    assert "distribution_pct" in data

def test_robustness_monte_carlo():
    response = client.get("/api/robustness/monte-carlo/NVDA?simulations=100&horizon=120")
    assert response.status_code == 200
    data = response.json()
    assert "p50_equity_curve" in data
    assert "metrics" in data
    assert "terminal_wealth_p50" in data["metrics"]
