import time
import json
import logging
from datetime import datetime
from trading.load_data import DataLoader
from trading.strategies.rsi_bb_strategy import RSIBBStrategy

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

        # 봇 상태 (시작 시 파일에서 로드)
        self.state = self.load_state()
        self.dry_run = True  # 실제 주문 방지 플래그

    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except:
            return {"is_holding": False, "avg_buy_price": 0, "stop_loss": 0, "balance": 1000000}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def run(self):
        logger.info(f"🚀 {self.loader.ticker} 매매 엔진 가동 시작 (Dry-run: {self.dry_run})")

        while True:
            try:
                now = datetime.now()

                # [1] 1초 주기 감시 루프: 스탑로스 체크
                if self.state["is_holding"] and self.state["stop_loss"] > 0:
                    current_price = self.loader.get_current_price()
                    if current_price <= self.state["stop_loss"]:
                        self.execute_emergency_sell(current_price, "Stop-loss 도달")

                # [2] 매매 루프 테스트: 10초마다 실행 (나중에 now.minute % 15 == 0으로 변경)
                if now.second % 10 == 0:
                    self.perform_strategy_check()
                    time.sleep(1) # 중복 실행 방지

                time.sleep(1)  # 1초 휴식

            except Exception as e:
                logger.error(f"❌ 메인 루프 에러: {e}", exc_info=True)
                time.sleep(5)

    def perform_strategy_check(self):
        """15분 봉 마감 후 전략 판단 및 실행"""
        logger.info("⏳ 데이터 수집 및 전략 판단 시작")
        df = self.loader.fetch_ohlcv(count=200)

        if df is None:
            return

        # 데이터 검증 실행
        is_valid, validation_msg = self.strategy.validate_data(df)
        if not is_valid:
            logger.warning(f"데이터 검증 실패: {validation_msg}")
            return

        # 1. 지표 계산 (rsi, bb 등이 추가된 데이터프레임 생성)
        df_with_indicators = self.strategy.setup_indicators(df)

        # 2. [수정됨] 지표가 포함된 데이터를 사용하여 판단 호출
        result = self.strategy.decide(df_with_indicators, self.state, {})

        decision = result["decision"]
        reason = result["reason"]

        logger.info(f"📊 판단 결과: {decision} (사유: {reason})")

        if decision == "BUY" and not self.state["is_holding"]:
            # 매수 시점의 종가 사용
            self.execute_buy(df_with_indicators['close'].iloc[-1], trade_params)
        elif decision == "SELL" and self.state["is_holding"]:
            # 매도 시점의 종가 사용
            self.execute_sell(df_with_indicators['close'].iloc[-1], reason)

    def execute_buy(self, price, trade_params):
        self.state["is_holding"] = True
        self.state["avg_buy_price"] = price
        self.state["stop_loss"] = trade_params.get("stop_loss", price * 0.95)
        self.save_state()
        logger.info(f"✨ [매수 체결] 가격: {price:,.0f} | 스탑로스: {self.state['stop_loss']:,.0f}")

    def execute_sell(self, price, reason):
        profit_pct = (price - self.state["avg_buy_price"]) / self.state["avg_buy_price"] * 100
        self.state["is_holding"] = False
        self.state["avg_buy_price"] = 0
        self.state["stop_loss"] = 0
        self.save_state()
        logger.info(f"💰 [매도 체결] 가격: {price:,.0f} | 수익률: {profit_pct:.2f}% | 사유: {reason}")

    def execute_emergency_sell(self, price, reason):
        logger.warning(f"🚨 긴급 매도 발동!! {reason}")
        self.execute_sell(price, reason)


if __name__ == "__main__":
    bot = TradingBot()
    bot.run()
