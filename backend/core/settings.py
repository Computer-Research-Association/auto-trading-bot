import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# .env 파일 로드 (절대 경로 사용)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

class Settings(BaseSettings):
    # .env 파일 또는 환경 변수에서 자동으로 매핑됨
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str
    
    # Snapshot 스케줄 설정
    SNAPSHOT_CRON_HOUR: int = 0
    SNAPSHOT_CRON_MINUTE: int = 0
    SNAPSHOT_TIMEZONE: str = "Asia/Seoul"

    # 환경 변수 설정
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore" # 추가 환경 변수는 무시
    )

    @property
    def database_url(self) -> str:
        # DB_HOST에 혹시 모를 주석이나 공백이 포함된 경우를 대비해 정제
        host = self.DB_HOST.split('#')[0].strip() if self.DB_HOST else "db"
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{host}:{self.DB_PORT}/{self.DB_NAME}"

# 싱글톤 인스턴스 생성
settings = Settings()
