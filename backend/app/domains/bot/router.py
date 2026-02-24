from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from app.domains.bot.schemas import BotStatusResponse
from app.domains.bot.service import BotService
from app.domains.bot.deps import get_bot
from trading.bot import TradingBot

router = APIRouter()

@router.post("/start")
async def start_bot(bot: TradingBot = Depends(get_bot)):
    service = BotService(bot)
    return await service.start()

@router.post("/stop")
async def stop_bot(bot: TradingBot = Depends(get_bot)):
    service = BotService(bot)
    return await service.stop()

@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(bot: TradingBot = Depends(get_bot)):
    service = BotService(bot)
    return await service.get_status()

@router.post("/dry-run")
async def toggle_dry_run(enable: bool, bot: TradingBot = Depends(get_bot)):
    service = BotService(bot)
    return await service.toggle_dry_run(enable)

@router.get("/stream")
async def stream_bot_status(request: Request, bot: TradingBot = Depends(get_bot)):
    """
    1초 단기 폴링(Short Polling)의 API 부하를 없애고
    SSE(Server-Sent Events)를 통해 주기적으로 상태를 Push합니다.
    """
    service = BotService(bot)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                # 메모리에 저장된 봇의 상태 반환 (Upbit API 호출 없음)
                status = await service.get_status()
                
                yield {
                    "event": "message",
                    "data": json.dumps(status, ensure_ascii=False)
                }
                
                # 프론트엔드 반영 주기 및 지휘관 루프(3초) 고려
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            pass

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return EventSourceResponse(event_generator(), headers=headers)
