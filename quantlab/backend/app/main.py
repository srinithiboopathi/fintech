import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.database.connection import engine, Base

# Import Routers
from app.api.auth import router as auth_router
from app.api.market import router as market_router
from app.api.analytics import router as analytics_router
from app.api.correlation import router as correlation_router
from app.api.strategies import router as strategies_router
from app.api.backtest import router as backtest_router
from app.api.robustness import router as robustness_router
from app.api.regimes import router as regimes_router
from app.api.reports import router as reports_router

# Initialize Database schema
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database schema initialization warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Quantitative Multi-Asset Financial Intelligence & Backtesting Platform API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware for React / Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Endpoints
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {"status": "ok"}

# Mount Routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(market_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(correlation_router, prefix="/api/v1")
app.include_router(strategies_router, prefix="/api/v1")
app.include_router(backtest_router, prefix="/api/v1")
app.include_router(robustness_router, prefix="/api/v1")
app.include_router(regimes_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")

# Also Mount Routers under /api for clean universal routing
app.include_router(auth_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(correlation_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")
app.include_router(robustness_router, prefix="/api")
app.include_router(regimes_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

@app.get("/", tags=["System"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
        "supported_assets": ["Gold (GC=F)", "Bitcoin (BTC-USD)", "NVIDIA (NVDA)"]
    }
