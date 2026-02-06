import os
import math
from dotenv import load_dotenv
import pyupbit


class UpbitClient:
    """"""

    def __init__(self) -> None:
        load_dotenv()
        access_key = os.getenv("UPBIT_ACCESS_KEY")
        secret_key = os.getenv("UPBIT_SECRET_KEY")
        if not access_key or not secret_key:
            raise ValueError("UPBIT_ACCESS_KEY 또는 UPBIT_SECRET_KEY가 .env에 없습니다.")
        self.upbit = pyupbit.Upbit(access_key, secret_key)

    def get_balances(self):
        return self.upbit.get_balances()

    def get_current_prices(self, tickers: list[str]) -> dict[str, float]:
        # pyupbit.get_current_price는 list[str] 넣으면 dict 반환
        prices = pyupbit.get_current_price(tickers)
        if isinstance(prices, (int, float)):
            # tickers 1개일 때 대비
            return {tickers[0]: float(prices)} if tickers else {}
        if isinstance(prices, dict):
            return {k: float(v) for k, v in prices.items()}
        return {t: 0.0 for t in tickers}

    # 봇 전용 조회 확장 메서드

    def get_krw_balance(self) -> float:
        """"가용 원화(krw) 잔고 조회"""
        balance = self.upbit.get_balance("KRW")
        return float(balance) if balance is not None else 0.0

    def get_coin_balance(self, ticker: str) -> float:
        """특정 코인의 보유 수량 조회"""
        balance = self.upbit.get_balance(ticker)
        return float(balance) if balance is not None else 0.0

    def get_avg_buy_price(self, ticker: str) -> float:
        """업비트 서버 기준의 실제 평단가 조회"""
        avg_price = self.upbit.get_avg_buy_price(ticker)
        return float(avg_price) if avg_price else 0.0

    # 실전 매매 주문 메서드

    def buy_market_order(self, ticker: str, krw_amount: float):
        """시장가 매수 실행"""
        return self.upbit.buy_market_order(ticker, krw_amount)
    
    def sell_market_order(self, ticker: str, volume: float):
        """ 
        시장가 매도 실행 (수량 기준)
        지수 표기법(e-05 등)으로 인한 api 오류 방지를 위해 문자열 포맷팅 적용
        """
        formatted_volume = f"{volume:.8f}"
        return self.upbit.sell_market_order(ticker, formatted_volume)

    # 정밀 유틸리티 메서드. 

    @staticmethod
    def floor_tick_size(price: float) -> float:
        """
        업비트 호가 단위를 준수하며 부동 소수점 오차를 방지하는 가격 내림 처리.
        피드백 반영: epsilon(1e-9) 가산으로 floor 오차 방지 및 round를 통한 최종 정밀도 확보.
        """
        if price >= 2000000: tick = 1000
        elif price >= 1000000: tick = 500
        elif price >= 500000: tick = 100
        elif price >= 100000: tick = 50
        elif price >= 10000: tick = 10
        elif price >= 1000: tick = 5
        elif price >= 100: tick = 1
        elif price >= 10: tick = 0.1
        else: tick = 0.01

        # 1e-9를 더해 floor 시 발생하는 미세한 하향 오차 방지
        # KRW 시장 규격에 따라 tick이 1 미만이면 소수점 2자리까지 round 처리
        tick_precision = 2 if tick < 1 else 0
        return round(math.floor(price / tick + 1e-9) * tick, tick_precision)

# 인스턴스 생성
client = UpbitClient()