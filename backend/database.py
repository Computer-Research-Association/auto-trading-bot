import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.utills.models import Base

BASE_DIR = Path(__file__).resolve().parent  # backend 폴더
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL이 설정되어 있지 않습니다. backend/.env 확인")

engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

def init_db() -> None:
    """서버 시작 시 테이블 생성"""
    Base.metadata.create_all(engine)

def get_session():
    """FastAPI Depends로 주입할 DB 세션"""
    with Session(engine) as session:
        yield session