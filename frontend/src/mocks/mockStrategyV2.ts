import type { Strategy } from "../types/strategy.types";

export interface StrategyV2 extends Strategy {
  descriptionDetail: string; // 더 긴 설명
  sparklineData: { value: number }[]; // 최근 20개 데이터 포인트
  dailyPnl: number; // 일일 수익금액
}

export const mockStrategiesV2: StrategyV2[] = [
  {
    id: "rsi_bb_core",
    name: "RSI BB 매매 전략",
    subtitle: "Core Trading Engine",
    desc: "RSI 과매도/과매수 및 볼린저 밴드 융합 전략",
    descriptionDetail: "현재 봇에 유일하게 탑재되어 실가동 중인 핵심 엔진입니다. RSI(14) 지표의 과매도 상태와 볼린저 밴드 하단 터치를 결합하여 안정적인 진입 타점을 잡고, 2-Loop 시스템을 통해 즉각적인 손오절을 집행합니다.",
    tags: ["핵심", "중간 리스크", "안정성"],
    rateOfReturn: 12.5,
    winRate: 64,
    mdd: 4.2,
    performanceScore: 82.2,
    dailyPnl: 125000,
    sparklineData: Array.from({ length: 20 }, () => ({ value: 10 + Math.random() * 5 })),
  },
  {
    id: "rsi_rebound",
    name: "RSI 과매도 반등",
    subtitle: "Mean Reversion",
    desc: "RSI 30 이하 구간에서 과매도 반등을 노리는 진입",
    descriptionDetail: "RSI(14) 지표가 30 이하로 떨어졌을 때 과매도 상태로 판단하여 분할 매수하고, 70 이상으로 올라갔을 때 매도하는 역추세 매매 전략입니다. 횡보장에서 유리합니다.",
    tags: ["역추세", "낮은 리스크", "5m·1h"],
    rateOfReturn: 13.8,
    winRate: 72,
    mdd: 3.8,
    performanceScore: 69,
    dailyPnl: 84000,
    sparklineData: Array.from({ length: 20 }, () => ({ value: 20 + Math.random() * 8 })),
  },
  {
    id: "bb_lower",
    name: "볼린저 밴드 하단 터치",
    subtitle: "Volatility Bounce",
    desc: "하단 밴드 터치 후 되돌림 구간에서 반등 매수",
    descriptionDetail: "볼린저 밴드(20, 2) 하단선을 터치하고 양봉이 발생했을 때 진입하여 중심선이나 상단선에서 청산하는 전략입니다. 변동성이 큰 장세에서 효과적입니다.",
    tags: ["변동성", "중간~높음", "15m·1h"],
    rateOfReturn: -2.3,
    winRate: 48,
    mdd: 12.5,
    performanceScore: 45.1,
    dailyPnl: -15000,
    sparklineData: Array.from({ length: 20 }, () => ({ value: 15 - Math.random() * 5 })),
  },
  {
    id: "scalping_v1",
    name: "초단타 스캘핑 V1",
    subtitle: "High Frequency",
    desc: "1분봉 기준 급등주 포착 및 빠른 차익 실현",
    descriptionDetail: "거래량이 급증하며 1분봉이 3% 이상 상승할 때 추격 매수하고, 1% 수익 시 즉시 매도하는 초단기 전략입니다.",
    tags: ["스캘핑", "높은 리스크", "1m"],
    rateOfReturn: 5.1,
    winRate: 90,
    mdd: 8.8,
    performanceScore: 58.4,
    dailyPnl: 42000,
    sparklineData: Array.from({ length: 20 }, () => ({ value: 5 + Math.random() * 3 })),
  },
];
