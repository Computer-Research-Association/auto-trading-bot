import type { Strategy } from "../types/strategy.types";

export const mockStrategyPanel: Strategy[] = [
  {
    id: "ma_cross",
    name: "이동평균선 골든크로스",
    subtitle: "Trend Following",
    desc: "단기 이평선이 장기 이평선을 상향 돌파할 때 진입",
    tags: ["추세", "중간 리스크", "5m·15m"],
    rateOfReturn: 12.5,
    winRate: 64,
    mdd: 4.2,
    performanceScore: 62.2,
  },
  {
    id: "rsi_rebound",
    name: "RSI 과매도 반등",
    subtitle: "Mean Reversion",
    desc: "RSI 30 이하 구간에서 과매도 반등을 노리는 진입",
    tags: ["역추세", "낮은 리스크", "5m·1h"],
    rateOfReturn: 13,
    winRate: 72,
    mdd: 3.8,
    performanceScore: 69,
  },
  {
    id: "bb_lower",
    name: "볼린저 밴드 하단 터치",
    subtitle: "Volatility Bounce",
    desc: "하단 밴드 터치 후 되돌림 구간에서 반등 매수",
    tags: ["변동성", "중간~높음", "15m·1h"],
    rateOfReturn: -9.8,
    winRate: 48,
    mdd: 12.5,
    performanceScore: 26.1,
  },
];
