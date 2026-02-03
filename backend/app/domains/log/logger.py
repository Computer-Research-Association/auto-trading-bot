from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from datetime import datetime, timezone

class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogCategory(str, Enum):
    SYSTEM = "SYSTEM"
    DATA = "DATA"
    STRATEGY = "STRATEGY"
    TRADE = "TRADE"


class LogEvent(str, Enum):
    # SYSTEM
    ENGINE_START = "ENGINE_START"
    HEARTBEAT = "HEARTBEAT"
    ERROR = "ERROR"

    # DATA
    FETCH_FAIL = "FETCH_FAIL"
    VALID_FAIL = "VALID_FAIL"

    # STRATEGY
    DECISION = "DECISION"

    # TRADE
    BUY = "BUY"
    SELL = "SELL"
    STOPLOSS = "STOPLOSS"

async def log_to_db(
    db: AsyncSession,
    *,
    category: LogCategory,
    event_name: str,
    level: LogLevel,
    message: str,
    timestamp: Optional[datetime] = None,
    commit: bool = True,
) -> OperatingLog:

    row = OperatingLog(
        timestamp=timestamp or datetime.now(timezone.utc),
        level=level.value,
        category=category.value,
        event_name=event_name,  # 필요하면 LogEvent로 강제 가능
        message=message,
    )

    db.add(row)

    if commit:
        await db.commit()
        await db.refresh(row)

    return row


async def log_event(
    db: AsyncSession,
    *,
    category: LogCategory,
    event: LogEvent,
    level: LogLevel,
    message: str,
    timestamp: Optional[datetime] = None,
    commit: bool = True,
) -> OperatingLog:
    return await log_to_db(
        db,
        category=category,
        event_name=event.value,
        level=level,
        message=message,
        timestamp=timestamp,
        commit=commit,
    )