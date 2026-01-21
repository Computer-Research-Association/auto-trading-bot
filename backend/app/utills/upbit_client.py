import os

from dotenv import load_dotenv
import pyupbit


class UpbitClient:
    """PortfolioService가 기대하는 최소 메서드만 제공하는 래퍼"""

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



client = UpbitClient()