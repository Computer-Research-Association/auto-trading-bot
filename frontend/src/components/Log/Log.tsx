import React, { useState, useEffect } from 'react';
import './Log.css';
import Loading from '../Common/Loading.js';

interface Log {
    id: string;
    strategyName: string;
    strategyDescription: string;
    rateofreturn: number; // 수익률 (%)
    winRate: number;      // 승률 (%)
    mdd: number;          // 최대 낙폭 (%)
    transaction: number;  // 총 거래 수
    runningDays: number;  // 가동 일수
    status: 'running' | 'stopped';
}

const types_strategies: Log[] = [
    {
        id: "ma_cross",
        strategyName: "이동평균선 골든크로스",
        strategyDescription: "단기 이평선이 장기 이평선을 상향 돌파할 때 진입하여 추세를 추종하는 전략입니다.",
        rateofreturn: 12.5,
        winRate: 64,
        mdd: 4.2,
        transaction: 30,
        runningDays: 15,
        status: 'running'
    },
    {
        id: "rsi_rebound",
        strategyName: "RSI 과매도 반등",
        strategyDescription: "RSI 30 이하 구간에서 과매도된 코인의 기술적 반등을 노리는 단기 전략입니다.",
        rateofreturn: 13.0,
        winRate: 72,
        mdd: 3.8,
        transaction: 60,
        runningDays: 45,
        status: 'running'
    },
    {
        id: "bb_lower",
        strategyName: "볼린저 밴드 하단 터치",
        strategyDescription: "변동성이 큰 시장에서 볼린저 밴드 하단 이탈 후 회복 시점을 포착하여 매수합니다.",
        rateofreturn: -9.8,
        winRate: 48,
        mdd: 12.5,
        transaction: 45,
        runningDays: 20,
        status: 'stopped'
    },
];

const Log: React.FC = () => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // 시각적 고도화를 위한 시뮬레이션 로딩
        const timer = setTimeout(() => setLoading(false), 400);
        return () => clearTimeout(timer);
    }, []);

    if (loading) {
        return <Loading message="자동매매 전략을 분석 중입니다..." />;
    }

    return (
        <div className="main-panel">
            <div className="strategy-grid">
                {types_strategies.map((strategy) => (
                    <div className="strategy-card" key={strategy.id}>
                        <div className="card-header">
                            <div>
                                <h3 className="strategy-name">{strategy.strategyName}</h3>
                                <p className="strategy-desc">{strategy.strategyDescription}</p>
                            </div>
                        </div>

                        <div className="metrics-grid">
                            <div className="metric-item">
                                <span className="metric-label">수익률</span>
                                <span className={`metric-value ${strategy.rateofreturn >= 0 ? 'positive' : 'negative'}`}>
                                    {strategy.rateofreturn > 0 ? '+' : ''}{strategy.rateofreturn}%
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">승률</span>
                                <span className="metric-value">{strategy.winRate}%</span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">최대 낙폭(MDD)</span>
                                <span className="metric-value">{strategy.mdd}%</span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">거래 횟수</span>
                                <span className="metric-value">{strategy.transaction}회</span>
                            </div>
                            <div className="metric-item">
                                <span className="metric-label">가동 일수</span>
                                <span className="metric-value">{strategy.runningDays}일</span>
                            </div>
                        </div>

                        <div className="performance-bar-wrap">
                            <div className="performance-bar-label">
                                <span>성과 점수</span>
                                <span>{(strategy.winRate * 0.7 + (100 - strategy.mdd * 10) * 0.3).toFixed(1)}점</span>
                            </div>
                            <div className="performance-bar">
                                <div
                                    className="performance-fill"
                                    style={{ width: `${strategy.winRate * 0.7 + (100 - strategy.mdd * 10) * 0.3}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Log;