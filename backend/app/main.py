from fastapi import FastAPI
from app.api.market import router as market_router

app = FastAPI(title="QuantLab API")

app.include_router(market_router)


@app.get("/")
def root():
    return {"message": "QuantLab API is running"}