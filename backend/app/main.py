from fastapi import FastAPI

from app.api.market import router as market_router
from app.api.backtest import router as backtest_router


app = FastAPI(title="QuantLab API")

app.include_router(market_router)
app.include_router(backtest_router)


@app.get("/")
def root():
    return {"message": "QuantLab API is running"}