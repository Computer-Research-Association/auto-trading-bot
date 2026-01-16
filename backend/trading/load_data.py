import pyupbit
import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, ticker: str = "KRW-BTC", interval: str = "minute15"):
        self.ticker = ticker
        self.interval = interval

    def fetch_ohlcv()