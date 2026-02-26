import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import AsyncSessionLocal
from core.logger import logger
from app.domains.coin.service import sync_trade_history

# 전용 스케줄러 인스턴스
scheduler = AsyncIOScheduler()

async def trade_sync_job():
    """
    60초마다 실행되어 Upbit 체결 내역을 동기화하는 작업.
    """
    try:
        async with AsyncSessionLocal() as session:
            await sync_trade_history(session)
    except Exception as e:
        logger.error(f"[Scheduler] Error in trade_sync_job: {e}", exc_info=True)

def start_trade_sync_scheduler():
    """
    스케줄러 시작 및 작업 등록
    """
    if not scheduler.running:
        # 실행 간격 (초)
        SYNC_INTERVAL_SECONDS = 60
        
        scheduler.add_job(
            trade_sync_job,
            "interval",
            seconds=SYNC_INTERVAL_SECONDS,
            id="upbit_trade_sync",
            replace_existing=True,
            coalesce=True,
            max_instances=1 # 동시 실행 방지
        )
        
        scheduler.start()
        logger.info(f"[Scheduler] Trade sync scheduler started (Interval: {SYNC_INTERVAL_SECONDS}s).")

def stop_trade_sync_scheduler():
    """
    스케줄러 종료
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Trade sync scheduler stopped.")
