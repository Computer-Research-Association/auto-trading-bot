import pandas as pd
import pandas_ta as ta


def get_sma(df: pd.DataFrame, length: int = 20):
    """ 
    단순 이동평균선(sma) 계산
    결과: Series
    """
    return ta.sma(df['close'], length=length)