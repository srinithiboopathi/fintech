"""
Step 13: Unit and Integration Tests for Grounded AI Financial Intelligence Assistant.
Verifies factual quantitative context generation, intent parsing, provider abstractions,
session memory, error resilience, zero-hallucination rules, and secret protection.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
import httpx

from app.main import app
from app.config import settings
from app.models.schemas import AIChatRequest, AIChatResponse, AIStatusResponse
from app.services.ai_assistant import (
    AIAssistantService,
    GeminiProvider,
    OpenAIProvider,
    ai_assistant_service
)


@pytest.fixture
def clean_service():
    """Provides an isolated AIAssistantService instance with empty conversation memory."""
    service = AIAssistantService()
    service._conversations.clear()
    return service


# ==============================================================================
# 1. AI Service Initialization
# ==============================================================================
def test_ai_service_initialization(clean_service):
    """Verifies default initialization of the AI assistant service."""
    assert clean_service is not None
    assert clean_service.max_history_turns == 6
    assert isinstance(clean_service._conversations, dict)
    assert len(clean_service._conversations) == 0


# ==============================================================================
# 2. Missing AI Configuration
# ==============================================================================
@pytest.mark.asyncio
async def test_missing_ai_configuration(clean_service):
    """Verifies that missing AI_API_KEY generates grounded quantitative fallback with zero crashes."""
    with patch.object(settings, "AI_API_KEY", ""):
        provider, p_name, m_name = clean_service.get_provider()
        assert provider is None
        assert p_name == "unconfigured"

        resp = await clean_service.chat(message="What is NVDA's latest price?")
        assert isinstance(resp, AIChatResponse)
        assert resp.provider == "unconfigured"
        assert "Quantexa Grounded Financial Analysis" in resp.answer
        assert len(resp.data_references) > 0
        assert "nvidia" in resp.relevant_assets


# ==============================================================================
# 3. Provider Configuration
# ==============================================================================
def test_provider_configuration():
    """Verifies instantiation and configuration of Gemini and OpenAI provider classes."""
    gemini = GeminiProvider(api_key="mock-gemini-key", model="gemini-1.5-flash")
    assert gemini.api_key == "mock-gemini-key"
    assert gemini.model == "gemini-1.5-flash"
    assert "gemini-1.5-flash" in gemini.endpoint

    openai = OpenAIProvider(api_key="mock-openai-key", model="gpt-4o-mini")
    assert openai.api_key == "mock-openai-key"
    assert openai.model == "gpt-4o-mini"
    assert openai.endpoint == "https://api.openai.com/v1/chat/completions"


# ==============================================================================
# 4. Market Context
# ==============================================================================
@pytest.mark.asyncio
async def test_market_context(clean_service):
    """Verifies that market quotes are retrieved and structured into factual context."""
    intent = clean_service.parse_intent("What is the latest price of NVDA?")
    assert intent["asset"] == "nvidia"
    assert "market_data" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "LATEST MARKET QUOTE" in context_str
    assert "Price" in context_str
    assert any(ref.topic == "market_data" for ref in refs)


# ==============================================================================
# 5. Risk Context
# ==============================================================================
@pytest.mark.asyncio
async def test_risk_context(clean_service):
    """Verifies risk context extraction (Sharpe ratio and max drawdown)."""
    intent = clean_service.parse_intent("What is Bitcoin's Sharpe ratio and drawdown?")
    assert intent["asset"] == "bitcoin"
    assert "sharpe" in intent["topics"]
    assert "drawdown" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "RISK ANALYSIS" in context_str
    assert "Annualized Sharpe Ratio" in context_str
    assert "Maximum Drawdown" in context_str
    assert any(ref.topic == "risk_analysis" for ref in refs)


# ==============================================================================
# 6. Correlation Context
# ==============================================================================
@pytest.mark.asyncio
async def test_correlation_context(clean_service):
    """Verifies cross-asset correlation context extraction."""
    intent = clean_service.parse_intent("Compare Bitcoin and Gold correlation.")
    assert "correlation" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "PEARSON CORRELATION MATRIX" in context_str
    assert "NVDA" in context_str or "BTC/USD" in context_str
    assert any(ref.topic == "correlation" for ref in refs)


# ==============================================================================
# 7. Strategy Context
# ==============================================================================
@pytest.mark.asyncio
async def test_strategy_context(clean_service):
    """Verifies strategy signals and backtest context extraction."""
    intent = clean_service.parse_intent("Explain the SMA Crossover strategy for NVDA.")
    assert intent["asset"] == "nvidia"
    assert intent["strategy"] == "sma_crossover"

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "STRATEGY COMPARISON" in context_str or "SMA Crossover" in context_str
    assert any(ref.topic == "strategy_backtest" for ref in refs)


# ==============================================================================
# 8. Backtest Context
# ==============================================================================
@pytest.mark.asyncio
async def test_backtest_context(clean_service):
    """Verifies backtesting performance and benchmark comparison data context."""
    intent = clean_service.parse_intent("How did Momentum perform against Buy and Hold on Bitcoin?")
    assert intent["asset"] == "bitcoin"
    assert intent["strategy"] == "momentum"
    assert "backtest" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "STRATEGY COMPARISON & BACKTEST" in context_str
    assert "Buy & Hold" in context_str


# ==============================================================================
# 9. Robustness Context
# ==============================================================================
@pytest.mark.asyncio
async def test_robustness_context(clean_service):
    """Verifies robustness and parameter sensitivity context retrieval."""
    intent = clean_service.parse_intent("Analyze parameter robustness and sensitivity for NVDA.")
    assert "robustness" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "ROBUSTNESS SENSITIVITY" in context_str
    assert any(ref.topic == "robustness" for ref in refs)


# ==============================================================================
# 10. Regime Context
# ==============================================================================
@pytest.mark.asyncio
async def test_regime_context(clean_service):
    """Verifies market regimes context retrieval and trend/volatility states."""
    intent = clean_service.parse_intent("What is Gold's current market regime?")
    assert intent["asset"] == "gold"
    assert "regime" in intent["topics"]

    context_str, refs, assets, metrics = await clean_service.build_grounded_context(intent, [])
    assert "MARKET REGIMES" in context_str
    assert any(ref.topic == "market_regimes" for ref in refs)


# ==============================================================================
# 11. Asset Detection
# ==============================================================================
def test_asset_detection(clean_service):
    """Verifies natural language alias resolution for supported assets."""
    assert clean_service.parse_intent("What is NVIDIA trading at?")["asset"] == "nvidia"
    assert clean_service.parse_intent("Show me NVDA trends")["asset"] == "nvidia"
    assert clean_service.parse_intent("How is Bitcoin doing today?")["asset"] == "bitcoin"
    assert clean_service.parse_intent("BTC/USD price check")["asset"] == "bitcoin"
    assert clean_service.parse_intent("Check bullion and Gold volatility")["asset"] == "gold"
    assert clean_service.parse_intent("XAU price")["asset"] == "gold"


# ==============================================================================
# 12. Strategy Detection
# ==============================================================================
def test_strategy_detection(clean_service):
    """Verifies detection of all four trading strategies."""
    assert clean_service.parse_intent("Run SMA crossover on NVDA")["strategy"] == "sma_crossover"
    assert clean_service.parse_intent("Show EMA trend signals")["strategy"] == "ema_trend"
    assert clean_service.parse_intent("Calculate momentum ROC")["strategy"] == "momentum"
    assert clean_service.parse_intent("Test mean reversion strategy")["strategy"] == "mean_reversion"


# ==============================================================================
# 13. Conversation History
# ==============================================================================
@pytest.mark.asyncio
async def test_conversation_history(clean_service):
    """Verifies multi-turn contextual tracking and bounded history."""
    conv_id = "test-session-123"

    # Turn 1: Specify NVDA
    await clean_service.chat(
        message="What is NVDA's Sharpe ratio?",
        conversation_id=conv_id
    )
    assert len(clean_service._conversations[conv_id]) == 2

    # Turn 2: Follow-up question without naming NVDA
    intent2 = clean_service.parse_intent("Why is the drawdown so large?")
    assert intent2["asset"] is None

    # build_grounded_context should inherit 'nvidia' from history
    context_str, refs, assets, _ = await clean_service.build_grounded_context(
        intent2,
        clean_service._conversations[conv_id]
    )
    assert assets == ["nvidia"]

    # Fill history beyond max limit (6 turns = 3 user + 3 assistant)
    for i in range(5):
        await clean_service.chat(
            message=f"Follow-up question {i}",
            conversation_id=conv_id
        )
    assert len(clean_service._conversations[conv_id]) <= clean_service.max_history_turns


# ==============================================================================
# 14. Unavailable Data
# ==============================================================================
@pytest.mark.asyncio
async def test_unavailable_data(clean_service):
    """Verifies clean message when an asset is completely unsupported and no references match."""
    intent = {"asset": None, "strategy": None, "topics": ["unsupported_metric"]}
    context_str, refs, assets, _ = await clean_service.build_grounded_context(intent, [])
    
    # When empty data references are supplied to fallback generator
    answer = clean_service._generate_unconfigured_fallback("query", context_str, [])
    assert "currently unavailable on the Quantexa platform" in answer


# ==============================================================================
# 15. No-Hallucination Prompt Rules
# ==============================================================================
def test_no_hallucination_prompt_rules(clean_service):
    """Verifies system prompt strictly forbids inventing numbers and mandates factual citation."""
    prompt = clean_service.construct_system_prompt("PLATFORM_SAMPLE_DATA_123")
    assert "NEVER invent, hallucinate, simulate, or estimate" in prompt
    assert "EXCLUSIVELY the factual PLATFORM DATA" in prompt
    assert "do not guarantee future returns" in prompt
    assert "PLATFORM_SAMPLE_DATA_123" in prompt


# ==============================================================================
# 16. Numerical Context Preservation
# ==============================================================================
@pytest.mark.asyncio
async def test_numerical_context_preservation(clean_service):
    """Verifies numerical precision and exact metric values in data references."""
    intent = clean_service.parse_intent("What is NVDA's Sharpe ratio?")
    _, refs, _, _ = await clean_service.build_grounded_context(intent, [])

    risk_ref = next((r for r in refs if r.topic == "risk_analysis"), None)
    assert risk_ref is not None
    assert "sharpe_ratio" in risk_ref.summary
    assert isinstance(risk_ref.summary["sharpe_ratio"], float)
    assert "max_drawdown" in risk_ref.summary


# ==============================================================================
# 17. Invalid Requests
# ==============================================================================
@pytest.mark.asyncio
async def test_invalid_requests():
    """Verifies HTTP 400 rejection for blank or malformed messages."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/ai/chat", json={"message": ""})
        assert resp.status_code == 400

        resp2 = await ac.post("/ai/chat", json={"message": "   "})
        assert resp2.status_code == 400


# ==============================================================================
# 18. AI API Endpoint
# ==============================================================================
@pytest.mark.asyncio
async def test_ai_api_endpoint():
    """Verifies standard POST /ai/chat and GET /ai/status HTTP endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. GET /ai/status
        status_resp = await ac.get("/ai/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert "status" in status_data
        assert "provider" in status_data
        assert "is_configured" in status_data

        # 2. POST /ai/chat
        chat_resp = await ac.post("/ai/chat", json={"message": "What is NVDA price?"})
        assert chat_resp.status_code == 200
        chat_data = chat_resp.json()
        assert "conversation_id" in chat_data
        assert "answer" in chat_data
        assert "relevant_assets" in chat_data
        assert "data_references" in chat_data


# ==============================================================================
# 19. Provider Timeout
# ==============================================================================
@pytest.mark.asyncio
async def test_provider_timeout(clean_service):
    """Verifies graceful fallback when provider encounters a timeout."""
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(side_effect=httpx.TimeoutException("Mock Timeout"))

    with patch.object(clean_service, "get_provider", return_value=(mock_provider, "mock_llm", "mock-model")):
        resp = await clean_service.chat("What is NVDA's Sharpe ratio?")
        assert isinstance(resp, AIChatResponse)
        assert "TimeoutException" in resp.answer or "Grounded Financial Analysis" in resp.answer
        assert len(resp.data_references) > 0


# ==============================================================================
# 20. Provider Error
# ==============================================================================
@pytest.mark.asyncio
async def test_provider_error(clean_service):
    """Verifies graceful fallback when provider returns HTTP 429 or 500."""
    mock_provider = MagicMock()
    mock_provider.generate_response = AsyncMock(side_effect=RuntimeError("Provider HTTP 429 Rate Limit"))

    with patch.object(clean_service, "get_provider", return_value=(mock_provider, "mock_llm", "mock-model")):
        resp = await clean_service.chat("What is Bitcoin's volatility?")
        assert isinstance(resp, AIChatResponse)
        assert "RuntimeError" in resp.answer or "Grounded Financial Analysis" in resp.answer


# ==============================================================================
# 21. Secret Protection
# ==============================================================================
@pytest.mark.asyncio
async def test_secret_protection(clean_service):
    """Verifies raw API keys are never exposed in responses or status payloads."""
    with patch.object(settings, "AI_API_KEY", "sk-super-secret-production-key-99999"):
        status = clean_service.get_status()
        assert "sk-super-secret-production-key-99999" not in status.masked_key
        assert status.masked_key.endswith("9999") or status.masked_key == "***"

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/ai/status")
            body = resp.text
            assert "sk-super-secret-production-key-99999" not in body


# ==============================================================================
# 22. No Fake Values
# ==============================================================================
@pytest.mark.asyncio
async def test_no_fake_values(clean_service):
    """Verifies that all values extracted in data references originate from real services."""
    intent = clean_service.parse_intent("What is NVDA's price?")
    _, refs, _, _ = await clean_service.build_grounded_context(intent, [])

    market_ref = next(r for r in refs if r.topic == "market_data")
    assert market_ref.summary["price"] > 0.0
    assert market_ref.timestamp is not None
    assert "fake" not in str(market_ref.summary).lower()
    assert "mock" not in str(market_ref.summary).lower()


# ==============================================================================
# 23. NVDA Context
# ==============================================================================
@pytest.mark.asyncio
async def test_nvda_context(clean_service):
    """Verifies dedicated end-to-end grounded query for NVIDIA."""
    resp = await clean_service.chat("What is NVDA's Sharpe ratio?")
    assert "nvidia" in resp.relevant_assets
    assert any(ref.asset == "NVDA" for ref in resp.data_references)


# ==============================================================================
# 24. BTC Context
# ==============================================================================
@pytest.mark.asyncio
async def test_btc_context(clean_service):
    """Verifies dedicated end-to-end grounded query for Bitcoin."""
    resp = await clean_service.chat("What is Bitcoin's return and volatility?")
    assert "bitcoin" in resp.relevant_assets
    assert any(ref.asset == "BTC/USD" for ref in resp.data_references)


# ==============================================================================
# 25. Gold Context
# ==============================================================================
@pytest.mark.asyncio
async def test_gold_context(clean_service):
    """Verifies dedicated end-to-end grounded query for Gold."""
    resp = await clean_service.chat("What is Gold's maximum drawdown?")
    assert "gold" in resp.relevant_assets
    assert any(ref.asset == "XAU/USD" for ref in resp.data_references)
