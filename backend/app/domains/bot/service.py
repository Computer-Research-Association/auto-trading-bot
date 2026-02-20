from trading.bot import TradingBot
from datetime import datetime

class BotService:
    def __init__(self, bot: TradingBot):
        self.bot = bot

    async def start(self) -> dict:
        if self.bot.is_active:
            return {"status": "already started", "is_active": True}
        
        await self.bot.set_active(True)
        return {"status": "bot started", "is_active": True}

    async def stop(self) -> dict:
        if not self.bot.is_active:
            return {"status": "already stopped", "is_active": False}
            
        await self.bot.set_active(False)
        return {"status": "bot stopped", "is_active": False}

    async def get_status(self) -> dict:
        # Use cached snapshot to avoid Rate Limit
        snapshot = await self.bot.get_snapshot()
        
        # 서비스 계층에서 수익률 계산
        current_price = await self.bot.loader.get_current_price() or 0
        avg_price = snapshot.get("avg_buy_price", 0)
        
        if snapshot.get("is_holding") and avg_price > 0 and current_price > 0:
            profit_rate = ((current_price - avg_price) / avg_price) * 100
        else:
            profit_rate = 0.0

        # API 응답 포맷 매핑
        return {
            "is_active": snapshot.get("is_active", False),
            "strategy_name": snapshot.get("strategy_name", "Unknown"),
            "balance": snapshot.get("balance", 0),
            "is_holding": snapshot.get("is_holding", False),
            "avg_buy_price": avg_price,
            "target_price": snapshot.get("target_price", 0),
            "stop_loss": snapshot.get("stop_loss", 0),
            "last_reason": snapshot.get("last_reason", ""),
            "timestamp": snapshot.get("timestamp"),
            "profit_rate": profit_rate
        }
