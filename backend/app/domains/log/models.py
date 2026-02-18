from datetime import datetime
from sqlalchemy import DateTime, String, func, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.utills.models import BaseEntity


class Log(BaseEntity):
    __tablename__ = "operating_log"

    # 로그 발생 시각
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    # 로그 심각도 (INFO / WARNING / ERROR)
    level: Mapped[str] = mapped_column(String, index=True)

    # 로그 대분류 (SYSTEM / DATA / STRATEGY / TRADE)
    category: Mapped[str] = mapped_column(String, index=True)

    # 이벤트 식별자 (ENGINE_START, BUY, SELL 등)
    event_name: Mapped[str] = mapped_column(String, index=True)

    # 사람이 읽는 실제 로그 메시지 (대용량 대응)
    message: Mapped[str] = mapped_column(Text)

    # 복합 인덱스 추가 (요구사항)
    __table_args__ = (
        Index("ix_logs_level_timestamp", "level", "timestamp"),
        Index("ix_logs_category_timestamp", "category", "timestamp"),
    )