import asyncio
from core.database import AsyncSessionLocal
from sqlalchemy import select, func, desc
from app.domains.coin.models import TradeHistory

async def test():
    async with AsyncSessionLocal() as session:
        stmt = select(TradeHistory).order_by(desc(TradeHistory.timestamp)).limit(5)
        res = await session.execute(stmt)
        trades = res.scalars().all()
        for t in trades:
            print(t.id, t.market, t.timestamp, t.strategy)

if __name__ == "__main__":
    asyncio.run(test())
