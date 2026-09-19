from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginRequest) -> Dict[str, Any]:
    if payload.username.strip() and payload.password:
        return {
            "access_token": "quantlab-jwt-session-token-institutional-demo",
            "token_type": "bearer",
            "user": {
                "id": "u-001",
                "username": payload.username,
                "name": "Alex Vance",
                "email": f"{payload.username}@quantlab.internal",
                "role": "Lead Quantitative Researcher",
                "tier": "Enterprise Institutional"
            }
        }
    raise HTTPException(status_code=400, detail="Invalid username or password")

@router.get("/me")
def get_current_user() -> Dict[str, Any]:
    return {
        "id": "u-001",
        "username": "quant_trader",
        "name": "Alex Vance",
        "email": "alex.vance@quantlab.internal",
        "role": "Lead Quantitative Researcher",
        "tier": "Enterprise Institutional"
    }
