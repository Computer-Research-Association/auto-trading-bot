import time
import json
import logging
from datetime import datetime
from load_data import DataLoader
from strategies.rsi_bb_strategy import RSIBBStrategy

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("trading.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, ticker="KRW-BTC"):
        self.loader = DataLoader(ticker=ticker)
        self.strategy = RSIBBStrategy()
        self.state_file = "bot_state.json"

        # 봇 상태 로드
        self.state = self.load_state()
        self.dry_run = True  # 실거래 방지

    def load_state(self):
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # 파일은 있는데 필드가 없는 경우를 대비한 자동 업데이트
                if "is_active" not in state: state["is_active"] = False
                if "last_reason" not in state: state["last_reason"] = ""
                return state
        except Exception:
            # 초기 상태값
            return {
                "is_active": False, 
                "is_holding": False, 
                "avg_buy_price": 0, 
                "stop_loss": 0, 
                "balance": 1000000,
                "last_reason": "봇이 초기화 됨"  # 매매 근거 기록용
            }

    def save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)

    def run(self):
        logger.info(f"🚀 {self.loader.ticker} 엔진 가동 (Dry-run: {self.dry_run})")

        while True:
            try:
                # [Guard] 1. 활성화 상태 체크 (최상단)
                # False일 경우 아래의 모든 로직(API 호출 포함)을 건너뜁니다.
                if not self.state.get("is_active", False):
                    # 활성화를 기다리며 긴 주기로 체크
                    time.sleep(10) 
                    continue

                now = datetime.now()

                # [2] 스탑로스 감시 (매초 실행)
                if self.state["is_holding"] and self.state["stop_loss"] > 0:
                    current_price = self.loader.get_current_price()
                    if current_price is not None:
                        if current_price <= self.state["stop_loss"]:
                            self.execute_emergency_sell(current_price, "Stop-loss 도달")
                    else:
                        logger.warning("⏳ 현재가를 불러올 수 없어 스탑로스 감시를 1회 건너뜁니다.")

                # [3] 전략 매매 루프 (10초 주기)
                if now.second % 10 == 0:
                    self.perform_strategy_check()
                    time.sleep(1)

                time.sleep(1)

            except Exception as e:
                logger.error(f"❌ 메인 루프 에러: {e}", exc_info=True)
                time.sleep(5)

    def perform_strategy_check(self):
        """데이터 수집 및 전략 판단 파이프라인"""
        # [Data] 전략 기반 동적 캔들 수집
        count = getattr(self.strategy, "required_candles", 200)
        df = self.loader.fetch_ohlcv(count=count)

        if df is None: return

        # [Safety] 데이터 검증 강제화
        is_valid, msg = self.strategy.validate_data(df)
        if not is_valid:
            logger.warning(f"⚠️ 데이터 검증 실패: {msg}")
            return

        # 지표 계산 및 판단
        df_with_indicators = self.strategy.setup_indicators(df)
        result = self.strategy.decide(df_with_indicators, self.state, {})

        decision = result["decision"]
        reason = result["reason"]
        trade_params = result.get("trade_params", {})

        logger.info(f"📊 판단: {decision} | 사유: {reason}")

        # [Output] Rich Output 처리 파이프라인
        current_close = df_with_indicators['close'].iloc[-1]
        
        if decision == "BUY" and not self.state["is_holding"]:
            self.execute_buy(current_close, reason, trade_params)
        elif decision == "SELL" and self.state["is_holding"]:
            self.execute_sell(current_close, reason, trade_params)

    def execute_buy(self, price, reason, trade_params):
        """매수 실행 및 상태 업데이트"""
        self.state["is_holding"] = True
        self.state["avg_buy_price"] = price

        # [Output] 스탑로스 오버라이드 로직
        # 전략이 준 값이 있으면 사용, 없으면 기본 5% 적용
        self.state["stop_loss"] = trade_params.get("stop_loss", price * 0.95)

        # 사유 기록: 로그 찍고, bot_state.json 파일 저장
        log_msg = f"[매수] {reason}"
        self.state["last_reason"] = log_msg

        self.save_state()
        logger.info(f"✨{log_msg} | 가격: {price:,.0f}")
        logger.info(f"🛡️ 스탑로스 설정: {self.state['stop_loss']:,.0f}")

    def execute_sell(self, price, reason, trade_params):
        """매도 실행 및 수익률 계산"""
        profit_pct = (price - self.state["avg_buy_price"]) / self.state["avg_buy_price"] * 100

        # 매도 근거와 수익률 하나로 묶음
        log_msg = f"[매도] {reason} | 수익률: {profit_pct:.2f}%"
        self.state["last_reason"] = log_msg
        self.state["is_holding"] = False
        self.state["avg_buy_price"] = 0
        self.state["stop_loss"] = 0

        self.save_state()
        logger.info(f"💰 {log_msg} | 가격: {price:,.0f}")

    def execute_emergency_sell(self, price, reason):
        """긴급 매도 로직"""
        emergency_reason = f"긴급 매도: {reason}"
        logger.warning(emergency_reason)
        self.execute_sell(price, f"[긴급]{reason}", {})


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
