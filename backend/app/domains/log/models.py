from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.utills.models import BaseEntity


class OperatingLog(BaseEntity):
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

    # 사람이 읽는 실제 로그 메시지
    message: Mapped[str] = mapped_column(String)