from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import Log


async def create_log(
    db: AsyncSession,
    level: str,
    category: str,
    event_name: str,
    message: str,
    timestamp: Optional[datetime] = None,
    commit: bool = True,
) -> Log:
    """DB에 로그를 적재하는 유틸리티"""
    new_log = Log(
        level=level,
        category=category,
        event_name=event_name,
        message=message,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(new_log)
    if commit:
        await db.commit()
        await db.refresh(new_log)
    return new_log
