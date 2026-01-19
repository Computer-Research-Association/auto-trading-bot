import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pyupbit

from app.domains.portfolio.routes import router as portfolio_router

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Auto Trading Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(portfolio_router)

@app.get("/")
def root():
    return {"message": "Server is up and running"}

@app.get("/test-upbit")
def test_upbit():
    access_key = os.getenv("UPBIT_ACCESS_KEY")
    secret_key = os.getenv("UPBIT_SECRET_KEY")

    if not access_key or not secret_key:
        return {"status": "error", "message": "UPBIT keys not found in .env"}

    upbit = pyupbit.Upbit(access_key, secret_key)
    try:
        balances = upbit.get_balances()
        return {"status": "success", "data": balances}
    except Exception as e:
        return {"status": "error", "message": str(e)}