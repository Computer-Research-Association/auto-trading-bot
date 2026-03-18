from datetime import datetime, time, timezone, date, timedelta
from sqlalchemy import select, func, desc, asc, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import Log
from core.settings import settings

# 한국 표준시 (UTC+9) — 날짜 필터 기준
KST = timezone(timedelta(hours=9))

async def list_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    limit: int = 50,
    level: list[str] | None = None,       # 다중선택: INFO, ERROR 동시
    category: list[str] | None = None,    # 다중선택: SYSTEM, DATA 동시
    eventname: list[str] | None = None,   # 다중선택: BUY, SELL 동시
    filter_op: str = "AND",               # AND: 타입 간 교집합 / OR: 타입 간 합집합
    search: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    offset = (page - 1) * limit

    stmt = select(Log)
    count_stmt = select(func.count()).select_from(Log)
    
    or_values: list = []    # OR 모드용: 모든 조건을 하나의 OR로
    and_filters: list = []  # AND 모드용: 각 조건을 별도 WHERE로

    for lvl in (level or []):
        v = lvl.upper()
        if filter_op == "OR":
            or_values.append(Log.level == v)
        else:
            and_filters.append(Log.level == v)

    for cat in (category or []):
        v = cat.upper()
        if filter_op == "OR":
            or_values.append(Log.category == v)
        else:
            and_filters.append(Log.category == v)

    for ev in (eventname or []):
        v = ev.upper()
        if filter_op == "OR":
            or_values.append(Log.event_name == v)
        else:
            and_filters.append(Log.event_name == v)

    fixed_filters = []
    if search:
        fixed_filters.append(
            or_(
                Log.message.ilike(f"%{search}%"),
                Log.event_name.ilike(f"%{search}%"),
                Log.level.ilike(f"%{search}%"),
                Log.category.ilike(f"%{search}%"),
            )
        )
    if start_date:
        # 사용자가 선택한 날짜는 KST 기준 → UTC로 변환해서 DB 비교
        start_kst = datetime.combine(start_date, time.min, tzinfo=KST)
        fixed_filters.append(Log.timestamp >= start_kst.astimezone(timezone.utc))
    if end_date:
        end_kst = datetime.combine(end_date, time.max, tzinfo=KST)
        fixed_filters.append(Log.timestamp <= end_kst.astimezone(timezone.utc))

    # 최종 조합
    all_filters: list = []
    if filter_op == "OR" and or_values:
        all_filters.append(or_(*or_values))  # 하나라도 맞으면 표시
    elif and_filters:
        all_filters.extend(and_filters)      # 모두 AND (같은 타입 여러 값 → 불가 → 0건)
    all_filters.extend(fixed_filters)

    if all_filters:
        stmt = stmt.where(*all_filters)
        count_stmt = count_stmt.where(*all_filters)

    total_count = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(Log.timestamp), desc(Log.id)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return items, total_count

async def get_new_logs(db: AsyncSession, last_id: int):
    """지정한 last_id 이후의 새 로그들을 가져옴 (ID 오름차순으로 순서 보장)"""
    stmt = select(Log).where(Log.id > last_id).order_by(asc(Log.id))
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_old_logs(db: AsyncSession):
    """
    오래된 로그 자동 삭제
    1. 단기 삭제 (HEARTBEAT, SYNC 등): LOG_RETENTION_DAYS_SHORT 경과 시
    2. 일반 삭제: LOG_RETENTION_DAYS 경과 시
    3. 개수 제한 삭제: 전체 합계가 LOG_MAX_COUNT 초과 시 오래된 로그부터
    """
    try:
        now_utc = datetime.now(timezone.utc)
        
        # 1. 단기 삭제
        cutoff_short = now_utc - timedelta(days=settings.LOG_RETENTION_DAYS_SHORT)
        stmt_short = delete(Log).where(
            Log.event_name.in_(["HEARTBEAT", "SYNC"]),
            Log.timestamp < cutoff_short
        )
        await db.execute(stmt_short)
        
        # 2. 일반 삭제
        cutoff_normal = now_utc - timedelta(days=settings.LOG_RETENTION_DAYS)
        stmt_normal = delete(Log).where(Log.timestamp < cutoff_normal)
        await db.execute(stmt_normal)
        
        # 변경사항 반영 (이후 count 정확성을 위해)
        await db.commit()
        
        # 3. 개수 제한 삭제
        count_stmt = select(func.count(Log.id))
        total_count = (await db.execute(count_stmt)).scalar() or 0
        
        if total_count > settings.LOG_MAX_COUNT:
            # 유지할 로그 중 가장 오래된 로그(MAX_COUNT번째)의 ID 탐색
            cutoff_id_stmt = (
                select(Log.id)
                .order_by(desc(Log.timestamp), desc(Log.id))
                .offset(settings.LOG_MAX_COUNT - 1)
                .limit(1)
            )
            cutoff_id_result = await db.execute(cutoff_id_stmt)
            cutoff_id = cutoff_id_result.scalar()
            
            if cutoff_id is not None:
                # 해당 ID보다 작은(오래된) 행 초과분 일괄 삭제
                stmt_excess = delete(Log).where(Log.id < cutoff_id)
                await db.execute(stmt_excess)
                await db.commit()
                
    except Exception as e:
        await db.rollback()
        raise e
