from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_database
from app.domains.coin import service, schemas

router = APIRouter(tags=["coin"])

@router.get("/trades", response_model=schemas.TradeHistoryResponse)
async def get_trades(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    side: str | None = None,
    search: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_database),
):
    return await service.get_trade_history(
        q=schemas.TradeHistoryQuery(
            page=page,
            limit=limit,
            tx_type=side.lower() if side and side.lower() in ["buy", "sell", "deposit", "withdraw"] else "all",
            keyword=search
        ),
        db=db
    )

@router.get("/trades/re", response_model=schemas.TradeHistoryResponse)
async def get_trades_re(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database),
):
    """Refactored version of trade history with optimized Pydantic conversion"""
    return await service.get_trade_history_re(page=page, limit=limit, db=db)

@router.post("/trades/test-seed")
async def seed_trade(db: AsyncSession = Depends(get_database)):
    """테스트용 데이터 1건 생성 (나중에 삭제 예정)"""
    trade = await service.create_seed_data(db)
    return {"status": "success", "id": trade.id}
