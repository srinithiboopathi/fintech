"""
Step 13: Grounded AI Financial Intelligence Assistant API Routes.
Provides interactive conversational analysis endpoints backed by authoritative quantitative calculations.
"""

from fastapi import APIRouter, HTTPException, Request, status
from app.models.schemas import AIChatRequest, AIChatResponse, AIStatusResponse
from app.services.ai_assistant import ai_assistant_service
from app.utils.logging import logger

router = APIRouter(prefix="/ai", tags=["AI Intelligence Assistant"])


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Query the Grounded AI Financial Intelligence Assistant",
    description=(
        "Synthesizes platform quantitative data (returns, volatility, Sharpe, max drawdown, "
        "correlation, strategy signals, backtest results, and market regimes) into explainable insights. "
        "Strictly grounded in factual platform calculations with zero simulated or hallucinated numbers."
    ),
    responses={
        200: {"description": "Grounded AI analysis and factual references successfully generated."},
        400: {"description": "Malformed chat message or empty prompt."},
        500: {"description": "Internal error processing the grounded AI analysis."}
    }
)
async def chat(request: AIChatRequest):
    """Processes an interactive inquiry and returns a context-grounded response."""
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty."
        )

    try:
        response = await ai_assistant_service.chat(
            message=request.message.strip(),
            asset_hint=request.asset,
            conversation_id=request.conversation_id
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error handling AI chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating the financial intelligence response."
        )


@router.get(
    "/status",
    response_model=AIStatusResponse,
    summary="AI Assistant Health & Provider Status",
    description="Returns the active AI provider, model configuration, and readiness status without exposing secrets."
)
async def get_status():
    """Returns AI assistant provider status and configuration readiness."""
    try:
        return ai_assistant_service.get_status()
    except Exception as e:
        logger.exception(f"Error retrieving AI assistant status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI assistant status."
        )
