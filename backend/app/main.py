"""
QUANTLAB Backend Application Entry Point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.market import router as market_router
from backend.app.api.quant import router as quant_router
from backend.app.api.correlation import router as correlation_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Quantitative Multi-Asset Financial Intelligence & Backtesting API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health endpoint
@app.get("/health", tags=["Health"])
def root_health():
    return {"status": "healthy"}

@app.get("/", tags=["Root"])
def root():
    return {
        "platform": "QUANTLAB",
        "description": "Quantitative Multi-Asset Financial Intelligence & Backtesting Platform",
        "status": "online",
        "version": "0.1.0",
        "health_endpoint": "/health"
    }

# API v1 routes
app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(market_router, prefix=settings.API_V1_PREFIX)
app.include_router(quant_router, prefix=settings.API_V1_PREFIX)
app.include_router(correlation_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
