import pandas as pd
# 01/12: 현재 아래 파일은 빈 상태
from .trend import get_sma, get_ema, get_macd  
from .momentum import get_rsi
from .volatility import get_bbands

# 각 지표가 어떤 핸들러(계산 방식)를 사용할지 정의
# 굳이 getattr을 스지 않아도, 여기서 매핑한다
INDICATOR_HANDLERS = {
    'sma': lambda df, p: get_sma(df, length=int(p[0]) if p else 20),
    'ema': lambda df, p: get_ema(df, length=int(p[0]) if p else 20),
    'rsi': lambda df, p: get_rsi(df, length=int(p[0]) if p else 14),
    'macd': lambda df, p: get_macd(df),  # 필요 시 p로 파라미터 전달 가능
    'bb': lambda df, p: get_bbands(df, length=int(p[0]) if p else 20,
                                    std=int(p[1]) if len(p)>1 else 2)
}
