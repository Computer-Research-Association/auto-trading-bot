from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

import core.cors as cors_config
from app.api.router import api_router
from core.deps import get_database
from core.database import AsyncSessionLocal
from core.logger import logger, setup_logging
from app.domains.portfolio.service import take_portfolio_snapshot_async


async def _run_snapshot():
    """APScheduler가 주기적으로 호출하는 스냅샷 저장 작업"""
    today = date.today()
    logger.info(f"[Scheduler] 스냅샷 저장 시작: {today}")
    try:
        async with AsyncSessionLocal() as session:
            snap = await take_portfolio_snapshot_async(session, today)
            if snap:
                logger.info(
                    f"[Scheduler] 스냅샷 저장 완료 | "
                    f"equity={snap.equity_krw:,.0f} KRW | "
                    f"pnl={snap.pnl_krw:+,.0f} KRW ({snap.pnl_rate:+.2f}%)"
                )
            else:
                logger.info(f"[Scheduler] 오늘({today}) 스냅샷이 이미 존재합니다. 건너뜁니다.")
    except Exception as e:
        logger.error(f"[Scheduler] 스냅샷 저장 실패: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("lifespan started")

    # APScheduler 설정
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 매일 자정(00:00)에 스냅샷 저장
    scheduler.add_job(
        _run_snapshot,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_snapshot",
        replace_existing=True,
    )

    # 매 1시간마다 스냅샷 저장 (같은 날 이미 있으면 자동 스킵)
    scheduler.add_job(
        _run_snapshot,
        trigger="interval",
        hours=1,
        id="hourly_snapshot",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] 스케줄러 시작됨 (매 1시간마다 스냅샷 저장)")

    # 서버 시작 시 즉시 1회 실행 (테스트 겸 초기 데이터 확보)
    logger.info("[Scheduler] 서버 시작 즉시 스냅샷 1회 실행...")
    await _run_snapshot()

    yield

    scheduler.shutdown()
    logger.info("[Scheduler] 스케줄러 종료됨")
    logger.info("lifespan stopped")


app = FastAPI(lifespan=lifespan)


@app.get("/db-test")
async def db_test(db: AsyncSession = Depends(get_database)):
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"db": "ok", "result": value}


cors_config.setup_cors(app)
app.include_router(api_router)
