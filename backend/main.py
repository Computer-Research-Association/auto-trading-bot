import os
from dotenv import load_dotenv
import pyupbit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from pathlib import Path

from database import engine
from upbit.asset_api import router as asset_router

# 1. 환경 변수 로드
env_path = Path(__file__).resolve().parent / ".env"  # ✅ (루트 main.py 기준)
load_dotenv(dotenv_path=env_path)

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key = os.getenv("UPBIT_SECRET_KEY")

# (선택) 키 없을 때 바로 알려주기
if not access_key or not secret_key:
    print("⚠️ UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY 가 .env에서 로드되지 않았습니다.")

upbit = pyupbit.Upbit(access_key, secret_key)

app = FastAPI()


@app.on_event("startup")
def on_startup():
    try:
        SQLModel.metadata.create_all(engine)
        print("DB Connection & Tables Creation Success!")
    except Exception as e:
        print(f"DB Connection Failed: {e}")


@app.get("/")
def root():
    return {"message": "Server is up and running"}


@app.get("/test-upbit")
async def test_upbit():
    """업비트 api 키가 정상인지 확인하는 테스트 엔드 포인트"""
    try:
        balances = upbit.get_balances()
        return {"status": "success", "data": balances}
    except Exception as e:
        return {"status": "error", "message": str(e)}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asset_router, prefix="/api")