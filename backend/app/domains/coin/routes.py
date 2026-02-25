from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.domains.coin import schemas, service

router = APIRouter(tags=["coin"])

@router.get("/trades", response_model=schemas.TradeHistoryResponse)
async def list_trades(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    period: schemas.Period = Query("30d"),
    tx_type: schemas.TxType = Query("all"),
    keyword: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    q = schemas.TradeHistoryQuery(
        page=page,
        limit=limit,
        period=period,
        tx_type=tx_type,
        keyword=keyword
    )
    return await service.get_trade_history(q, db)

@router.post("/trades/test-seed")
async def seed_trade(db: AsyncSession = Depends(get_db)):
    """테스트용 데이터 1건 생성 (나중에 삭제 예정)"""
    trade = await service.create_seed_data(db)
    return {"status": "success", "id": trade.id}