import asyncio
from datetime import datetime, date
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.settings import settings
from core.logger import logger
from app.domains.portfolio.service import get_assets
from app.domains.portfolio.models import PortfolioSnapshot

scheduler = AsyncIOScheduler()

async def save_portfolio_snapshot_job():
    """
    매일 정해진 시간에 실행되어 포트폴리오 스냅샷을 저장하는 작업.
    """
    logger.info("[Scheduler] Portfolio snapshot job started.")
    
    try:
        # 1. 자산 데이터 조회 (sync service logic)
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, get_assets)
        s = resp.summary
        
        base_date = datetime.now(pytz.timezone(settings.SNAPSHOT_TIMEZONE)).date()
        
        invested_krw = float(s.total_buy_krw)
        equity_krw = float(s.total_assets_krw)
        pnl_krw = equity_krw - invested_krw
        pnl_rate = (pnl_krw / invested_krw * 100.0) if invested_krw > 0 else 0.0
        
        assets_payload = {
            "krw_total": float(s.krw_total),
            "krw_available": float(s.krw_available),
            "items": [
                {
                    "symbol": it.symbol,
                    "quantity": float(it.quantity),
                    "avg_buy_price": float(it.avg_buy_price),
                    "current_price": float(it.current_price),
                    "evaluation_krw": float(it.evaluation_krw),
                }
                for it in resp.items
            ],
        }

        # 2. 비동기 세션을 사용하여 DB 저장
        async with AsyncSessionLocal() as session:
            # 중복 체크 (upsert 처리)
            stmt = select(PortfolioSnapshot).where(PortfolioSnapshot.base_date == base_date)
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            if existing:
                logger.info(f"[Scheduler] Already exists snapshot for {base_date}. Updating...")
                existing.invested_krw = invested_krw
                existing.equity_krw = equity_krw
                existing.pnl_krw = pnl_krw
                existing.pnl_rate = pnl_rate
                existing.assets = assets_payload
            else:
                logger.info(f"[Scheduler] Creating new snapshot for {base_date}.")
                snap = PortfolioSnapshot(
                    base_date=base_date,
                    invested_krw=invested_krw,
                    equity_krw=equity_krw,
                    pnl_krw=pnl_krw,
                    pnl_rate=pnl_rate,
                    assets=assets_payload,
                )
                session.add(snap)
            
            await session.commit()
            logger.info(f"[Scheduler] Portfolio snapshot saved successfully for {base_date}.")

            # SNAPSHOT_SAVED 로그 추가 (Best-effort, 기존 세션 재사용)
            try:
                from app.domains.log.logger import create_log
                await create_log(
                    db=session,
                    level="INFO",
                    category="SYSTEM",
                    event_name="SNAPSHOT_SAVED",
                    message=f"{base_date} 포트폴리오 스냅샷이 성공적으로 저장되었습니다."
                )
            except Exception:
                logger.warning(f"[Log] Failed to record SNAPSHOT_SAVED log for {base_date}.")

    except Exception as e:
        logger.error(f"[Scheduler] Error during portfolio snapshot job: {str(e)}", exc_info=True)
        # SNAPSHOT_FAILED 로그 추가 (Best-effort, 새 세션 사용)
        try:
            from app.domains.log.logger import create_log
            async with AsyncSessionLocal() as db_err:
                await create_log(
                    db=db_err,
                    level="ERROR",
                    category="SYSTEM",
                    event_name="SNAPSHOT_FAILED",
                    message=f"스냅샷 저장 중 오류 발생: {str(e)}"
                )
        except Exception:
            logger.exception("[DB_LOG_FAIL] SNAPSHOT_FAILED")

def start_snapshot_scheduler():
    """
    스케줄러 시작 및 작업 등록.
    서버 시작 시 오늘 스냅샷이 없으면 즉시 1회 저장 후 cron 등록.
    """
    if not scheduler.running:
        trigger = CronTrigger(
            hour=settings.SNAPSHOT_CRON_HOUR,
            minute=settings.SNAPSHOT_CRON_MINUTE,
            timezone=pytz.timezone(settings.SNAPSHOT_TIMEZONE)
        )

        scheduler.add_job(
            save_portfolio_snapshot_job,
            trigger=trigger,
            id="save_portfolio_snapshot",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=10  # 10초 허용
        )

        # 서버 시작 시 오늘 스냅샷이 없으면 즉시 1회 실행
        scheduler.add_job(
            _run_snapshot_if_missing_today,
            trigger="date",  # 즉시 1회 실행
            id="save_portfolio_snapshot_on_startup",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(f"[Scheduler] Portfolio snapshot scheduler started (Cron: {settings.SNAPSHOT_CRON_HOUR:02d}:{settings.SNAPSHOT_CRON_MINUTE:02d} {settings.SNAPSHOT_TIMEZONE}).")


async def _run_snapshot_if_missing_today():
    """
    서버 시작 시 오늘 날짜 스냅샷이 DB에 없을 때만 즉시 1회 저장.
    중복 저장을 방지하기 위해 먼저 조회 후 진행.
    """
    import pytz
    from core.settings import settings

    base_date = datetime.now(pytz.timezone(settings.SNAPSHOT_TIMEZONE)).date()

    async with AsyncSessionLocal() as session:
        stmt = select(PortfolioSnapshot).where(PortfolioSnapshot.base_date == base_date)
        result = await session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            logger.info(f"[Scheduler] Startup check: snapshot for {base_date} already exists. Skipping.")
            return

    logger.info(f"[Scheduler] Startup check: no snapshot for {base_date}. Taking snapshot now...")
    await save_portfolio_snapshot_job()

def stop_snapshot_scheduler():
    """
    스케줄러 안전 종료
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Portfolio snapshot scheduler stopped.")
