"""
Health check endpoints for QUANTLAB Backend.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str = "QUANTLAB API"
    environment: str = "development"


@router.get("/health", response_model=HealthResponse)
def get_health():
    """
    Health check endpoint to verify backend operational readiness.
    """
    return HealthResponse(
        status="healthy",
        app_name="QUANTLAB API",
        environment="development"
    )
