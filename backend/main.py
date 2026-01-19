import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

# 1) .env 로드
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# 2) app 생성
app = FastAPI(title="Auto Trading Bot API")

# 3) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4) 라우터 등록 (반드시 app 만든 다음!)
app.include_router(api_router)

# 5) 루트 확인용
@app.get("/")
def root():
    return {"message": "Server is up and running"}