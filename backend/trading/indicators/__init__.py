import pandas as pd
from .trend import get_sma, get_ema, get_macd  
from .momentum import get_rsi
from .volatility import get_bbands

# 각 지표가 어떤 핸들러(계산 방식)를 사용할지 정의
# 굳이 getattr을 스지 않아도, 여기서 매핑한다
INDICATOR_HANDLERS = {
    'sma': lambda df, p: get_sma(df, length=p.get('length', 20)),
    'ema': lambda df, p: get_ema(df, length=p.get('length', 20)),
    'rsi': lambda df, p: get_rsi(df, length=p.get('length', 14)),
    'macd': lambda df, p: get_macd(
        df,
        fast=p.get('fast', 12),
        slow=p.get('slow', 26),
        signal=p.get('signal', 9)
        ),
    'bb': lambda df, p: get_bbands(df,
        length=p.get('length', 20), std=p.get('std', 2.0)
        )
}


def add_indicators(df: pd.DataFrame, requested_list: list) -> pd.DataFrame:
    df = df.copy()
    for item in requested_list:
        name = item.get('name', '').lower()
        params = item.get('params', {})

        if name in INDICATOR_HANDLERS:
            try:
                # 핸들러 실행
                result = INDICATOR_HANDLERS[name](df, params)

                # 결과가 데이터 프레임이면 합치고, 시리즈면 컬럼 추가
                if isinstance(result, pd.DataFrame):
                    df = pd.concat([df, result], axis=1)
                else:
                    col_name = f"{name.upper()}_{params[0]}" if params else name.upper()
                    df[col_name] = result
            except Exception as e:
                print(f"Error calculating {item}: {e}")
        else:
            print(f"Warning: {name} is not supported.")
    return df
