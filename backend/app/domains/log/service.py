from datetime import datetime, time, timezone, date
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import Log

async def list_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    limit: int = 50,
    level: str | None = None,
    category: str | None = None,
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    offset = (page - 1) * limit
    
    # 쿼리 빌더 패턴으로 개선
    stmt = select(Log)
    count_stmt = select(func.count()).select_from(Log)
    
    filters = []
    if level:
        filters.append(Log.level == level)
    if category:
        filters.append(Log.category == category)
    if search:
        filters.append(
            or_(
                Log.message.ilike(f"%{search}%"),
                Log.event_name.ilike(f"%{search}%"),
                Log.level.ilike(f"%{search}%")
            )
        )
    
    # 날짜 범위 처리: date 객체로 직접 받아 안전하게 처리
    if start_date:
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        filters.append(Log.timestamp >= start_dt)
    if end_date:
        end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        filters.append(Log.timestamp <= end_dt)
        
    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)
        
    # Total count (완전히 동일한 필터 적용)
    total_count = (await db.execute(count_stmt)).scalar() or 0
    
    # Items (정렬 안정성 강화)
    stmt = stmt.order_by(desc(Log.timestamp), desc(Log.id)).offset(offset).limit(limit)
        
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return items, total_count

async def get_new_logs(db: AsyncSession, last_id: int):
    """지정한 last_id 이후의 새 로그들을 가져옴 (ID 오름차순으로 순서 보장)"""
    stmt = select(Log).where(Log.id > last_id).order_by(asc(Log.id))
    result = await db.execute(stmt)
    return result.scalars().all()
