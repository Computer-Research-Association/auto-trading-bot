import pandas as pd
import numpy as np
from ..indicators import add_indicators


def run_test():
    # 1. 테스트용 가짜 데이터 생성 (OHLCV 형태)
    data = {
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(200, 300, 100),
        'low': np.random.uniform(50, 100, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    }
    df = pd.DataFrame(data)

    print("--- 테스트 시작 ---")
    print(f"원본 컬럼: {df.columns.tolist()}")

    # 2. 지표 추가 요청 (우리가 만든 문자열 방식)
    requested = ['sma_20', 'ema_10', 'macd', 'rsi', 'bb']
    
    try:
        result_df = add_indicators(df, requested)
        
        print("\n--- 결과 확인 ---")
        print(f"추가 후 컬럼: {result_df.columns.tolist()}")
        
        # 마지막 5줄 출력해서 값이 비어있지 않은지 확인
        print("\n최근 5개 데이터 샘플:")
        print(result_df[['close', 'SMA_20', 'EMA_10', 'MACD_12_26_9', 'RSI', 
        'bb_middle', 'bb_upper', 'bb_lower']].tail())
        
        if 'SMA_20' in result_df.columns and 'MACD_12_26_9' in result_df.columns:
            print("\n✅ 테스트 성공: 지표가 정상적으로 계산되고 병합되었습니다!")
        else:
            print("\n❌ 테스트 실패: 일부 지표 컬럼이 누락되었습니다.")

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")


if __name__ == "__main__":
    run_test()