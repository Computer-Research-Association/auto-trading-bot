from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class OperatingLog(SQLModel, table=True):

    __tablename__ = "operating_log"

    # ID 저장됨
    id: Optional[int] = Field(default=None, primary_key=True)

    # 로그 발생 시각
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        index=True,
        description="로그 발생 시각",
    )

    # 로그 심각도 (INFO / WARNING / ERROR)
    level: str = Field(
        index=True,
        description="로그 레벨 (INFO, WARNING, ERROR)",
    )

    # 로그 대분류 (SYSTEM / DATA / STRATEGY / TRADE)
    category: str = Field(
        index=True,
        description="로그 카테고리",
    )

    # 이벤트 식별자 (ENGINE_START, BUY, SELL 등)
    event_name: str = Field(
        index=True,
        description="이벤트 이름",
    )

    # 사람이 읽는 실제 로그 메시지
    message: str = Field(
        description="상세 로그 메시지",
    )