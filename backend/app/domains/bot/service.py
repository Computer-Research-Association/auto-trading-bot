import asyncio
import pyupbit
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
        
        # 봇의 메모리에서 직접 수익률을 꺼냄 (API 호출 없이 0.2초마다 자동 갱신됨)
        profit_rate = snapshot.get("profit_rate", 0.0)

        # ✨ 스파크라인용 1분봉 데이터 추가 획득 (Upbit API 호출)
        sparkline_data = []
        try:
            ticker = self.bot.ticker if hasattr(self.bot, 'ticker') else "KRW-BTC"
            # 1분봉으로 최근 20개 가져오기
            df = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="minute1", count=20)
            if df is not None and not df.empty:
                sparkline_data = df['close'].tolist()
        except Exception as e:
            from core.logger import logger
            logger.warning(f"스파크라인 데이터 조회 실패: {e}")

        # API 응답 포맷 매핑
        return {
            "is_active": snapshot.get("is_active", False),
            "is_dry_run": snapshot.get("is_dry_run", False),
            "strategy_name": snapshot.get("strategy_name", "Unknown"),
            "balance": snapshot.get("balance", 0),
            "is_holding": snapshot.get("is_holding", False),
            "avg_buy_price": snapshot.get("avg_buy_price", 0),
            "target_price": snapshot.get("target_price", 0), # Deprecated 방어
            "stop_loss": snapshot.get("stop_loss", 0),       # Deprecated 방어
            "target_buy_price": snapshot.get("target_buy_price", 0.0),
            "target_sell_price": snapshot.get("target_sell_price", 0.0),
            "target_stop_loss": snapshot.get("target_stop_loss", 0.0),
            "last_reason": snapshot.get("last_reason", ""),
            "timestamp": snapshot.get("timestamp"),
            "profit_rate": profit_rate,
            "sparkline_data": sparkline_data
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
