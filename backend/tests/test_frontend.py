"""
Automated Integration and Sanity Tests for Step 12 Frontend Dashboard.
Verifies static asset serving, DOM structure, API client route coverage, and absence of hardcoded mock data or secrets.
"""

import os
import re
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@pytest.mark.asyncio
async def test_viewer_endpoint_serves_html():
    """Verify /viewer returns 200 with Quantexa master application shell."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/viewer")

    assert response.status_code == 200
    html = response.text
    assert "QUANTEXA" in html
    assert "Quantitative Multi-Asset Financial Intelligence Platform" in html
    assert "Chart.js" in html or "chart.umd.min.js" in html


@pytest.mark.asyncio
async def test_static_assets_served():
    """Verify CSS and JS modular assets are served by FastAPI static mount."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for path in ["/css/styles.css", "/js/api.js", "/js/charts.js", "/js/app.js"]:
            res = await ac.get(path)
            assert res.status_code == 200, f"Failed to serve {path}"
            assert len(res.text) > 500, f"Asset {path} unexpectedly small"


def test_frontend_files_exist():
    """Verify required frontend structure exists."""
    assert (FRONTEND_DIR / "index.html").exists()
    assert (FRONTEND_DIR / "css" / "styles.css").exists()
    assert (FRONTEND_DIR / "js" / "api.js").exists()
    assert (FRONTEND_DIR / "js" / "charts.js").exists()
    assert (FRONTEND_DIR / "js" / "app.js").exists()


def test_dom_sections_and_canvases_present():
    """Verify that all required view sections and chart canvases exist in index.html."""
    html_content = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

    # Required navigation view panels
    required_views = [
        "view-overview",
        "view-market",
        "view-indicators",
        "view-risk",
        "view-correlation",
        "view-strategies",
        "view-backtest",
        "view-comparison",
        "view-robustness",
        "view-regimes",
        "view-system",
        "view-ai",
    ]
    for view_id in required_views:
        assert f'id="{view_id}"' in html_content, f"Missing view section: {view_id}"

    # Required Chart.js canvases
    required_canvases = [
        "market-price-chart",
        "indicators-chart",
        "returns-bar-chart",
        "volatility-line-chart",
        "risk-drawdown-chart",
        "rolling-corr-chart",
        "backtest-equity-chart",
        "regime-donut-chart",
    ]
    for canvas_id in required_canvases:
        assert f'id="{canvas_id}"' in html_content, f"Missing chart canvas: {canvas_id}"

    # Required controls
    required_controls = [
        "btn-global-refresh",
        "select-corr-pair",
        "select-corr-window",
        "backtest-strat-select",
        "robustness-strat-select",
        "btn-floating-ai",
        "ai-chat-drawer",
        "drawer-ai-chat-input",
        "btn-drawer-ai-send",
        "btn-drawer-clear-chat",
    ]
    for ctrl_id in required_controls:
        assert f'id="{ctrl_id}"' in html_content, f"Missing interactive control: {ctrl_id}"


def test_ai_suggested_prompts_present():
    """Verify all 6 required jury suggested prompts are present in index.html."""
    html_content = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    required_prompts = [
        "Analyze NVDA",
        "Compare Bitcoin and Gold correlation",
        "Explain NVDA's Sharpe ratio",
        "How did SMA Crossover perform?",
        "What is the current market regime?",
        "Explain the latest drawdown",
    ]
    for prompt in required_prompts:
        assert prompt in html_content, f"Missing required suggested jury question: {prompt}"


def test_api_client_route_coverage():
    """Verify that js/api.js implements calls to all required backend API endpoints."""
    api_js = (FRONTEND_DIR / "js" / "api.js").read_text(encoding="utf-8")

    expected_routes = [
        "/health",
        "/assets",
        "/market/${asset}/latest",
        "/market/${asset}/historical",
        "/market/${asset}/data",
        "/market/${asset}/indicators",
        "/market/${asset}/risk-metrics",
        "/market/${asset}/risk-analysis",
        "/market/correlation",
        "/market/correlation/rolling",
        "/market/${asset}/strategy/signals",
        "/market/${asset}/strategy/backtest",
        "/market/${asset}/strategy/compare",
        "/market/${asset}/strategy/robustness",
        "/market/${asset}/regimes",
        "/market/${asset}/regimes/summary",
        "/market/${asset}/regimes/performance",
        "/ai/chat",
        "/ai/status",
    ]

    for route in expected_routes:
        assert route in api_js, f"API client missing route signature: {route}"


def test_no_hardcoded_secrets_or_keys():
    """Verify that no real API keys or sensitive secrets are stored in frontend files."""
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f.endswith((".html", ".js", ".css")):
                content = Path(root, f).read_text(encoding="utf-8")
                # Look for suspicious raw 32-char hex or alphanumeric keys
                assert "TWELVE_DATA_API_KEY=" not in content
                assert "ALPHA_VANTAGE_API_KEY=" not in content
                assert "AI_API_KEY=" not in content
                assert not re.search(r"['\"][a-f0-9]{32}['\"]", content), f"Suspicious API key in {f}"


def test_no_mock_data_generators():
    """Verify that frontend does not generate random/simulated prices or fake strategy signals."""
    for root, _, files in os.walk(FRONTEND_DIR):
        for f in files:
            if f.endswith(".js"):
                content = Path(root, f).read_text(encoding="utf-8")
                assert "Math.random() *" not in content, f"Detected pseudo-random math in {f}"
                assert "fakePrice" not in content
                assert "mockSignal" not in content
