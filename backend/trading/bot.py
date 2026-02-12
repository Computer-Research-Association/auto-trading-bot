import asyncio
import json
import os
import time
import traceback
import logging
from pathlib import Path

# 인프라 및 도구 임포트
from .load_data import DataLoader
from .db_logger import save_log_to_db
from trading.strategies.rsi_bb_strategy import RSIBBStrategy
from app.utills.upbit_client import client as upbit_client

logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, ticker="KRW-BTC"):
        # 전략 식별자 및 로그 접두어 정의
        self.ticker = ticker
        self.strategy_name = "RSI_BB"
        self.log_prefix = f"[{self.ticker}_{self.strategy_name}]"
        # data loader 및 전략 인스턴스화
        self.loader = DataLoader(ticker=self.ticker)
        self.strategy = RSIBBStrategy()
        # [Pathlib] 실행 환경 불변 절대 경로 설정
        self.base_dir = Path(__file__).parent.resolve()
        self.state_file = self.base_dir / "bot_state.json"
        # 파일 수정 시간 추적
        self.last_file_mtime = 0.0

        # 초기 상태 로드
        self.state = self.load_state_sync()

        # 하트비트 설정
        self.heartbeat_interval = 5
        self.last_heartbeat_time = 0

    # -----------------------------------------------------------
    # [Properties] 간결한 상태 확인
    # -----------------------------------------------------------
    @property
    def is_active(self) -> bool: return self.state.get("is_active", False)

    @property
    def is_holding(self) -> bool: return self.state.get("is_holding", False)

    # -----------------------------------------------------------
    # [Core Logic] API 동기화 및 데이터 정합성
    # -----------------------------------------------------------
    async def sync_state_with_api(self):
        """[Source of Truth] 실제 계좌 상태와 메모리/장부를 강제 동기화"""
        try:
            # 1. 시세 조회 (실패 시 중단)
            current_price = await self.loader.get_current_price()
            if not current_price:
                return logger.warning(f"{self.log_prefix} 시세 조회 실패로 동기화 건너뜀")

            # 2. 계좌 정보 조회
            actual_krw = self.upbit_client.get_krw_balance()
            actual_coin_bal = self.upbit_client.get_coin_balance(self.ticker)
            
            # 3. 미세 잔고(Dust) 처리: 5,000원 미만은 미보유로 판단
            is_holding = (actual_coin_bal * current_price) >= 5000
            avg_buy_price = self.upbit_client.get_avg_buy_price(self.ticker) if is_holding else 0

            # 4. 상태 갱신 및 저장
            self.state.update({
                "balance": actual_krw,
                "is_holding": is_holding,
                "avg_buy_price": avg_buy_price
            })
            await self.save_state()
            self.last_sync_time = time.time()

            await save_log_to_db(
                level="INFO", category="SYSTEM", event_name="SYNC",
                message=f"{self.log_prefix} API 동기화 완료 (보유: {is_holding}, 잔고: {actual_krw:,.0f}원)"
            )

        except Exception:
            await save_log_to_db(
                level="ERROR", category="SYSTEM", event_name="ERROR",
                message=f"{self.log_prefix} API 동기화 실패: {traceback.format_exc()}"
            )

    # -----------------------------------------------------------
    # [State Management] 파일 I/O 및 병합
    # -----------------------------------------------------------
    def load_state_sync(self):
        """기동 시 동기 로드 (가드 클로즈 적용)"""
        if not self.state_file.exists():
            return self._get_default_state()  # 초기 상태 반환
            
        try:
            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.last_file_mtime = (
                        self.state_file.stat().st_mtime
                    )  # 마지막 파일 수정 시간 기록
                    return state
        except Exception:
            logger.error(f"초기 상태 로드 실패: {traceback.format_exc()}")

        return {  # 로드 실패 시 기본값 반환
            "is_active": False,
            "is_holding": False,
            "avg_buy_price": 0,
            "target_price": 0,
            "stop_loss": 0,
            "balance": 10000,
            "last_reason": "",
        }

    async def load_state_async(self):
        """비동기 로드: 파일 수정 시에만 병합 (가드 클로즈)"""
        if not self.state_file.exists(): return

        current_stat = self.state_file.stat() 
        if current_stat.st_mtime == self.last_file_mtime: return  

        await self._read_and_merge_state(current_stat.st_mtime)

    async def _read_and_merge_state(self, current_mtime):
        """실제 파일 읽기 및 병합 로직 (분리됨)
        is_active 값만 읽고 로그"""

        def _read():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)

        file_state = await asyncio.to_thread(_read)
        sync_keys = ["is_active", "is_holding", "avg_buy_price", "target_price", "stop_loss", "balance"]
        
        for key in sync_keys:
            if key not in file_state: continue
            
            # 사용자 명령(is_active) 변경 로그 처리
            if key == "is_active" and self.state.get(key) != file_state[key]:
                await self._log_command_change(file_state[key])
            
            self.state[key] = file_state[key]

        # [Selective Merge] 사용자 명령(is_active)만 반영
        if "is_active" in file_state:
            new_active = file_state["is_active"]
            if self.is_active != new_active:
                log_msg = "가동 시작" if new_active else "정지 명령 수신"
                await save_log_to_db(
                    level="INFO",
                    category="SYSTEM",
                    event_name="COMMAND",
                    message=f"{self.log_prefix} 사용자 명령 변경: {self.is_active} -> {new_active} ({log_msg})",
                )
            self.state["is_active"] = new_active  # is_active 값만 갱신

        self.last_file_mtime = (
            current_mtime  # bot_state.json 파일의 최신 수정 시간 갱신
        )

    async def save_state(self):
        """원자적 저장 (Atomic Save)"""
        temp_file = self.state_file.with_suffix(".json.tmp")
        def _atomic_save():
            try:  # 임시 파일에 저장 후 교체, 그리고 파일ㄴ 수정 시간 갱신
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self.state, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, self.state_file)
                self.last_file_mtime = self.state_file.stat().st_mtime
            except Exception as e:
                if temp_file.exists(): os.remove(temp_file)
                raise e
        await asyncio.to_thread(_atomic_save)

    # -----------------------------------------------------------
    # [Trade Execution] 매매 명령 실행
    # -----------------------------------------------------------
    async def execute_buy(self, price, reason, trade_params):
        self.state.update(
            {  # 매수 시 상태 업데이트
                "is_holding": True,
                "avg_buy_price": price,
                "target_price": trade_params.get(
                    "target_price", price * 1.05
                ),  # 지정 목표가 없을 경우 5% 상향
                "stop_loss": trade_params.get(
                    "stop_loss", price * 0.95
                ),  # 지정 손절가 없을 경우 5% 하향
                "last_reason": f"[매수] {reason}",
            }
        )

        await self.save_state()
        await self.sync_state_with_api() # 체결 직후 동기화
        
        await save_log_to_db(
            level="INFO",
            category="TRADE",
            event_name="BUY",
            message=f"{self.log_prefix} {self.state['last_reason']} | 매수가: {price:,.0f}",
        )

    async def execute_sell(self, price, reason, event_name="SELL"):
        avg_price = self.state.get("avg_buy_price", 0)  # 평균 매수가 로드
        profit_pct = (
            ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
        )  # 수익 계산 및 ZeroDivision 방지
        log_msg = f"[매도] {reason} | 수익률: {profit_pct:.2f}%"

        self.state.update(
            {  # 매도 시 상태 업데이트
                "is_holding": False,
                "avg_buy_price": 0,
                "target_price": 0,
                "stop_loss": 0,
                "last_reason": log_msg,
            }
        )

        await self.save_state()
        level = (
            "WARNING" if event_name == "STOPLOSS" else "INFO"
        )  # stoploss 시 warning 레벨
        await save_log_to_db(
            level=level,
            category="TRADE",
            event_name=event_name,
            message=f"{self.log_prefix} {log_msg} | 매도가: {price:,.0f}",
        )

    # -----------------------------------------------------------
    # [Main Loops] 감시 및 분석 루프
    # -----------------------------------------------------------
    async def monitor_market_loop(self):
        """[파수꾼] 0.2초 주기: 즉각적인 매도(익절/손절) 감시"""
        while True:
            try:
                await self.load_state_async()  # 파일 내 변경사항이 있을 때 비동기 로드
                await self.check_heartbeat()  # 하트비트 로그

                # 가드 클로즈: 비활성 또는 미보유 시 스킵
                if not self.is_active or not self.is_holding:
                    await asyncio.sleep(0.2)
                    continue

                # [Refactor] 복잡한 분석 로직은 별도 메서드로 위임
                await self._process_strategy_analysis()
                await asyncio.sleep(10)

            except Exception:
                await save_log_to_db(
                    level="ERROR",
                    category="SYSTEM",
                    event_name="ERROR",
                    message=f"{self.log_prefix} 분석 루프 예외: {traceback.format_exc()}",
                )
                await asyncio.sleep(10)

    async def _process_strategy_analysis(self):
        """[Refactor] 비즈니스 로직 분리: 실제 데이터 분석 및 매매 결정"""
        # ohlcv 데이터 로드
        df = await self.loader.fetch_ohlcv()

        # [Guard] 데이터 로드 실패 시 종료
        if df is None:
            return

        is_valid, msg = self.strategy.validate_data(df)
        # [Guard] 데이터 유효성 검증 실패 시 종료
        if not is_valid:
            return

        # 전략 실행
        df_indicators = self.strategy.setup_indicators(df)
        result = self.strategy.decide(df_indicators, self.state, {})
        current_close = df_indicators["close"].iloc[-1]
        trade_params = result.get("trade_params", {})

        # 1. 미보유 상태 -> 매수 판단
        if not self.is_holding:
            if result["decision"] == "BUY":
                await self.execute_buy(current_close, result["reason"], trade_params)
            return

        # 2. 보유 상태 -> 목표가 업데이트 (Trailing Stop 등)
        new_target = trade_params.get("target_price", self.state["target_price"])
        if new_target != self.state["target_price"]:
            self.state["target_price"] = new_target
            await self.save_state()
            await save_log_to_db(
                level="INFO",
                category="STRATEGY",
                event_name="DECISION",
                message=f"{self.log_prefix} 목표가 업데이트: {new_target:,.0f}",
            )

    async def monitor_market_loop(self):
        """[파수꾼] 0.2초 주기: 즉각적인 반응을 위해 최적화됨
        매도 조건 감시 담당, 하트비트 포함"""
        while True:
            try:
                await self.load_state_async()  # bot_state.json 변경사항 있으면 로드
                if not self.is_active:
                    await asyncio.sleep(1); continue  # 비활성 시 대기 시간은 1초

                # 주기적 무결성 체크 (1시간)
                if time.time() - self.last_sync_time >= 3600:
                    await self.sync_state_with_api()

                await self._process_strategy_analysis()
                await asyncio.sleep(10)  # 매수 판단은 10초 주기
            except Exception:
                await save_log_to_db(
                    level="ERROR",
                    category="SYSTEM",
                    event_name="ERROR",
                    message=f"{self.log_prefix} [파수꾼] 감시 루프 예외: {traceback.format_exc()}",
                )
                await asyncio.sleep(1)

    async def _check_market_conditions(self):
        """[Refactor] 로직 분리: 익절/손절 조건 체크"""
        current_price = await self.loader.get_current_price()
        if current_price is None:
            return

        # 익절 감시
        if current_price >= self.state["target_price"]:
            await self.execute_sell(current_price, "익절가 도달", event_name="SELL")
            return

        # 손절 감시
        if self.state["stop_loss"] > 0 and current_price <= self.state["stop_loss"]:
            await self.execute_sell(
                current_price, "스탑로스 도달", event_name="STOPLOSS"
            )

    async def check_heartbeat(self):
        current_time = time.time()
        if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
            msg = (
                f"[매매 가동 중] 엔진 생존 신고 (보유: {self.is_holding})"
                if self.is_active
                else "[대기 모드] 엔진 생존 신고 (사용자 명령 대기 중)"
            )

            await save_log_to_db(
                level="INFO",
                category="SYSTEM",
                event_name="HEARTBEAT",
                message=f"{self.log_prefix} {msg}",
            )
            self.last_heartbeat_time = current_time
    # -----------------------------------------------------------
    # [Helpers] 내부 보조 메서드 (Flattening을 위한 분리)
    # -----------------------------------------------------------
    async def _check_market_conditions(self):
        """
        즉각적인 매도 조건(익절/손절) 체크 및 실행(execute_sell 호출)
        1. 현재가 조회
        2. 익절가 도달 시 매도
        3. 손절가 도달 시 매도
        4. 조건 미충족 시 종료
        """
        current_price = await self.loader.get_current_price()  # 현재가를 dataloader에서 조회
        if not current_price: return  # 시세 조회 실패 시 중단

        # 익절 체크
        if current_price >= self.state["target_price"]:
            return await self.execute_sell(current_price, "익절가 도달")

        # 손절 체크
        if self.state["stop_loss"] > 0 and current_price <= self.state["stop_loss"]:
            await self.execute_sell(current_price, "스탑로스 도달", "STOPLOSS")

    async def _process_strategy_analysis(self):
        df = await self.loader.fetch_ohlcv()  # 최신 ohlcv 데이터 로드ㄴ
        if df is None: return
        
        is_valid, _ = self.strategy.validate_data(df)
        if not is_valid: return

        df_indicators = self.strategy.setup_indicators(df)  #
        result = self.strategy.decide(df_indicators, self.state, {})
        current_close = df_indicators['close'].iloc[-1]
        
        # 1. 미보유 시 -> 매수 판단
        if not self.is_holding:
            if result["decision"] == "BUY":
                await self.execute_buy(current_close, result["reason"], result.get("trade_params", {}))
            return

        # 2. 보유 시 -> 목표가 갱신 로직
        await self._update_target_price(result.get("trade_params", {}))

    async def _update_target_price(self, trade_params):
        new_target = trade_params.get("target_price", self.state["target_price"])
        if new_target == self.state["target_price"]: return

        self.state["target_price"] = new_target
        await self.save_state()
        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="ENGINE_START",
            message=f"{self.log_prefix} 비동기 고속 엔진 가동 (Cycle: 0.2s)",
        )

    def _get_default_state(self):
        return {"is_active": False, "is_holding": False, "avg_buy_price": 0, 
                "target_price": 0, "stop_loss": 0, "balance": 0, "last_reason": ""}

    async def _log_command_change(self, new_active):
        msg = "가동 시작" if new_active else "정지 명령 수신"
        await save_log_to_db(level="INFO", category="SYSTEM", event_name="COMMAND",
                             message=f"{self.log_prefix} 사용자 명령 변경: {not new_active} -> {new_active} ({msg})")

    async def _log_loop_error(self, loop_name, error_trace):
        await save_log_to_db(level="ERROR", category="SYSTEM", event_name="ERROR",
                             message=f"{self.log_prefix} {loop_name} 예외: {error_trace}")
        await asyncio.sleep(5)

    async def run(self):
        await self.sync_state_with_api() # 시작 시 강제 동기화
        await save_log_to_db(level="INFO", category="SYSTEM", event_name="ENGINE_START",
                             message=f"{self.log_prefix} 비동기 클린 엔진 가동")
        await asyncio.gather(self.monitor_market_loop(), self.perform_analysis_loop())


if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())