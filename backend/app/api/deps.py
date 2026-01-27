import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL이 설정되어 있지 않습니다. .env에 DATABASE_URL을 추가하세요.")

from pathlib import Path

# DB 경로를 절대 경로로 강제 변환 (실행 위치에 따른 에러 방지)
if DATABASE_URL.startswith("sqlite"):
    # backend/ 폴더 위치 찾기 (deps.py -> api -> app -> backend)
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
    # URL 파싱: "sqlite:///./foo.db" -> "./foo.db"
    # "sqlite:///foo.db" -> "foo.db"
    if "sqlite:///" in DATABASE_URL:
        rel_path = DATABASE_URL.split("sqlite:///")[1]
    else:
        rel_path = DATABASE_URL.split("sqlite:")[1]

    # 상대 경로인 경우에만 절대 경로로 변환
    # (이미 절대 경로이거나, 메모리 DB인 경우는 제외하고 싶지만, 
    #  보통 .env에 ./filename.db 형태로 적으므로 이를 처리)
    if not os.path.isabs(rel_path):
        # ./ 제거
        if rel_path.startswith("./"):
            rel_path = rel_path[2:]
            
        db_path = BASE_DIR / rel_path
        DATABASE_URL = f"sqlite:///{db_path}"
        print(f"DEBUG_DB: Resolved Absolute Path -> {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
