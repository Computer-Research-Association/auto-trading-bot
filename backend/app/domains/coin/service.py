from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.coin.models import TradeHistory

_PERIOD_TO_DAYS = {
    "7d": 7,
    "30d": 30,
    "90d": 90,
    "180d": 180,
}

def _since_dt(period: schemas.Period) -> datetime:
    days = _PERIOD_TO_DAYS[period]
    return datetime.now() - timedelta(days=days)

async def get_trade_history(q: schemas.TradeHistoryQuery, db: AsyncSession) -> schemas.TradeHistoryResponse:
    since = _since_dt(q.period)

    stmt = select(TradeHistory).where(TradeHistory.timestamp >= since)

    # 타입 필터 (side)
    if q.tx_type != "all":
        stmt = stmt.where(TradeHistory.side == q.tx_type.upper())

    # 검색 (market)
    if q.keyword:
        kw = f"%{q.keyword.strip()}%"
        stmt = stmt.where(TradeHistory.market.ilike(kw))

    # total
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    # paging
    offset = (q.page - 1) * q.limit
    stmt = stmt.order_by(desc(TradeHistory.timestamp)).offset(offset).limit(q.limit)

    trades = (await db.execute(stmt)).scalars().all()

    rows = [
        schemas.TradeHistoryRow(
            timestamp=t.timestamp,
            market=t.market,
            side=t.side,
            volume=float(t.volume),
            price=float(t.price),
            amount=float(t.amount),
            fee=float(t.fee),
            strategy=t.strategy,
        )
        for t in trades
    ]

    return schemas.TradeHistoryResponse(rows=rows, total=total, page=q.page, limit=q.limit)

async def create_seed_data(db: AsyncSession):
    new_trade = TradeHistory(
        market="KRW-BTC",
        side="BUY",
        volume=0.001,
        price=100000000.0,
        amount=100000.0,
        fee=50.0,
        strategy="Test Strategy"
    )
    db.add(new_trade)
    await db.commit()
    return new_trade

