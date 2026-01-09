import os
from dotenv import load_dotenv

load_dotenv()  # .env 로드

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

ENV = os.getenv("ENV", "dev")

if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
    raise RuntimeError("Upbit API keys are not set")