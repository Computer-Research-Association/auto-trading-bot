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
        # TODO: I/O가 오래 걸릴 경우 run_in_executor 고려 가능하나, 
        # 현재는 pyupbit를 직접 사용하는 service logic을 그대로 활용.
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

    except Exception as e:
        logger.error(f"[Scheduler] Error during portfolio snapshot job: {str(e)}", exc_info=True)

def start_snapshot_scheduler():
    """
    스케줄러 시작 및 작업 등록
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
            max_instances=1
        )
        
        scheduler.start()
        logger.info(f"[Scheduler] Portfolio snapshot scheduler started (Cron: {settings.SNAPSHOT_CRON_HOUR:02d}:{settings.SNAPSHOT_CRON_MINUTE:02d} {settings.SNAPSHOT_TIMEZONE}).")

def stop_snapshot_scheduler():
    """
    스케줄러 안전 종료
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[Scheduler] Portfolio snapshot scheduler stopped.")
