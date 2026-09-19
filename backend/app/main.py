from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.market import router as market_router
from app.utils.exceptions import AlphaVantageBaseException
from app.utils.logging import logger

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Production-grade Market Data Ingestion Layer for Quantitative Analysis "
            "and Multi-Asset Backtesting (NVIDIA, Bitcoin, Gold)."
        ),
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler for Alpha Vantage & Domain Exceptions
    @app.exception_handler(AlphaVantageBaseException)
    async def alpha_vantage_exception_handler(request: Request, exc: AlphaVantageBaseException):
        logger.error(f"Domain Error [{exc.error_type}]: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )

    from fastapi.exceptions import RequestValidationError

    # Validation Exception Handler (convert 422 to 400 Bad Request)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation Error on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "BAD_REQUEST",
                "message": "Malformed request parameters or invalid payload.",
                "status_code": 400,
                "details": exc.errors(),
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )

    # Fallback Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled Exception on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred while processing the market data request.",
                "status_code": 500,
                "path": request.url.path,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )

    # Mount Routes
    app.include_router(market_router)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
            "docs": "/docs",
            "viewer": "/viewer",
            "endpoints": {
                "health": "/health",
                "assets": "/assets",
                "historical": "/market/{asset}/historical",
                "latest": "/market/{asset}/latest",
                "clean_data": "/market/{asset}/data",
                "clean_summary": "/market/{asset}/data/summary",
                "indicators": "/market/{asset}/indicators",
                "risk_metrics": "/market/{asset}/risk-metrics",
                "risk_analysis": "/market/{asset}/risk-analysis",
                "correlation": "/market/correlation",
                "rolling_correlation": "/market/correlation/rolling",
                "backtest": "/market/{asset}/backtest"
            },


            "supported_assets": ["nvidia", "bitcoin", "gold"]
        }

    from pathlib import Path
    from fastapi.responses import FileResponse
    frontend_file = Path(__file__).resolve().parent.parent.parent / "frontend" / "index.html"

    @app.get("/viewer", tags=["Viewer"])
    async def viewer():
        """Serves the Market Data Viewer web application."""
        if frontend_file.exists():
            return FileResponse(frontend_file)
        return JSONResponse({"error": "Viewer frontend not found"}, status_code=404)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )
