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

# -----------------------------------------------------------
# [Constants] 상수 정의
# -----------------------------------------------------------
# bot_state.json에 저장할 키 목록 (Persistent State)
# is_holding, balance, avg_buy_price는 저장하지 않음 (API Fact)
_PERSISTENT_KEYS = {"is_active", "target_price", "stop_loss", "last_reason"}

# API 호출 최소 대기 시간 (Rate Limit 방어, 초)
_MIN_API_INTERVAL = 0.15

# target_price 저장 스로틀 (초) - 최대 10초에 1회
_TARGET_PRICE_SAVE_THROTTLE = 10.0


class TradingBot:
    def __init__(self, ticker="KRW-BTC"):
        self.ticker = ticker  # 거래 대상 티커
        self.strategy_name = "RSI_BB"  # 전략 식별자
        self.log_prefix = f"[{self.ticker}_{self.strategy_name}]"  # 로그 식별자

        # 의존성 주입
        self.upbit_client = upbit_client  # UpbitClient 인스턴스
        self.loader = DataLoader(ticker=self.ticker)  # 데이터 로더 인스턴스
        self.strategy = RSIBBStrategy()  # 전략 인스턴스

        # 경로 및 상태 관리 변수
        self.base_dir = Path(__file__).parent.resolve()  # 현재 파일 디렉토리
        self.state_file = self.base_dir / "bot_state.json"  # 상태 파일 경로

        # 동시성 제어
        self._lock = asyncio.Lock()  # 상태 변경 및 파일 저장 Race Condition 방지

        # 타이머 및 하트비트
        self.last_sync_time = 0.0          # 마지막 API 동기화 시간
        self.last_api_call_time = 0.0      # Rate Limit 추적용
        self.last_target_save_time = 0.0   # target_price 저장 스로틀 추적
        self.heartbeat_interval = 5        # 하트비트 간격 (초)
        self.last_heartbeat_time = 0       # 마지막 하트비트 시간

        # Persistent State는 파일 로드, Transient State는 API로 채움
        self.state = self._load_persistent_state()

    # -----------------------------------------------------------
    # [Properties] 간결한 상태 확인
    # -----------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return self.state.get("is_active", False)

    @property
    def is_holding(self) -> bool:
        return self.state.get("is_holding", False)

    # -----------------------------------------------------------
    # [State Management] 초기화, 로드, 저장
    # -----------------------------------------------------------
    def _get_default_state(self) -> dict:
        """기본 상태 (Persistent State만 정의)"""
        return {
            "is_active": False,
            "target_price": 0,
            "stop_loss": 0,
            "last_reason": "",
            # Transient: API에서 채워짐
            "balance": 0,
            "is_holding": False,
            "avg_buy_price": 0,
        }

    def _load_persistent_state(self) -> dict:
        """
        기동 시 동기 로드 (가드 클로즈 적용).
        파일에서 Persistent State만 읽어 기본 상태 위에 병합.
        Transient State(balance 등)는 0으로 초기화 후 API 동기화에서 채움.
        """
        state = self._get_default_state()

        if not self.state_file.exists():
            return state

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                file_state = json.load(f)

            # Persistent 키만 병합 (Transient 키는 파일에 있어도 무시)
            for key in _PERSISTENT_KEYS:
                if key in file_state:
                    state[key] = file_state[key]

            logger.info(f"{self.log_prefix} 상태 파일 로드 완료: {self.state_file}")
        except Exception:
            logger.error(f"{self.log_prefix} 상태 파일 로드 실패: {traceback.format_exc()}")

        return state

    async def save_state(self):
        """
        원자적 저장 (Atomic Save).
        Persistent State 키만 필터링하여 저장.
        Lock은 호출자 측에서 이미 잡혀 있는 경우도 있으므로, 내부에서 중복 Lock 미사용.
        """
        export_data = {k: v for k, v in self.state.items() if k in _PERSISTENT_KEYS}
        temp_file = self.state_file.with_suffix(".json.tmp")

        def _atomic_write():
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, self.state_file)
            except Exception as e:
                if temp_file.exists():
                    os.remove(temp_file)
                raise e

        await asyncio.to_thread(_atomic_write)

    # -----------------------------------------------------------
    # [API Control] Rate Limit 및 Transient State 갱신
    # -----------------------------------------------------------
    async def _wait_for_rate_limit(self):
        """업비트 API 과부하 방지: 최소 호출 간격 보장"""
        elapsed = time.time() - self.last_api_call_time
        if elapsed < _MIN_API_INTERVAL:
            await asyncio.sleep(_MIN_API_INTERVAL - elapsed)
        self.last_api_call_time = time.time()

    async def sync_state_with_api(self):
        """
        [Source of Truth] 실제 계좌 상태와 메모리를 강제 동기화.
        Phase 1: Lock 밖에서 API 호출 (Non-blocking).
        Phase 2: Lock 안에서 Transient State 업데이트 (Atomic).
        예외 발생 시 상위로 전파 (호출자가 핸들링).
        """
        await self._wait_for_rate_limit()

        # Phase 1: API 호출 (Lock 없이, 블로킹 I/O는 스레드풀로)
        current_price = await self.loader.get_current_price()
        if not current_price:
            logger.warning(f"{self.log_prefix} 시세 조회 실패로 동기화 건너뜀")
            return

        actual_krw = await asyncio.to_thread(self.upbit_client.get_krw_balance)
        actual_coin_bal = await asyncio.to_thread(self.upbit_client.get_coin_balance, self.ticker)

        # 미세 잔고(Dust) 처리: 5,000원 미만은 미보유로 판단
        is_holding = (actual_coin_bal * current_price) >= 5000
        avg_buy_price = (
            await asyncio.to_thread(self.upbit_client.get_avg_buy_price, self.ticker)
            if is_holding else 0
        )

        # Phase 2: 메모리 업데이트 (Lock 안)
        async with self._lock:
            self.state.update({
                "balance": actual_krw,
                "is_holding": is_holding,
                "avg_buy_price": avg_buy_price,
            })

        self.last_sync_time = time.time()

        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="SYNC",
            message=f"{self.log_prefix} API 동기화 완료 (보유: {is_holding}, 잔고: {actual_krw:,.0f}원)",
        )

    # -----------------------------------------------------------
    # [Trade Execution] 매매 명령 실행
    # -----------------------------------------------------------
    async def execute_buy(self, price, reason, trade_params):
        """
        매수 로직 실행.
        1. API 호출 (asyncio.to_thread)
        2. 상태 업데이트 (Lock)
        3. 예외 시 즉시 sync_state_with_api (이벤트 기반 자가 치유)
        """
        try:
            await self._wait_for_rate_limit()
            # 실제 주문 실행
            await asyncio.to_thread(
                self.upbit_client.buy_market_order, self.ticker, self.state.get("balance", 0)
            )

            # Phase 2: 중요 이벤트 → Lock 안에서 상태 업데이트 및 즉시 저장
            async with self._lock:
                self.state.update({
                    "is_holding": True,
                    "avg_buy_price": price,
                    "target_price": trade_params.get("target_price", price * 1.05),
                    "stop_loss": trade_params.get("stop_loss", price * 0.95),
                    "last_reason": f"[매수] {reason}",
                })
                await self.save_state()  # Critical Event: 즉시 저장

        except Exception as e:
            # 자가 치유: 주문 실패/타임아웃 시 실제 체결 여부 즉시 확인
            logger.error(f"{self.log_prefix} 매수 주문 오류 → 자가 치유 동기화 시도: {e}")
            await save_log_to_db(
                level="ERROR",
                category="TRADE",
                event_name="ERROR",
                message=f"{self.log_prefix} 매수 실패 ({e}). 즉시 동기화 시도.",
            )
            try:
                await self.sync_state_with_api()
            except Exception:
                pass  # 동기화도 실패하면 다음 주기에 맡김
            return  # 매수 실패 시 로그 기록 없이 종료

        # 체결 직후 동기화 (정확한 잔고 반영)
        try:
            await self.sync_state_with_api()
        except Exception:
            pass

        await save_log_to_db(
            level="INFO",
            category="TRADE",
            event_name="BUY",
            message=f"{self.log_prefix} {self.state['last_reason']} | 예정가: {price:,.0f}",
        )

    async def execute_sell(self, price, reason, event_name="SELL"):
        """
        매도 로직 실행.
        1. API 호출 (asyncio.to_thread)
        2. 상태 업데이트 (Lock)
        3. 예외 시 즉시 sync_state_with_api (이벤트 기반 자가 치유)
        """
        avg_price = self.state.get("avg_buy_price", 0)
        profit_pct = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0

        try:
            await self._wait_for_rate_limit()
            # 실제 주문 실행
            coin_balance = await asyncio.to_thread(self.upbit_client.get_coin_balance, self.ticker)
            await asyncio.to_thread(self.upbit_client.sell_market_order, self.ticker, coin_balance)

            # Phase 2: Critical Event → Lock 안에서 상태 업데이트 및 즉시 저장
            async with self._lock:
                self.state.update({
                    "is_holding": False,
                    "avg_buy_price": 0,
                    "target_price": 0,
                    "stop_loss": 0,
                    "last_reason": f"[매도] {reason} | 수익률: {profit_pct:.2f}%",
                })
                await self.save_state()  # Critical Event: 즉시 저장

        except Exception as e:
            # 자가 치유: 주문 실패/타임아웃 시 실제 체결 여부 즉시 확인
            logger.error(f"{self.log_prefix} 매도 주문 오류 → 자가 치유 동기화 시도: {e}")
            await save_log_to_db(
                level="ERROR",
                category="TRADE",
                event_name="ERROR",
                message=f"{self.log_prefix} 매도 실패 ({e}). 즉시 동기화 시도.",
            )
            try:
                await self.sync_state_with_api()
            except Exception:
                pass
            return  # 매도 실패 시 로그 기록 없이 종료

        # 체결 직후 동기화
        try:
            await self.sync_state_with_api()
        except Exception:
            pass

        await save_log_to_db(
            level="WARNING" if event_name == "STOPLOSS" else "INFO",
            category="TRADE",
            event_name=event_name,
            message=f"{self.log_prefix} {self.state['last_reason']} | 예정가: {price:,.0f}",
        )

    # -----------------------------------------------------------
    # [Main Loops] 감시 및 분석 루프
    # -----------------------------------------------------------
    async def monitor_market_loop(self):
        """[파수꾼] 0.2초 주기: 즉각적인 매도(익절/손절) 감시. 파일 폴링 없음."""
        while True:
            try:
                await self.check_heartbeat()  # 하트비트 로그

                # 가드 클로즈: 비활성 또는 미보유 시 스킵
                if not self.is_active or not self.is_holding:
                    await asyncio.sleep(0.2)
                    continue

                await self._check_market_conditions()  # 익절/손절 조건 체크 후 매도 실행
                await asyncio.sleep(0.2)
            except Exception:
                await self._log_loop_error("감시 루프", traceback.format_exc())

    async def perform_analysis_loop(self):
        """[지휘부] 10초 주기(비활성 시 1초): 데이터 분석 및 주기적 동기화. 파일 폴링 없음."""
        while True:
            try:
                if not self.is_active:
                    await asyncio.sleep(1)
                    continue  # 비활성 시 대기 시간은 1초

                # 주기적 무결성 체크 (1시간): Drift 감지 및 자가 치유
                if time.time() - self.last_sync_time >= 3600:
                    try:
                        await self.sync_state_with_api()
                    except Exception:
                        await self._log_loop_error("정기 동기화", traceback.format_exc())

                await self._process_strategy_analysis()
                await asyncio.sleep(10)  # 매수 판단은 10초 주기
            except Exception:
                await self._log_loop_error("분석 루프", traceback.format_exc())

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
        current_price = await self.loader.get_current_price()
        if not current_price:
            return  # 시세 조회 실패 시 중단

        # 익절 체크
        if current_price >= self.state["target_price"]:
            return await self.execute_sell(current_price, "익절가 도달")

        # 손절 체크
        if self.state["stop_loss"] > 0 and current_price <= self.state["stop_loss"]:
            await self.execute_sell(current_price, "스탑로스 도달", "STOPLOSS")

    async def _process_strategy_analysis(self):
        df = await self.loader.fetch_ohlcv()  # 최신 ohlcv 데이터 로드
        if df is None:
            return

        is_valid, _ = self.strategy.validate_data(df)
        if not is_valid:
            return

        df_indicators = self.strategy.setup_indicators(df)
        result = self.strategy.decide(df_indicators, self.state, {})
        current_close = df_indicators["close"].iloc[-1]

        # 1. 미보유 시 → 매수 판단
        if not self.is_holding:
            if result["decision"] == "BUY":
                await self.execute_buy(
                    current_close, result["reason"], result.get("trade_params", {})
                )
            return

        # 2. 보유 시 → 목표가 갱신 로직
        await self._update_target_price(result.get("trade_params", {}))

    async def _update_target_price(self, trade_params):
        new_target = trade_params.get("target_price", self.state["target_price"])
        if new_target == self.state["target_price"]:
            return

        # 스로틀링: 10초 이내 재저장 방지 (메모리는 즉시 갱신)
        async with self._lock:
            self.state["target_price"] = new_target

        now = time.time()
        if now - self.last_target_save_time >= _TARGET_PRICE_SAVE_THROTTLE:
            await self.save_state()
            self.last_target_save_time = now

        await save_log_to_db(
            level="INFO",
            category="STRATEGY",
            event_name="DECISION",
            message=f"{self.log_prefix} 목표가 업데이트: {new_target:,.0f}",
        )

    async def _log_command_change(self, new_active):
        msg = "가동 시작" if new_active else "정지 명령 수신"
        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="COMMAND",
            message=f"{self.log_prefix} 사용자 명령 변경: {not new_active} -> {new_active} ({msg})",
        )

    async def _log_loop_error(self, loop_name, error_trace):
        await save_log_to_db(
            level="ERROR",
            category="SYSTEM",
            event_name="ERROR",
            message=f"{self.log_prefix} {loop_name} 예외: {error_trace}",
        )
        await asyncio.sleep(5)

    # -----------------------------------------------------------
    # [Lifecycle] 봇 시작 및 외부 제어
    # -----------------------------------------------------------
    async def set_active(self, new_value: bool):
        """
        FastAPI 엔드포인트에서 호출하여 is_active를 메모리에서 직접 변경.
        Critical Event: 즉시 파일 저장.
        """
        old_value = self.is_active
        async with self._lock:
            self.state["is_active"] = new_value
            await self.save_state()

        if old_value != new_value:
            await self._log_command_change(new_value)

    async def run(self):
        """
        봇 생명주기 진입점.
        1. 초기 API 동기화 (최대 3회 재시도)
        2. 성공 시에만 루프 시작
        """
        # Startup Policy: 초기 동기화 실패 시 루프 진입 차단
        max_retries = 3
        retry_delay = 5.0

        for attempt in range(max_retries):
            try:
                await self.sync_state_with_api()
                logger.info(f"{self.log_prefix} 초기 API 동기화 성공 (시도 {attempt + 1})")
                break
            except Exception as e:
                logger.warning(
                    f"{self.log_prefix} 초기 동기화 실패 (시도 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.critical(
                        f"{self.log_prefix} 초기 동기화 {max_retries}회 모두 실패. 봇 가동 중단."
                    )
                    await save_log_to_db(
                        level="ERROR",
                        category="SYSTEM",
                        event_name="ERROR",
                        message=f"{self.log_prefix} 초기 동기화 실패로 엔진 가동 중단",
                    )
                    return  # 불완전 상태로 루프 진입 방지

        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="ENGINE_START",
            message=f"{self.log_prefix} 비동기 엔진 가동 시작",
        )
        await asyncio.gather(self.monitor_market_loop(), self.perform_analysis_loop())


if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
