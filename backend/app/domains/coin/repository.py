from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.coin.models import TradeHistory

async def get_pagination_trade_history(page: int, per_page: int, db: AsyncSession):
    """
    체결 내역을 페이징하여 조회합니다.
    """
    offset = (page - 1) * per_page
    
    # 전체 개수 조회
    count_stmt = select(func.count()).select_from(TradeHistory)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # 데이터 조회 (최신순)
    stmt = (
        select(TradeHistory)
        .order_by(TradeHistory.timestamp.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return items, total
