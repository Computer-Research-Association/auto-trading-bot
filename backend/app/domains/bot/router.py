from fastapi import APIRouter, Depends
from app.domains.bot.schemas import BotStatusResponse
from app.domains.bot.service import BotService
from app.domains.bot.dependencies import get_bot
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
