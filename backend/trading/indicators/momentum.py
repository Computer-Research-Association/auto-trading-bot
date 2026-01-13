import pandas as pd
import numpy as np


def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """
    RSI 계산
    SMMA 방식을 사용하여 업계 표준값 산출
    """
    delta = df['close'].diff()