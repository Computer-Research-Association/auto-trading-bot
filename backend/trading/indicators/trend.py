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
    