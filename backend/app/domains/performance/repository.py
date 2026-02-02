from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.portfolio.models import PortfolioSnapshot

# TODO:
async def get_snapshots(
        db: AsyncSession,
        start: date | None = None,
        end: date | None = None,
        ) -> list[PortfolioSnapshot]:
    stmt = select(PortfolioSnapshot)
    if start is not None:
        stmt = stmt.where(PortfolioSnapshot.base_date >= start)
    if end is not None:
        stmt = stmt.where(PortfolioSnapshot.base_date <= end)
    stmt = stmt.order_by(PortfolioSnapshot.base_date.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

# service가 기대하는 이름을 맞춰주는 alias 메서드 추가
async def get_daily_snapshots(start: date, end: date, db: AsyncSession) -> list[PortfolioSnapshot]:
    return await get_snapshots(db, start=start, end=end)

