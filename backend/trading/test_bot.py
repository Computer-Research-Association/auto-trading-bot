import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from trading.strategies.test_strategy import MacdBbRsiStrategy


def get_realistic_mock_data(n=150):
    """
    고가 < 저가와 같은 오류가 없는 현실적인 Mock 데이터를 생성합니다.
    """
    base_price = 100.0
    data = []
    current_time = datetime.now() - timedelta(minutes=n * 15)

    for i in range(n):
        # 변동성 부여 (이전 종가 기준 +- 1%)
        change = np.random.uniform(-0.01, 0.01)
        open_price = base_price
        close_price = base_price * (1 + change)

        # 고가는 open, close 중 높은 값보다 더 높게, 저가는 낮은 값보다 더 낮게
        high_price = max(open_price, close_price) * \
            (1 + np.random.uniform(0, 0.005))
        low_price = min(open_price, close_price) * \
            (1 - np.random.uniform(0, 0.005))
        volume = np.random.uniform(100, 1000)

        data.append(
            [
                current_time + timedelta(minutes=i * 15),
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
            ]
        )
        base_price = close_price  # 다음 캔들의 시가는 현재 종가

    df = pd.DataFrame(
        data, columns=["datetime", "open", "high", "low", "close", "volume"]
    )
    return df


def main():
    # 1. 전략 초기화 (외부 파라미터 주입 테스트)
    config = {
        "strategy_id": "TEST_STRAT_01",
        "params": {"rsi_len": 14, "rsi_buy_level": 50, "rsi_sell_level": 70},
        "required_candles": 20,
    }

    strategy = MacdBbRsiStrategy(**config)

    # 2. 테스트용 가짜 계좌 정보
    account_info = {"is_holding": False}

    print(f"🚀 {strategy.display_name} 통합 테스트 시작 (1단계)")
    print("-" * 50)

    try:
        while True:
            # [Step 1] 현실적인 Mock 데이터 수집
            df = get_realistic_mock_data(150)

            # [Step 2] 데이터 검증 (BaseStrategy 기능)
            is_valid, msg = strategy.validate_data(df)
            if not is_valid:
                print(f"❌ 데이터 검증 실패: {msg}")
                break

            # [Step 3] 지표 계산 (Strategy -> Indicators 핸들러 호출)
            # 전략이 정의한 output_name에 맞춰 컬럼이 생성되는지 확인하는 핵심 단계
            df_with_ind = strategy.setup_indicators(df)

            # [Step 4] 매매 판단 (MacdBbRsiStrategy.decide)
            result = strategy.decide(df_with_ind, account_info, {})

            # 결과 출력
            last_price = df_with_ind["close"].iloc[-1]
            # test_bot.py의 출력부 수정
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"Price: {last_price:.2f} | "
                # metadata 활용
                f"RSI: {result['metadata'].get('rsi', 0):.2f} | "
                f"BB_UP: {result['metadata'].get('bb_up', 0):.2f} | "
                f"BB_LOW: {result['metadata'].get('bb_low', 0):.2f} | "
                f"MACD: {result['metadata'].get('macd_hist', 0):.2f} | "
                f"Decision: {result['decision']} | "
                f"Reason: {result['reason']}"
            )
            # 테스트를 위해 판단 결과에 따라 가짜 계좌 상태 업데이트
            if result["decision"] == "BUY":
                account_info["is_holding"] = True
            elif result["decision"] == "SELL":
                account_info["is_holding"] = False

            # 너무 빠르지 않게 2초 대기
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n👋 테스트를 종료합니다.")


if __name__ == "__main__":
    main()
