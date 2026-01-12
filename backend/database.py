import os
from dotenv import load_dotenv  
from sqlmodel import create_engine, Session
from pathlib import Path

# 1. DB 접속 정보 설정 (이미지에서 설정한 정보와 일치해야 함)
# 형식: postgresql://사용자:비밀번호@호스트:포트/DB이름
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
# 2. 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)  # echo=True는 SQL 로그를 터미널에 보여

# 3. DB 세션을 가져오는 함수 (나중에 사용)


def get_session():
    with Session(engine) as session:
        yield session