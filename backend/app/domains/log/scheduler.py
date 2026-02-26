import asyncio
from datetime import datetime
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.settings import settings
from core.logger import logger
from app.domains.log.service import delete_old_logs

scheduler = AsyncIOScheduler()

async def delete_old_log_job():
    """
    매일 설정된 시간에 실행되어 오래된 로그를 삭제하는 작업.
    """
    logger.info("[Scheduler] Log cleanup job started.")
    try:
        async with AsyncSessionLocal() as session:
            await delete_old_logs(session)
            
            # 성공 로그 기록
            try:
                from app.domains.log.logger import create_log
                await create_log(
                    db=session,
                    level="INFO",
                    category="SYSTEM",
                    event_name="LOG_CLEANUP_SUCCESS",
                    message="로그 정리 작업이 성공적으로 완료되었습니다.",
                    commit=True
                )
            except Exception:
                logger.warning("[Scheduler] Failed to record LOG_CLEANUP_SUCCESS log.")
    except Exception as e:
        logger.error(f"[Scheduler] Error during log cleanup job: {str(e)}", exc_info=True)
        # 에러 로그 기록용 새 세션
        try:
            from app.domains.log.logger import create_log
            async with AsyncSessionLocal() as db_err:
                await create_log(
                    db=db_err,
                    level="ERROR",
                    category="SYSTEM",
                    event_name="LOG_CLEANUP_FAILED",
                    message=f"로그 정리 중 오류 발생: {str(e)}",
                    commit=True
                )
        except Exception:
            logger.exception("[DB_LOG_FAIL] LOG_CLEANUP_FAILED")

def start_log_scheduler():
    """
    로그 청소 스케줄러 시작 및 작업 등록
    """
    if not scheduler.running:
        trigger = CronTrigger(
            hour=settings.LOG_CLEANUP_CRON_HOUR,
            minute=settings.LOG_CLEANUP_CRON_MINUTE,
            timezone=pytz.timezone(settings.SNAPSHOT_TIMEZONE)
        )
        
        scheduler.add_job(
            delete_old_log_job,
            trigger=trigger,
            id="cleanup_old_logs",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=60
        )
        
        scheduler.start()
        logger.info(f"[Scheduler] Log cleanup scheduler started (Cron: {settings.LOG_CLEANUP_CRON_HOUR:02d}:{settings.LOG_CLEANUP_CRON_MINUTE:02d} {settings.SNAPSHOT_TIMEZONE}).")

def stop_log_scheduler():
    """
    로그 청소 스케줄러 안전 종료
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Log cleanup scheduler stopped.")
