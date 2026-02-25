from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_database
from app.domains.coin import service, schemas

router = APIRouter(prefix="/api/coin", tags=["coin"])

@router.get("/trades", response_model=schemas.TradeHistoryListResponse)
async def get_trades(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    side: str | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_database),
):
    return await service.get_trade_histories(
        db=db,
        page=page,
        limit=limit,
        side=side,
        search=search,
        start_date=start_date,
        end_date=end_date,
    )

@router.post("/trades/test-seed")
async def seed_trade(db: AsyncSession = Depends(get_database)):
    """테스트용 데이터 1건 생성 (나중에 삭제 예정)"""
    trade = await service.create_seed_data(db)
    return {"status": "success", "id": trade.id}
