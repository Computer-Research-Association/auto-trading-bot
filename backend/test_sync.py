import asyncio
from core.database import AsyncSessionLocal
from app.domains.coin.service import sync_trade_history
import logging

logging.basicConfig(level=logging.INFO)

async def test():
    async with AsyncSessionLocal() as session:
        await sync_trade_history(session)

if __name__ == "__main__":
    asyncio.run(test())
