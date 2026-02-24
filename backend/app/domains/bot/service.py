from trading.bot import TradingBot
from datetime import datetime

class BotService:
    def __init__(self, bot: TradingBot):
        self.bot = bot

    async def start(self) -> dict:
        changed = await self.bot.set_active(True)
        if not changed:
            return {"status": "already started", "is_active": True}
        return {"status": "bot started", "is_active": True}

    async def stop(self) -> dict:
        changed = await self.bot.set_active(False)
        if not changed:
            return {"status": "already stopped", "is_active": False}
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
            "is_dry_run": snapshot.get("is_dry_run", False),
            "strategy_name": snapshot.get("strategy_name", "Unknown"),
            "balance": snapshot.get("balance", 0),
            "is_holding": snapshot.get("is_holding", False),
            "avg_buy_price": avg_price,
            "target_price": snapshot.get("target_price", 0), # Deprecated 방어
            "stop_loss": snapshot.get("stop_loss", 0),       # Deprecated 방어
            "target_buy_price": snapshot.get("target_buy_price", 0.0),
            "target_sell_price": snapshot.get("target_sell_price", 0.0),
            "target_stop_loss": snapshot.get("target_stop_loss", 0.0),
            "last_reason": snapshot.get("last_reason", ""),
            "timestamp": snapshot.get("timestamp"),
            "profit_rate": profit_rate
        }

    async def toggle_dry_run(self, enable: bool) -> dict:
        async with self.bot._lock:
            self.bot.state["is_dry_run"] = enable
            await self.bot.save_state()
        
        from core.logger import logger
        from trading.db_logger import save_log_to_db
        
        status_str = "ON (모의투자)" if enable else "OFF (실제 매매)"
        
        logger.info(f"사용자 명령에 의해 모의투자(Dry Run) 모드가 {status_str}로 변경되었습니다.")
        
        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="COMMAND",
            message=f"{self.bot.log_prefix} 모의투자(Dry-Run) 스위치 변경: {status_str}",
        )
        return {"status": "dry run updated", "is_dry_run": enable}
