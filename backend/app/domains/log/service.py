from __future__ import annotations
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import OperatingLog
from app.domains.log import schemas

async def get_logs(db: AsyncSession, limit: int = 100) -> schemas.LogResponse:
    stmt = select(OperatingLog).order_by(desc(OperatingLog.timestamp)).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    total_stmt = select(func.count()).select_from(OperatingLog)
    total = (await db.execute(total_stmt)).scalar_one()
    
    return schemas.LogResponse(
        rows=[schemas.LogRow.model_validate(log) for log in logs],
        total=total
    )
