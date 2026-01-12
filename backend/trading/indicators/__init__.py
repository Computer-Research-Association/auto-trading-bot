import pandas as pd
# 01/12: 현재 아래 파일은 빈 상태
from .trend import get_sma, get_ema, get_macd  
from .momentum import get_rsi
from .volatility import get_bbands

# 지표 이름과 함수 매핑
INDICATOR_MAP = {
    'sma': get_sma,
    'ema': get_ema,
    'macd': get_macd,
    'rsi': get_rsi,
    'bbands': get_bbands,
}


