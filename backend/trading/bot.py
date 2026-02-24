import asyncio
import json
import os
import time
import traceback
import logging
from pathlib import Path
from datetime import datetime

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
# is_holding, balance, coin_balance 등은 API 동기화를 소스로 활용
_PERSISTENT_KEYS = {"is_active", "is_dry_run", "target_buy_price", "target_sell_price", "target_stop_loss", "last_reason"}

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

        # 동시성 및 파일 I/O 제어
        self._lock = asyncio.Lock()  # 메모리 속기 시 Race Condition 방지
        self._state_queue = asyncio.Queue()  # 상태 쓰기 직렬화 큐
        self._state_worker_task = None  # 워커 태스크 참조

        # 타이머 및 하트비트
        self.last_sync_time = 0.0  # 마지막 API 동기화 시간
        self.last_api_call_time = 0.0  # Rate Limit 추적용
        self.last_target_save_time = 0.0  # target_price 저장 스로틀 추적
        self.heartbeat_interval = 600  # heartbeat 간격 (초)
        self.last_heartbeat_time = 0  # 마지막 하트비트 시간

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
        """기본 상태 (Persistent State + Transient State)"""
        return {
            "is_active": False,
            "is_dry_run": False,        # 모의 투자 여부
            "target_buy_price": 0.0,    # 분석 루프가 설정한 목표 매수가
            "target_sell_price": 0.0,   # 분석 루프가 설정한 목표 익절가
            "target_stop_loss": 0.0,    # 분석 루프가 설정한 목표 손절가
            "last_reason": "",          # 마지막 의사 결정 사유
            # Transient: API 동기화 기반 Shadow Balance
            "balance": 0.0,             # KRW 가용 잔고
            "coin_balance": 0.0,        # 코인 보유 수량
            "is_holding": False,
            "avg_buy_price": 0.0,
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
            logger.error(
                f"{self.log_prefix} 상태 파일 로드 실패: {traceback.format_exc()}"
            )

        return state

    async def _state_writer_worker(self):
        """[백그라운드] 큐에서 상태를 꺼내어 직렬화된 원자적(Atomic) 저장을 수행"""
        temp_file = self.state_file.with_suffix(".json.tmp")
        while True:
            try:
                export_data = await self._state_queue.get()
                
                # None이 큐에 들어오면 종료 신호
                if export_data is None:
                    self._state_queue.task_done()
                    break

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
                self._state_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.log_prefix} 상태 파일 저장 워커 오류: {e}")

    async def save_state(self):
        """
        원자적 저장 (Atomic Save).
        Persistent State 키만 필터링하여 비동기 큐에 전달하여 파일 I/O 블로킹 및 Race Condition 방지.
        """
        export_data = {k: v for k, v in self.state.items() if k in _PERSISTENT_KEYS}
        # 큐에 복사본(deep copy 필요 없음, 단순 dict)을 던져 워커가 쓰도록 위임
        await self._state_queue.put(export_data.copy())

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

        # Phase 1: API 호출 (Lock 없이, 블로킹 I/O는 스레드풀로 - Timeout 강제)
        try:
            current_price = await asyncio.wait_for(
                self.loader.get_current_price(), 
                timeout=self.upbit_client.timeout
            )
            if not current_price:
                logger.warning(f"{self.log_prefix} 시세 조회 실패로 동기화 건너뜀")
                return

            actual_krw = await asyncio.wait_for(
                asyncio.to_thread(self.upbit_client.get_krw_balance),
                timeout=self.upbit_client.timeout
            )
            actual_coin_bal = await asyncio.wait_for(
                asyncio.to_thread(self.upbit_client.get_coin_balance, self.ticker),
                timeout=self.upbit_client.timeout
            )

            # 미세 잔고(Dust) 처리: 5,000원 미만은 미보유로 판단
            is_holding = (actual_coin_bal * current_price) >= 5000
            if is_holding:
                avg_buy_price = await asyncio.wait_for(
                    asyncio.to_thread(self.upbit_client.get_avg_buy_price, self.ticker),
                    timeout=self.upbit_client.timeout
                )
            else:
                avg_buy_price = 0
        except asyncio.TimeoutError:
            logger.warning(f"{self.log_prefix} 동기화 중 HTTP Timeout 발생 (네트워크 지연)")
            return
        except Exception as e:
            logger.error(f"{self.log_prefix} 동기화 중 예외: {e}")
            return

        # 모의 투자인 경우, 기존 가상 자산을 API 팩트에 덮어씌워지지 않도록 방지
        # 실제 매매(운영) 환경에서만 API 잔고를 메모리에 그대로 덮어씀
        async with self._lock:
            if self.state.get("is_dry_run", False):
                # Dry run 시 초기 1회만 잔고를 반영하고, 그 뒤엔 로컬 Shadow를 신뢰
                if self.state.get("balance", 0) == 0 and actual_krw > 0:
                    self.state["balance"] = actual_krw
                    self.state["coin_balance"] = actual_coin_bal
                    self.state["avg_buy_price"] = avg_buy_price
                    self.state["is_holding"] = is_holding
            else:
                self.state.update(
                    {
                        "balance": actual_krw,
                        "coin_balance": actual_coin_bal,
                        "is_holding": is_holding,
                        "avg_buy_price": avg_buy_price,
                    }
                )

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
        매수 로직 실행. (집행관)
        1. Dry-run 검사
        2. 실제 API 호출
        3. Shadow Balance 즉시 갱신 (딜레이 제로)
        4. 예외 시 안전 정지(Kill Switch) 혹은 자가 치유
        """
        is_dry_run = self.state.get("is_dry_run", False)
        buy_amount = self.state.get("balance", 0)

        # 안전 장치: 최소 주문 금액 초과 확인
        if buy_amount < 5000:
            logger.warning(f"{self.log_prefix} 매수 불가: 잔고 부족 ({buy_amount}원)")
            return

        try:
            if not is_dry_run:
                await self._wait_for_rate_limit()
                # 실제 주문 실행 (Timeout 강제)
                await asyncio.wait_for(
                    asyncio.to_thread(self.upbit_client.buy_market_order, self.ticker, buy_amount),
                    timeout=self.upbit_client.timeout
                )
            else:
                await asyncio.sleep(0.01) # 모  의 지연

            # Phase 2: Shadow Balance 즉시 갱신(메모리 선반영)
            async with self._lock:
                fee_rate = 0.0005 # 업비트 기본 수수료 0.05%
                deducted_krw = buy_amount
                acquired_coin = (buy_amount * (1 - fee_rate)) / price

                self.state.update(
                    {
                        "is_holding": True,
                        "balance": 0.0,
                        "coin_balance": acquired_coin,
                        "avg_buy_price": price,
                        "last_reason": f"[DRY-RUN 매수] {reason}" if is_dry_run else f"[매수] {reason}",
                    }
                )
                await self.save_state()  # Critical Event: 즉시 저장

        except Exception as e:
            # 방어 로직 (Kill Switch)
            logger.error(f"{self.log_prefix} 매수 주문 치명적 오류: {e}")
            await self._trigger_kill_switch(f"매수 실패 예외: {e}")
            return  # 매수 실패 시 즉시 중단

        # 체결 직후 동기화 (정확한 수수료/단가 보정)
        if not is_dry_run:
            try:
                await self.sync_state_with_api()
            except Exception:
                pass

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
        매도 로직 실행. (집행관)
        """
        avg_price = self.state.get("avg_buy_price", 0)
        profit_pct = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0.0
        is_dry_run = self.state.get("is_dry_run", False)
        coin_balance = self.state.get("coin_balance", 0.0)

        # 먼지 잔고(Dust) 무시
        if (coin_balance * price) < 5000:
             logger.warning(f"{self.log_prefix} 매도 불가: 잔고 부족 ({coin_balance}개)")
             return

        try:
            if not is_dry_run:
                await self._wait_for_rate_limit()
                # 실제 주문 실행
                # 이미 메모리에 있는 섀도우 잔고를 우선 던지고 오차는 동시성에 맡김 (0.2초 반응 속도 우선)
                await asyncio.wait_for(
                    asyncio.to_thread(self.upbit_client.sell_market_order, self.ticker, coin_balance),
                    timeout=self.upbit_client.timeout
                )
            else:
                await asyncio.sleep(0.01)

            # Phase 2: Shadow Balance 즉시 갱신
            async with self._lock:
                fee_rate = 0.0005
                acquired_krw = (coin_balance * price) * (1 - fee_rate)

                self.state.update(
                    {
                        "is_holding": False,
                        "balance": self.state.get("balance", 0.0) + acquired_krw,
                        "coin_balance": 0.0,
                        "avg_buy_price": 0.0,
                        "target_buy_price": 0.0,
                        "target_sell_price": 0.0,
                        "target_stop_loss": 0.0,
                        "last_reason": f"[DRY-RUN 매도] {reason} | 수익률: {profit_pct:.2f}%" if is_dry_run else f"[매도] {reason} | 수익률: {profit_pct:.2f}%",
                    }
                )
                await self.save_state()  # Critical Event: 즉시 저장

        except Exception as e:
            logger.error(f"{self.log_prefix} 매도 주문 치명적 오류: {e}")
            await self._trigger_kill_switch(f"매도 실패 예외: {e}")
            return

        # 체결 직후 정합성 동기화
        if not is_dry_run:
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
    # [Main Loops] 감시(집행관) 및 분석(지휘관) 루프
    # -----------------------------------------------------------
    async def _trigger_kill_switch(self, reason_msg: str):
        """치명적 에러 발생 시 알 수 없는 포지션 진입을 막기 위한 강제 정지 장치"""
        async with self._lock:
            self.state["is_active"] = False
            self.state["last_reason"] = f"[KILL-SWITCH 작동] {reason_msg}"
            await self.save_state()
            
        await save_log_to_db(
            level="ERROR",
            category="SYSTEM",
            event_name="KILL_SWITCH",
            message=f"{self.log_prefix} 시스템 보호를 위해 봇이 긴급 정지되었습니다. 원인: {reason_msg}"
        )
    async def monitor_market_loop(self):
        """[집행관] 0.2초 주기: 즉각적인 매수/매도(익절/손절) 감시. 파일 폴링 없음."""
        while True:
            try:
                await self.check_heartbeat()  # 하트비트 로그

                # 가드 클로즈: 비활성 시 완전히 스킵
                if not self.is_active:
                    await asyncio.sleep(0.2)
                    continue

                await self._check_market_conditions()  # 현재가 vs 목표가 감시
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

                # 5분(300초) 주기 백그라운드 무결성 체크: Shadow Balance Drift 감지 및 자가 치유
                if time.time() - self.last_sync_time >= 300:
                    try:
                        await self.sync_state_with_api()
                    except Exception:
                        await self._log_loop_error(
                            "정기 동기화", traceback.format_exc()
                        )

                await self._process_strategy_analysis()
                await asyncio.sleep(10)  # 지휘관 분석 및 작전 하달은 10초 주기
            except Exception:
                await self._log_loop_error("분석 루프", traceback.format_exc())

    async def check_heartbeat(self):
        current_time = time.time()
        if current_time - self.last_heartbeat_time >= self.heartbeat_interval: 
            # 총 자산 가치 계산 로직 (KRW + 코인 잔고 * 현재가)
            current_price = await self.loader.get_current_price()
            krw_balance = self.state.get("balance", 0.0)
            coin_balance = self.state.get("coin_balance", 0.0)
            coin_val = coin_balance * (current_price if current_price else 0.0)
            total_assets = krw_balance + coin_val

            msg = (
                f"[매매 가동 중] 엔진 생존 신고 (총 자산: {total_assets:,.0f}원 | 보유 현황: {self.is_holding})"
                if self.is_active
                else f"[대기 모드] 엔진 생존 신고 (총 자산: {total_assets:,.0f}원 | 사용자 명령 대기 중)"
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
        즉각적인 매수/매도 조건 체크 및 실행 (executor)
        """
        current_price = await self.loader.get_current_price()
        if not current_price:
            return  # 시세 조회 실패 시 중단

        if self.is_holding:
            # 매도 감시 (보유 중)
            target_sell = self.state.get("target_sell_price", 0)
            target_stop = self.state.get("target_stop_loss", 0)
            
            if target_sell > 0 and current_price >= target_sell:
                return await self.execute_sell(current_price, "목표 익절가 도달", "SELL")
                
            if target_stop > 0 and current_price <= target_stop:
                return await self.execute_sell(current_price, "목표 손절가 도달", "STOPLOSS")
        else:
            # 매수 감시 (미보유 중)
            target_buy = self.state.get("target_buy_price", 0)
            
            if target_buy > 0 and current_price <= target_buy:
                return await self.execute_buy(current_price, "목표 매수가 도달", {})

    async def _process_strategy_analysis(self):
        df = await self.loader.fetch_ohlcv()  # 최신 ohlcv 데이터 로드
        if df is None:
            return

        is_valid, _ = self.strategy.validate_data(df)
        if not is_valid:
            return

        df_indicators = self.strategy.setup_indicators(df)
        result = self.strategy.decide(df_indicators, self.state, {})

        # 분석 결과 내의 trade_params만 추출하여 갱신 (KeyError 및 인자 불일치 해결)
        await self._update_target_price(result.get("trade_params", {}))

    async def _update_target_price(self, trade_params):
        new_buy = trade_params.get("target_buy_price", 0)
        new_sell = trade_params.get("target_sell_price", 0)
        new_stop = trade_params.get("target_stop_loss", 0)
        reason = trade_params.get("reason", "")
        
        # 이전 값과 하나라도 다르면 업데이트 대상
        if (new_buy == self.state.get("target_buy_price") and 
            new_sell == self.state.get("target_sell_price") and 
            new_stop == self.state.get("target_stop_loss")):
            return

        async with self._lock:
            self.state["target_buy_price"] = new_buy
            self.state["target_sell_price"] = new_sell
            self.state["target_stop_loss"] = new_stop
            if reason:
                self.state["last_reason"] = reason

        now = time.time()
        if now - self.last_target_save_time >= _TARGET_PRICE_SAVE_THROTTLE:
            await self.save_state()
            self.last_target_save_time = now

        msg = ""
        if self.is_holding:
            msg = f"익절: {new_sell:,.0f} / 손절: {new_stop:,.0f}" if new_sell else "대기"
        else:
            msg = f"진입: {new_buy:,.0f}" if new_buy else "대기"

        await save_log_to_db(
            level="INFO",
            category="STRATEGY",
            event_name="DECISION",
            message=f"{self.log_prefix} [모드:{'보유' if self.is_holding else '현금'}] 목표가 갱신 → {msg}",
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

    async def get_snapshot(self) -> dict:
        """
        외부 API 조회용: 현재 상태 스냅샷을 반환 (Thread-Safe).
        """
        async with self._lock:
            snapshot = self.state.copy()
            snapshot["timestamp"] = datetime.utcnow().isoformat()
            snapshot["strategy_name"] = self.strategy_name
            return snapshot

    async def run(self):
        """
        봇 생명주기 진입점.
        1. 초기 API 동기화 (최대 3회 재시도)
        2. 성공 시에만 루프 시작
        """
        # Startup Policy: 네트워크 오류 등에도 백그라운드 태스크가 종료되지 않도록 무한 재시도 (10초 대기)
        retry_delay = 10.0
        attempt = 1

        while True:
            try:
                await self.sync_state_with_api()
                logger.info(f"{self.log_prefix} 초기 API 동기화 성공 (시도 {attempt})")
                break
            except Exception as e:
                logger.warning(
                    f"{self.log_prefix} 초기 동기화 실패 (시도 {attempt}): {e}. {retry_delay}초 후 재시도..."
                )
                await asyncio.sleep(retry_delay)
                attempt += 1

        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="ENGINE_START",
            message=f"{self.log_prefix} 비동기 엔진 가동 시작",
        )

        # 큐 워커 태스크 시작
        self._state_worker_task = asyncio.create_task(self._state_worker_task_wrapper())

        try:
            await asyncio.gather(
                self.monitor_market_loop(), self.perform_analysis_loop()
            )
        except asyncio.CancelledError:
            logger.info(
                f"{self.log_prefix} 봇 작업이 취소되었습니다 (Graceful Shutdown)."
            )
            # 종료 시 큐 정리 대기
            await self._state_queue.put(None)
            if self._state_worker_task:
                await self._state_worker_task
            raise
        except Exception as e:
            logger.error(
                f"{self.log_prefix} 봇 메인 루프 예외 발생: {e}", exc_info=True
            )
            await save_log_to_db(
                level="ERROR",
                category="SYSTEM",
                event_name="ERROR",
                message=f"{self.log_prefix} 봇 메인 루프 크래시: {e}",
            )
            raise

    async def _state_worker_task_wrapper(self):
        """워커 예외 전파 차단 래퍼"""
        try:
            await self._state_writer_worker()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"{self.log_prefix} State worker crashed: {e}")


if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
