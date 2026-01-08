import os
from dotenv import load_dotenv
import pyupbit
from fastapi import FastAPI
from sqlmodel import SQLModel
from database import engine
# from models import User 테스트를 위한 임시 주석처리

# 1. 환경 변수 로드 및 업비트 초기화
load_dotenv()

access_key = os.getenv("UPBIT_ACCESS_KEY")
secret_key = os.getenv("UPBIT_SECRET_KEY")
upbit = pyupbit.Upbit(access_key, secret_key)

app = FastAPI()


@app.on_event("startup")
def on_startup():
    # 서버 시작 시 DB 테이블 생성 (도커 DB가 켜져 있어야 함)
    try:
        SQLModel.metadata.create_all(engine)
        print("DB Connection & Tables Creation Success!")
    except Exception as e:
        print(f"DB Connection Failed: {e}")


@app.get("/")
def root():
    return{"message": "Sever is up and running"}


@app.get("/test-upbit")
async def test_upbit():
    """업비트 api 키가 정상인지 확인하는 테스트 엔드 포인트"""
    try:
        # 잔고 하나 조회
        balances = upbit.get_balances()
        print(balances)
        
        return {"status": "success", "data": balances}
    except Exception as e:
        return {"status": "error", "message": str(e)}