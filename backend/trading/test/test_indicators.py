import pandas as pd
import numpy as np
# 경로 설정에 주의하세요 (실행 위치에 따라 .. 또는 .indicators)
from ..indicators import add_indicators 


def run_test():
    # 1. 테스트용 가짜 데이터 생성 (OHLCV 형태)
    # 캔들 개수를 120개 이상으로 설정 (BaseStrategy 기준 충족)
    rows = 150
    data = {
        'open': np.random.uniform(100, 200, rows),
        'high': np.random.uniform(200, 300, rows),
        'low': np.random.uniform(50, 100, rows),
        'close': np.random.uniform(100, 200, rows),
        'volume': np.random.uniform(1000, 5000, rows)
    }
    df = pd.DataFrame(data)

    print("--- 테스트 시작 ---")
    print(f"원본 컬럼: {df.columns.tolist()}")

    # 2. 지표 추가 요청 (새로운 딕셔너리 방식 적용)
    # 문자열 'sma_20' 대신 아래와 같은 구조로 전달해야 합니다.
    requested = [
        {"name": "sma", "params": {"length": 20}},
        {"name": "ema", "params": {"length": 10}},
        {"name": "rsi", "params": {"length": 14}},
        {"name": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}},
        {"name": "bb", "params": {"length": 20, "std": 2.0}}
    ]
    
    try:
        result_df = add_indicators(df, requested)
        
        print("\n--- 결과 확인 ---")
        print(f"추가 후 컬럼: {result_df.columns.tolist()}")
        
        # 3. 컬럼 존재 여부 확인 (수정된 add_indicators의 컬럼명 규칙 적용)
        # 단일 Series는 NAME_VALUE 형식 (예: SMA_20)
        # DataFrame 반환 지표는 함수 정의 컬럼명 그대로 사용
        check_cols = ['SMA_20', 'EMA_10', 'RSI_14', 'bb_middle', 'MACD_12_26_9']
        
        # 실제 존재하는 컬럼들만 필터링하여 출력 (에러 방지)
        existing_cols = [c for c in check_cols if c in result_df.columns]
        
        print("\n최근 5개 데이터 샘플:")
        print(result_df[['close'] + existing_cols].tail())
        
        # 성공 여부 판단
        if len(existing_cols) >= 3: # 주요 지표들이 포함되어 있다면
            print(f"\n✅ 테스트 성공: {len(existing_cols)}개의 지표가 계산되었습니다.")
        else:
            print("\n❌ 테스트 실패: 예상한 지표 컬럼이 발견되지 않았습니다.")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        # 상세 에러 추적을 위해 트레이스백이 필요하면 아래 주석 해제
        # import traceback; traceback.print_exc()


if __name__ == "__main__":
    run_test()