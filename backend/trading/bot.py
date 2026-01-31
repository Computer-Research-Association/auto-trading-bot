import asyncio
import json
import os
import time
import traceback
import logging
from datetime import datetime

# 인프라 및 도구 임포트
from .load_data import DataLoader
from .db_logger import save_log_to_db
from trading.strategies.rsi_bb_strategy import RSIBBStrategy

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, ticker="KRW-BTC"):
        # 전략 식별자 및 로그 접두어 정의
        self.ticker = ticker
        self.strategy_name = "RSI_BB"
        self.log_prefix = f"[{self.ticker}_{self.strategy_name}]"
        
        self.loader = DataLoader(ticker=self.ticker)
        self.strategy = RSIBBStrategy()
        self.state_file = r".\trading\bot_state.json"

        # 초기 상태 로드
        self.state = self.load_state_sync()
        self.dry_run = True 
        
        # 하트비트 설정 (테스트용 5초)
        self.heartbeat_interval = 5 
        self.last_heartbeat_time = 0

    def load_state_sync(self):
        """기존 JSON 상태 로드 로직"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state
        except Exception:
            pass
        return {
            "is_active": False, "is_holding": False, "avg_buy_price": 0, 
            "target_price": 0, "stop_loss": 0, "balance": 1000000, "last_reason": ""
        }

    async def save_state(self):
        """ 비동기 파일 저장 (데이터 정합성 보장)"""
        def _save():
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        await asyncio.to_thread(_save)

    async def execute_buy(self, price, reason, trade_params):
        """ 매수 실행 및 즉시 상태 동기화"""
        self.state["is_holding"] = True
        self.state["avg_buy_price"] = price
        # 지휘부가 설정한 목표가/손절가 저장
        self.state["target_price"] = trade_params.get("target_price", price * 1.05)
        self.state["stop_loss"] = trade_params.get("stop_loss", price * 0.95)
        
        log_msg = f"[매수] {reason}"
        self.state["last_reason"] = log_msg
        
        # [권장사항 반영] 매수 즉시 파일 저장
        await self.save_state()
        
        await save_log_to_db(
            level="INFO", category="TRADE", event_name="BUY",
            message=f"{self.log_prefix} {log_msg} | 매수가: {price:,.0f} | 목표가: {self.state['target_price']:,.0f}"
        )

    async def execute_sell(self, price, reason, event_name="SELL"):
        """ 매도 실행 및 수익률 정산 (ZeroDivision 방어 추가)"""
        # [수정] ZeroDivisionError 방지 로직 적용
        avg_price = self.state.get("avg_buy_price", 0)
        profit_pct = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
        
        log_msg = f"[매도] {reason} | 수익률: {profit_pct:.2f}%"
        
        self.state["is_holding"] = False
        self.state["avg_buy_price"] = 0
        self.state["target_price"] = 0
        self.state["stop_loss"] = 0
        self.state["last_reason"] = log_msg

        # [권장사항 반영] 매도 즉시 파일 저장
        await self.save_state()

        level = "WARNING" if event_name == "STOPLOSS" else "INFO"
        await save_log_to_db(
            level=level, category="TRADE", event_name=event_name,
            message=f"{self.log_prefix} {log_msg} | 매도가: {price:,.0f}"
        )

    async def perform_analysis_loop(self):
        """ 지휘부 루프: 10초마다 전략 분석 및 과녁(Target) 최신화"""
        while True:
            try:
                if not self.state.get("is_active", False):
                    await asyncio.sleep(10)
                    continue

                df = await self.loader.fetch_ohlcv()
                if df is not None:
                    is_valid, msg = self.strategy.validate_data(df)
                    if is_valid:
                        df_indicators = self.strategy.setup_indicators(df)
                        result = self.strategy.decide(df_indicators, self.state, {})
                        
                        current_close = df_indicators['close'].iloc[-1]
                        trade_params = result.get("trade_params", {})

                        if not self.state["is_holding"]:
                            if result["decision"] == "BUY":
                                await self.execute_buy(current_close, result["reason"], trade_params)
                        else:
                            # 보유 중 목표가 실시간 업데이트
                            new_target = trade_params.get("target_price", self.state["target_price"])
                            if new_target != self.state["target_price"]:
                                self.state["target_price"] = new_target
                                await self.save_state() 
                                await save_log_to_db(
                                    level="INFO", category="STRATEGY", event_name="DECISION",
                                    message=f"{self.log_prefix} 목표가 업데이트: {new_target:,.0f}"
                                )

                await asyncio.sleep(10)
            except Exception:
                await save_log_to_db(
                    level="ERROR", category="SYSTEM", event_name="ERROR",
                    message=f"{self.log_prefix} 분석 루프 예외: {traceback.format_exc()}"
                )
                await asyncio.sleep(10)

    async def monitor_market_loop(self):
        """ 파수꾼 루프: 1초마다 실시간 익절/손절 감시"""
        while True:
            try:
                # [권장사항 반영] 루프 최상단에서 하트비트 호출
                await self.check_heartbeat()

                if self.state.get("is_active", False) and self.state["is_holding"]:
                    current_price = await self.loader.get_current_price()
                    
                    if current_price is not None:
                        # [권장사항 반영] 익절가(Target Price) 감시 추가
                        if current_price >= self.state["target_price"]:
                            await self.execute_sell(current_price, "익절가 도달", event_name="SELL")
                        
                        # 손절가(Stop-loss) 감시
                        elif self.state["stop_loss"] > 0 and current_price <= self.state["stop_loss"]:
                            await self.execute_sell(current_price, "스탑로스 도달", event_name="STOPLOSS")
                
                await asyncio.sleep(1)
            except Exception:
                await save_log_to_db(
                    level="ERROR", category="SYSTEM", event_name="ERROR",
                    message=f"{self.log_prefix} 감시 루프 예외: {traceback.format_exc()}"
                )
                await asyncio.sleep(1)

    async def check_heartbeat(self):
        """ 가변 하트비트 로직"""
        current_time = time.time()
        if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
            await save_log_to_db(
                level="INFO", category="SYSTEM", event_name="HEARTBEAT",
                message=f"{self.log_prefix} 엔진 생존 신고 (보유: {self.state['is_holding']})"
            )
            self.last_heartbeat_time = current_time

    async def run(self):
        """ 엔진 가동 진입점"""
        await save_log_to_db(
            level="INFO", category="SYSTEM", event_name="ENGINE_START",
            message=f"{self.log_prefix} 비동기 이중 루프 엔진 가동"
        )
        # 분석과 감시 태스크 병렬 실행
        await asyncio.gather(self.monitor_market_loop(), self.perform_analysis_loop())
        # await asyncio.gather(self.perform_analysis_loop(), self.monitor_market_loop())

if __name__ == "__main__":
    bot = TradingBot()
    # 비동기 루프 시작
    asyncio.run(bot.run())