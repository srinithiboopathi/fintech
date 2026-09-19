from fastapi import APIRouter

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/health")
def market_health():
    return {"status": "market api is running"}