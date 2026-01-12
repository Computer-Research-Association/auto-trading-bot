import pandas as pd
import pandas_ta as ta


def get_sma(df: pd.DataFrame, length: int = 20):
    """ 
    단순 이동평균선(sma) 계산
    결과: Series
    """
    return ta.sma(df['close'], length=length)


def get_ema(df: pd.DataFrame, length: int = 20):
    """
    지수 이동평균선(EMA) 계산
    """
    return ta.ema(df['close'], length=length)


def get_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    MACD 계산
    결과: DataFrame (MACD선, 시그널선, 히스토그램 3개 컬럼)
    """
    return ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
    
