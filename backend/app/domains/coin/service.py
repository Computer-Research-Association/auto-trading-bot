from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.coin import schemas
from app.domains.coin.models import Trade

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

    stmt = select(Trade).where(Trade.executed_at >= since)

    # 타입 필터
    if q.tx_type != "all":
        stmt = stmt.where(Trade.tx_type == q.tx_type)

    # 검색 (market/coin)
    if q.keyword:
        kw = f"%{q.keyword.strip()}%"
        stmt = stmt.where(Trade.market.ilike(kw))

    # 전략 필터
    if q.strategy:
        stmt = stmt.where(Trade.strategy == q.strategy)

    # total
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    # paging
    offset = (q.page - 1) * q.size
    stmt = stmt.order_by(desc(Trade.executed_at)).offset(offset).limit(q.size)

    trades = (await db.execute(stmt)).scalars().all()

    rows = [
        schemas.TradeHistoryRow(
            executed_at=t.executed_at,
            market=t.market,
            tx_type=t.tx_type,
            qty=float(t.qty),
            price_krw=float(t.price_krw),
            amount_krw=float(t.amount_krw),
            fee_krw=float(getattr(t, "fee_krw", 0) or 0),
            strategy=getattr(t, "strategy", None),
        )
        for t in trades
    ]

    return schemas.TradeHistoryResponse(rows=rows, total=total, page=q.page, size=q.size)

