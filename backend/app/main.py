from fastapi import FastAPI

app = FastAPI(title="QuantLab API")


@app.get("/")
def root():
    return {"message": "QuantLab API is running"}