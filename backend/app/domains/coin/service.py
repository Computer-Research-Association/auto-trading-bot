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


##########################################################################################################################
async def get_trade_history_re(page: int, limit: int, db: AsyncSession) -> schemas.TradeHistoryResponse:
    import app.domains.coin.repository as coin_repo
    trades, total = await coin_repo.get_pagination_trade_history(page, limit, db)
    
    rows = [schemas.TradeHistoryRow.model_validate(t) for t in trades]
    return schemas.TradeHistoryResponse(rows=rows, total=total, page=page, limit=limit)

##########################################################################################################################
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
    - (market, side, price, volume, timestamp, amount, fee) 조합으로 중복 체크를 수행합니다.
    """
    try:
        # 1. DB에서 최신 timestamp 조회
        latest_stmt = select(func.max(TradeHistory.timestamp))
        latest_timestamp = (await db.execute(latest_stmt)).scalar()

        # 2. 조회 시작 범위 설정 (기본 3개월 전, 데이터 있으면 최신-5분)
        now = datetime.now(timezone.utc)
        three_months_ago = now - timedelta(days=90)

        if latest_timestamp:
            # DB timestamp는 보통 timezone-aware로 저장됨 (models.py: DateTime(timezone=True))
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
            start_time = max(latest_timestamp - timedelta(minutes=5), three_months_ago)
        else:
            start_time = three_months_ago

        logger.info(f"[TradeSync] Sync started from {start_time}")

        # 3. 완료된 주문 목록 조회
        # pyupbit.get_order(state='done')는 전체 마켓 대상
        # [TEST] get data from upbit (Mocked)
        done_orders = upbit_client.get_completed_orders()
        # done_orders = [
        #     {
        #         "uuid": "test-dummy-uuid-001",
        #         "market": "KRW-BTC",
        #         "side": "bid",
        #         "created_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        #     }
        # ]

        if not done_orders:
            logger.warning(f"[TradeSync] No completed orders found.")
            return

        fetch_count = 0
        insert_count = 0
        skip_count = 0

        for order in done_orders:
            # order['created_at'] parsing (ISO 8601)
            order_time = datetime.fromisoformat(order['created_at'])
            if order_time < start_time:
                # 주문 생성 시각이 start_time보다 이전이면 스킵 (early stop은 list가 정렬되어 있다는 가정하에 가능)
                # Upbit 주문 목록은 보통 최신순 정렬
                continue

            fetch_count += 1

            # [TEST] 개별 주문의 체결(fills) 상세 내역 조회 (Mocked)
            order_detail = upbit_client.get_order_info(order['uuid'])
            # order_detail = {
            #     "uuid": order['uuid'],
            #     "market": order['market'],
            #     "side": order['side'],
            #     "executed_volume": "0.001",
            #     "fee": "100.0",
            #     "trades": [
            #         {
            #             "market": order['market'],
            #             "price": "50000000.0",
            #             "volume": "0.001",
            #             "funds": "50000.0",
            #             "side": order['side'],
            #             "created_at": order['created_at'],
            #         }
            #     ]
            # }

            if not order_detail or 'trades' not in order_detail:
                continue

            trades = order_detail['trades']
            for fill in trades:
                # fill 데이터 추출
                market = order['market']
                side = order['side'].upper()  # 'bid' -> 'BUY', 'ask' -> 'SELL'
                if side == 'BID':
                    side = 'BUY'
                elif side == 'ASK':
                    side = 'SELL'

                price = float(fill['price'])
                volume = float(fill['volume'])
                amount = float(fill['funds'])
                # 수수료: order_detail['fee']는 전체 주문에 대한 것일 수 있음. 
                # 체결별 수수료는 (체결금액 * 수수료율)로 계산하거나 
                # order_detail['trades']에 수수료가 없다면 비례 배분 필요.
                # Upbit 주문 상세의 'fee'는 누적 수수료임.
                # 여기서는 간단하게 개별 체결의 비중만큼 fee를 배분하거나 0으로 일단 처리 후 업데이트 고민.
                # TradeHistory 테이블 스키마에 fee가 필수이므로 일단 주문 전체 수수료를 trades 수로 나누거나 비례 배분.
                total_fee = float(order_detail.get('fee', 0))
                total_volume = float(order_detail.get('executed_volume', 1))
                fill_fee = (volume / total_volume) * total_fee if total_volume > 0 else 0

                fill_time = datetime.fromisoformat(fill['created_at'])
                if fill_time.tzinfo is None:
                    fill_time = fill_time.replace(tzinfo=timezone.utc)

                if fill_time < start_time:
                    continue

                # 5. 중복 체크 (market, side, price, volume, timestamp, amount, fee)
                # amount와 fee는 부동소수점 오차 고려가 필요할 수 있으나 일단 필드값 그대로 비교
                ###################################################################3
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
                ######################################################################

                # 5.5 전략 추론 (최근 1분 내에 봇이 이 마켓/사이드로 로그를 남겼는지 확인)
                log_check_start = fill_time - timedelta(minutes=1)
                log_check_end = fill_time + timedelta(minutes=1)
                
                # 봇의 전략 로그 검색
                log_stmt = select(Log).where(
                    and_(
                        Log.category == "TRADE",
                        Log.timestamp >= log_check_start,
                        Log.timestamp <= log_check_end,
                        Log.message.ilike(f"%{market}%")
                    )
                ).order_by(desc(Log.timestamp)).limit(1)
                
                log_result = await db.execute(log_stmt)
                bot_log = log_result.scalars().first()
                
                derived_strategy = "수동 매매 (업비트)"
                if bot_log:
                    if "RSI_BB" in bot_log.message:
                        derived_strategy = "RSI 과매도 반동"
                    elif "Moving Average" in bot_log.message:
                        derived_strategy = "이동평균선 골든크로스"
                    elif "Scalping" in bot_log.message:
                        derived_strategy = "초단타 스캘핑 V1"
                    else:
                        derived_strategy = "기본 자동매매"

                # 6. DB 저장
                new_trade = TradeHistory(
                    market=market,
                    side=side,
                    volume=volume,
                    price=price,
                    amount=amount,
                    fee=fill_fee,
                    timestamp=fill_time,
                    strategy=derived_strategy
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
