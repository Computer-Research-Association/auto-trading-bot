from contextlib import asynccontextmanager
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

import core.cors as cors_config
from app.api.router import api_router
from core.deps import get_database
from core.database import AsyncSessionLocal
from core.logger import logger, setup_logging
from app.domains.portfolio.scheduler import start_snapshot_scheduler, stop_snapshot_scheduler
from app.domains.log.scheduler import start_log_scheduler, stop_log_scheduler
from trading.bot import TradingBot

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("lifespan started")

    # Snapshot 스케줄러 시작
    start_snapshot_scheduler()

    # Log Cleanup 스케줄러 시작
    start_log_scheduler()

    # 봇 인스턴스 생성 및 백그라운드 태스크 시작
    bot = TradingBot()
    bot_task = asyncio.create_task(bot.run())
    
    def on_bot_task_done(task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"봇 태스크 비정상 종료 (루프 탈출): {e}", exc_info=True)

    bot_task.add_done_callback(on_bot_task_done)
    app.state.bot = bot  # API 엔드포인트에서 bot 접근을 위해 저장

    yield

    # --- Graceful Shutdown ---
    # 봇 루프 취소
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass

    # 최종 상태 파일 저장 보장 (메모리 → 디스크)
    try:
        await bot.save_state()
        logger.info("봇 최종 상태 파일 저장 완료")
    except Exception as e:
        logger.error(f"봇 최종 상태 저장 실패: {e}")

    # Snapshot 스케줄러 종료
    stop_snapshot_scheduler()
    
    # Log Cleanup 스케줄러 종료
    stop_log_scheduler()
    
    logger.info("lifespan stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/db-test")
async def db_test(db: AsyncSession = Depends(get_database)):
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"db": "ok", "result": value}

cors_config.setup_cors(app)
app.include_router(api_router)
