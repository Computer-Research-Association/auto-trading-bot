from datetime import datetime, time, timezone, date, timedelta
from sqlalchemy import select, func, desc, asc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import Log

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

    # ① 주요 필터 — filter_op에 따라 다르게 조합
    #
    # AND 모드 (기본): 선택한 값마다 별도의 WHERE 조건 추가
    #   → category=SYSTEM AND category=DATA 는 불가능 → 0건 (정상)
    #   → category=SYSTEM AND event_name=SYNC → SYSTEM이면서 SYNC인 것
    #
    # OR 모드: 모든 선택값을 하나의 OR 조건으로 묶음
    #   → category=SYSTEM OR category=DATA OR event_name=SYNC → 하나라도 해당되면 표시
    #
    all_values = []  # OR 모드용: (컬럼, 값) 쌍 목록
    main_filters = []  # AND 모드용: 각 조건

    for lvl in (level or []):
        v = lvl.upper()
        if filter_op == "OR":
            all_values.append(Log.level == v)
        else:
            main_filters.append(Log.level == v)

    for cat in (category or []):
        v = cat.upper()
        if filter_op == "OR":
            all_values.append(Log.category == v)
        else:
            main_filters.append(Log.category == v)

    for ev in (eventname or []):
        v = ev.upper()
        if filter_op == "OR":
            all_values.append(Log.event_name == v)
        else:
            main_filters.append(Log.event_name == v)

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
    all_filters = []
    if filter_op == "OR" and all_values:
        all_filters.append(or_(*all_values))   # 하나라도 맞으면 표시
    elif main_filters:
        all_filters.extend(main_filters)       # 모두 AND (같은 타입 2개 → 0건)
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
