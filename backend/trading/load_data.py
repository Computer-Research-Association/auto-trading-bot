import pyupbit
import pandas as pd
import asyncio
import logging
from typing import Optional
from .db_logger import save_log_to_db

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, ticker: str = "KRW-BTC", interval: str = "minute15"):
        self.ticker = ticker
        self.interval = interval

    def fetch_ohlcv(self, count: int = 200) -> Optional[pd.DataFrame]:
        """
        업비트로부터 데이터를 가져오고, 최소 요구 개수를 충족하는지 검증
        """
        max_retries = 3
        # 업비트 호출 직전 짧은 대기
        time.sleep(0.1)

        for attempt in range(max_retries):
            try:
                df = pyupbit.get_ohlcv(
                    ticker=self.ticker,
                    interval=self.interval,
                    count=count
                )
                # 데이터 존재 여부 체크
                if df is None or df.empty:
                    logger.warning(f"[{self.ticker}] 데이터가 비어 있습니다. 재시도 중 ({attempt + 1}/{max_retries})...")
                    time.sleep(1)
                    continue

                # 데이터 개수 검증 로직
                current_len = len(df)
                fill_rate = (current_len / count) * 100

                # 최소 개수 검증
                # 요청 데이터 개수 보다 적은 데이터로 지표 계산 시 에러 날 수 있음
                if len(df) < count * 0.9:
                    logger.warning(f"[{self.ticker}] 데이터 개수 부족: {fill_rate:.1f}% ({attempt + 1}/{max_retries}) 이번 주기 패스.")
                    return None  # None 반환 시 bot.py가 판단을 생략함

                # 90% 이상이면 경고만 띄우기(신규 상장 코인의 경우)
                elif len(df) < count:
                    logger.warning(f"[{self.ticker}] 데이터 일부 누락: {fill_rate:.1f}%. 계산 강행.")

                # 표준 및 반환
                df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)  # float 강제 변환
                df.index.name = 'datetime'

                # 인덱스를 일반 컬럼으로 전환
                df = df.reset_index()

                return df

            except Exception as e:
                logger.error(f"[{self.ticker}] API 호출 중 에러: {e}")
                time.sleep(2)

        return None

    def get_current_price(self) -> float:
        """
        현재가 조회 (매우 빈번하게 후출될 것을 대비해 0.05초 대기)
        api 허용 횟수 초과 시 id 밴 당할 위험 있음
        """
        time.sleep(0.1)
        try:
            price = pyupbit.get_current_price(self.ticker)

            # 가격 가져올 때 에러 발생 시 로그 남기기
            if price is None:
                logger.warning(f"⚠️ [{self.ticker}] 현재가 조회 실패 (None 반환)")
                return None

            return float(price)

        except Exception as e:
            logger.error(f"[{self.ticker}] 현재가 조회 실패 {e}")
            return None

