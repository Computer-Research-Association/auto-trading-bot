from __future__ import annotations
from datetime import datetime, date, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Index

#거래 체결 시각알기 위함 (날짜 + 시간)
def utcnow() -> datetime:
    return datetime.now(timezone.utc)