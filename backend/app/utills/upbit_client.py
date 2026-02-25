import os
import math
from dotenv import load_dotenv
import pyupbit


class UpbitClient:
    """
    가상자산 거래소 '업비트'의 API를 전략적으로 래핑하여 데이터 정합성과 매매 안정성을 보장하는 클래스.
    
    주요 기능:
    1. 실시간 계좌 상태 동기화: 가용 원화, 코인 보유량, 실제 평단가 추출.
    2. 정밀 매매 실행: 지수 표기법 방지 및 고정 소수점 포맷팅을 적용한 시장가 주문.
    3. 호가 규격 최적화: 부동 소수점 오차를 보정한 가격대별 호가 단위(Tick Size) 처리.
    
    사용처:
    - TradingBot Engine: 매매 결정 시 실제 주문을 실행하고 계좌 상태를 동기화하는 핵심 도구.
    - PortfolioService: 웹 대시보드에 실시간 자산 및 시세 데이터를 공급하는 데이터 프로바이더.
    """

    def __init__(self) -> None:
        load_dotenv()
        access_key = os.getenv("UPBIT_ACCESS_KEY")
        secret_key = os.getenv("UPBIT_SECRET_KEY")
        if not access_key or not secret_key:
            raise ValueError("UPBIT_ACCESS_KEY 또는 UPBIT_SECRET_KEY가 .env에 없습니다.")
        self.upbit = pyupbit.Upbit(access_key, secret_key)
        
        # 초고속 매매 환경을 빙자하되, 라이브러리(pyupbit)의 동기 통신에서 
        # 발생하는 간혈적 렉을 방어하는 HTTP Request Timeout 설정 (3.0초)
        # 이 객체의 메서드(get_krw_balance 등)는 bot.py에서 asyncio.wait_for()와 
        # 함께 호출될 것이므로 여기서 내부 timeout 변수를 제공.
        self.timeout = 3.0



    def get_balances(self):
        return self.upbit.get_balances()

    def get_current_prices(self, tickers: list[str]) -> dict[str, float]:
        # pyupbit.get_current_price는 list[str] 넣으면 dict 반환
        try:
            prices = pyupbit.get_current_price(tickers)
        except Exception as e:
            return {t: 0.0 for t in tickers}
            
        if isinstance(prices, (int, float)):
            # tickers 1개일 때 대비
            return {tickers[0]: float(prices)} if tickers else {}
        if isinstance(prices, dict):
            # error 응답 dict 방어
            if "error" in prices:
                return {t: 0.0 for t in tickers}
            valid_prices = {}
            for k, v in prices.items():
                try:
                    valid_prices[k] = float(v)
                except (ValueError, TypeError):
                    pass
            return valid_prices
        return {t: 0.0 for t in tickers}

    # 타입 에러 방어 유틸
    def _safe_float(self, val: any) -> float:
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    # 봇 전용 조회 확장 메서드

    def get_krw_balance(self) -> float:
        """가용 원화(krw) 잔고 조회"""
        return self._safe_float(self.upbit.get_balance("KRW"))

    def get_coin_balance(self, ticker: str) -> float:
        """특정 코인의 보유 수량 조회"""
        return self._safe_float(self.upbit.get_balance(ticker))

    def get_avg_buy_price(self, ticker: str) -> float:
        """업비트 서버 기준의 실제 평단가 조회"""
        return self._safe_float(self.upbit.get_avg_buy_price(ticker))

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