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
    # [Refactor] 상태 접근을 위한 헬퍼 프로퍼티 (가독성 향상)
    # -----------------------------------------------------------
    @property
    def is_active(self) -> bool:
        return self.state.get("is_active", False)

    @property
    def is_holding(self) -> bool:
        return self.state.get("is_holding", False)

    # -----------------------------------------------------------
    # 상태 로드/저장 로직
    # -----------------------------------------------------------
    def load_state_sync(self):
        """초기 기동 시 동기 로드"""
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
        """
        [Refactor] 가드 클로즈를 적용하여 중첩을 제거한 지능형 로드
        bot_state.json 파일 읽기 수행.(파일 상태 변경 시에만)
        """
        max_retries = 3
        retry_delay = 0.05

        for _ in range(max_retries):
            try:
                # [Guard 1] 파일이 없으면 즉시 종료
                if not self.state_file.exists():
                    return

                # [Guard 2] 수정 시간이 동일하면(변경 없음) 즉시 종료 (최적화)
                current_stat = self.state_file.stat()
                if current_stat.st_mtime == self.last_file_mtime:
                    return

                # 파일 읽기 수행
                await self._read_and_merge_state(current_stat.st_mtime)
                return

            except OSError:
                await asyncio.sleep(retry_delay)
            except Exception:  # 3번 재시도 후 실패 시 기존 상태 그대로 유지
                pass

    async def _read_and_merge_state(self, current_mtime):
        """실제 파일 읽기 및 병합 로직 (분리됨)
        is_active 값만 읽고 로그"""

        def _read():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)

        file_state = await asyncio.to_thread(_read)

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
        temp_file = self.state_file.with_suffix(".json.tmp")  # 임시 파일 경로

        def _atomic_save():
            try:  # 임시 파일에 저장 후 교체, 그리고 파일ㄴ 수정 시간 갱신
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self.state, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, self.state_file)
                self.last_file_mtime = self.state_file.stat().st_mtime
            except Exception as e:
                logger.error(f"상태 저장 실패: {e}")  # 에러 발생 시 임시 파일 삭제 시도
                if temp_file.exists():
                    with asyncio.suppress(OSError):
                        os.remove(temp_file)
                raise e

        await asyncio.to_thread(_atomic_save)

    # -----------------------------------------------------------
    # 매매 실행 로직
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
    # 메인 루프 (리팩토링됨)
    # -----------------------------------------------------------
    async def perform_analysis_loop(self):
        """[지휘부] 10초 주기: 흐름 제어 담당
        매수 판단 및 매도 목표가 최신화 담당"""
        while True:
            try:
                await self.load_state_async()  # bot_state.json 최신화

                # is_active: false일 경우 sleep 후 건너뜀
                if not self.is_active:
                    await asyncio.sleep(1)
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
                await self.load_state_async()  # bot_state.json 로드
                await self.check_heartbeat()

                # [Guard 1] 비활성 상태면 즉시 건너뜀
                if not self.is_active:
                    await asyncio.sleep(0.2)
                    continue

                # [Guard 2] 보유 중이 아니면 시세 조회 불필요 (API 절약)
                if not self.is_holding:
                    await asyncio.sleep(0.2)
                    continue

                # 실제 시세 조회 및 감시
                await self._check_market_conditions()
                await asyncio.sleep(0.2)

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

    async def run(self):
        await save_log_to_db(
            level="INFO",
            category="SYSTEM",
            event_name="ENGINE_START",
            message=f"{self.log_prefix} 비동기 고속 엔진 가동 (Cycle: 0.2s)",
        )
        await asyncio.gather(self.monitor_market_loop(), self.perform_analysis_loop())


if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
