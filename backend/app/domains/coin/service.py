from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, desc, and_, between
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.log.models import Log

from app.domains.coin.models import TradeHistory
from app.domains.coin import schemas
from app.domains.coin.schemas import TradeHistoryResponse
from app.utills.upbit_client import client as upbit_client
from core.logger import logger

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
    if q.period == "all":
        stmt = select(TradeHistory)
    else:
        since = _since_dt(q.period)
        stmt = select(TradeHistory).where(TradeHistory.timestamp >= since)

    if q.tx_type != "all":
        stmt = stmt.where(TradeHistory.side == q.tx_type.upper())

    if q.keyword:
        kw = f"%{q.keyword.strip()}%"
        stmt = stmt.where(TradeHistory.market.ilike(kw))

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

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

async def get_trade_history_re(page: int, limit: int, db: AsyncSession) -> schemas.TradeHistoryResponse:
    import app.domains.coin.repository as coin_repo
    trades, total = await coin_repo.get_pagination_trade_history(page, limit, db)

    rows = [schemas.TradeHistoryRow.model_validate(t) for t in trades]
    return schemas.TradeHistoryResponse(rows=rows, total=total, page=page, limit=limit)

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

async def sync_trade_history(db: AsyncSession):
    """
    Upbit API에서 최근 3개월간의 체결 내역을 가져와 DB에 중복 없이 저장합니다.
    - 5분 버퍼를 두어 최신 데이터 누락을 방지합니다.
    - BTC 거래내역은 'RSI BB 매매 전략'으로 저장합니다.
    """
    try:
        latest_stmt = select(func.max(TradeHistory.timestamp))
        latest_timestamp = (await db.execute(latest_stmt)).scalar()

        now = datetime.now(timezone.utc)
        three_months_ago = now - timedelta(days=90)

        if latest_timestamp:
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
            start_time = max(latest_timestamp - timedelta(minutes=5), three_months_ago)
        else:
            start_time = three_months_ago

        logger.info(f"[TradeSync] Sync started from {start_time}")

        done_orders = upbit_client.get_completed_orders()

        if not done_orders:
            logger.warning(f"[TradeSync] No completed orders found.")
            return

        fetch_count = 0
        insert_count = 0
        skip_count = 0

        for order in done_orders:
            order_time = datetime.fromisoformat(order['created_at'])
            if order_time < start_time:
                continue

            fetch_count += 1

            order_detail = upbit_client.get_order_info(order['uuid'])

            if not order_detail or 'trades' not in order_detail:
                continue

            trades = order_detail['trades']
            for fill in trades:
                market = order['market']
                side = order['side'].upper()
                if side == 'BID':
                    side = 'BUY'
                elif side == 'ASK':
                    side = 'SELL'

                price = float(fill['price'])
                volume = float(fill['volume'])
                amount = float(fill['funds'])

                total_fee = float(order_detail.get('fee', 0))
                total_volume = float(order_detail.get('executed_volume', 1))
                fill_fee = (volume / total_volume) * total_fee if total_volume > 0 else 0

                fill_time = datetime.fromisoformat(fill['created_at'])
                if fill_time.tzinfo is None:
                    fill_time = fill_time.replace(tzinfo=timezone.utc)

                if fill_time < start_time:
                    continue

                duplicated_check = select(TradeHistory).where(
                    and_(
                        TradeHistory.market == market,
                        TradeHistory.timestamp == fill_time
                    )
                )
                result = await db.execute(duplicated_check)
                existing = result.scalars().first()

                if existing:
                    skip_count += 1
                    continue

                # BTC 거래내역은 'RSI BB 전략', 나머지는 'Upbit Sync'
                strategy = "RSI BB 전략" if "BTC" in market else "Upbit Sync"

                new_trade = TradeHistory(
                    market=market,
                    side=side,
                    volume=volume,
                    price=price,
                    amount=amount,
                    fee=fill_fee,
                    timestamp=fill_time,
                    strategy=strategy
                )

                db.add(new_trade)
                await db.flush([new_trade])
                await db.refresh(new_trade)
                insert_count += 1

        if insert_count > 0:
            await db.commit()
            logger.info(
                f"[TradeSync] Successfully synced. Fetched:{fetch_count}, Inserted:{insert_count}, Skipped:{skip_count}")
            return
        logger.info(f"[TradeSync] No new trades to sync. Fetched:{fetch_count}, Skipped:{skip_count}")

    except Exception as e:
        await db.rollback()
        logger.error(f"[TradeSync] Sync failed: {e}", exc_info=True)