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

    # ① 주요 필터 — filter_op 에 따라 동작이 완전히 다름
    #
    # ┌─ AND 모드 (기본) ────────────────────────────────────────────────────────┐
    # │ 선택한 값마다 독립적인 WHERE 조건을 추가하여 AND로 연결                      │
    # │                                                                          │
    # │ 예시 (AND)                                                               │
    # │  • Buy + Sell  → WHERE event_name='BUY' AND event_name='SELL'           │
    # │                   → 한 행이 두 값을 동시에 가질 수 없으므로 → 0건          │
    # │  • System + Data → WHERE category='SYSTEM' AND category='DATA' → 0건    │
    # │  • INFO + Buy    → WHERE level='INFO' AND event_name='BUY'              │
    # │                   → INFO 레벨이면서 Buy 이벤트인 것만 표시                 │
    # └──────────────────────────────────────────────────────────────────────────┘
    #
    # ┌─ OR 모드 ────────────────────────────────────────────────────────────────┐
    # │ 모든 선택값을 하나의 OR 조건으로 묶음                                        │
    # │                                                                          │
    # │ 예시 (OR)                                                                │
    # │  • Buy + Sell  → WHERE event_name='BUY' OR event_name='SELL'            │
    # │                   → Buy이거나 Sell인 로그 모두 표시                        │
    # │  • System + INFO → WHERE category='SYSTEM' OR level='INFO'              │
    # │                   → 둘 중 하나라도 해당하면 표시                           │
    # └──────────────────────────────────────────────────────────────────────────┘

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
