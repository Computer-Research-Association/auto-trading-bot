import React, { useMemo, useState, useEffect } from "react";
import "./StrategyPanel.css";
import type { Strategy } from "../../types/strategy.types";
import { mockStrategyPanel } from "../../mocks/mockStrategy";

const INITIAL_STRATEGIES: Strategy[] = [
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

export default function StrategyPanel() {
  const [strategies, setStrategies] = useState<Strategy[]>(INITIAL_STRATEGIES);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string>("ma_cross");
  // 실행 중인 전략 ID들을 Set으로 관리
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set());

  //   useEffect(() => {
  //   fetch("/api/strategies")
  //     .then((res) => res.json())
  //     .then(setStrategies)
  //     .catch(console.error);
  // }, []);

  useEffect(() => {
    setStrategies(mockStrategyPanel);
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return strategies;
    return strategies.filter((s) => s.name.toLowerCase().includes(q));
  }, [query, strategies]);

  // {filtered.map((s) => (
  //   <StrategyCard key={s.id} strategy={s} />
  // ))}

  const toggleStrategy = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();

    const isRunning = runningIds.has(id);
    const url = isRunning
      ? `/api/strategies/${id}/stop`
      : `/api/strategies/${id}/start`;

    try {
      await fetch(url, { method: "POST" });

      setRunningIds((prev) => {
        const next = new Set(prev);
        isRunning ? next.delete(id) : next.add(id);
        return next;
      });
    } catch (err) {
      alert("전략 상태 변경 실패");
    }
  };

  const stopAll = () => setRunningIds(new Set());

  return (
    <aside className="strategy-panel">
      {/* Header */}
      <div className="strategy-header">
        <div className="strategy-title-row">
          <h2 className="strategy-title">Trading Strategies</h2>
          <span className="strategy-badge">BETA</span>
        </div>
        <p className="strategy-subtitle">자동매매 전략을 독립적으로 가동하거나 중지할 수 있습니다.</p>

        <div className="strategy-search-wrap">
          <input
            className="strategy-search"
            placeholder="전략 검색 (예: RSI, 볼린저)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      <hr className="strategy-divider" />

      {/* List */}
      <div className="strategy-list">
        {filtered.map((s) => {
          const isSelected = s.id === selectedId;
          const isRunning = runningIds.has(s.id);
          return (
            <div
              key={s.id}
              className={`strategy-item ${isSelected ? "selected" : ""} ${isRunning ? "running" : ""}`}
              onClick={() => setSelectedId(s.id)}
            >
              <div className="strategy-item-top">
                <div className="strategy-item-title">
                  <span className="strategy-name">{s.name}</span>
                  <span className="strategy-sub">{s.subtitle}</span>
                </div>

                <button
                  type="button"
                  className={`item-toggle-btn ${isRunning ? "stop" : "start"}`}
                  onClick={(e) => toggleStrategy(s.id, e)}
                >
                  {isRunning ? "정지" : "시작"}
                </button>
              </div>

              <p className="strategy-desc">{s.desc}</p>

              <div className="strategy-metrics">
                <div className="metric">
                  <span className="metric-label">수익률</span>
                  <span className={`metric-value ${s.rateOfReturn >= 0 ? "plus" : "minus"}`}>
                    {s.rateOfReturn > 0 && "+"}{s.rateOfReturn}%
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">승률</span>
                  <span className="metric-value">{s.winRate}%</span>
                </div>
                <div className="metric">
                  <span className="metric-label">MDD</span>
                  <span className="metric-value minus">{s.mdd}%</span>
                </div>
                <div className="metric score">
                  <span className="metric-label">성과 점수</span>
                  <span className="metric-value">{s.performanceScore}</span>
                </div>
              </div>

              <div className="strategy-item-bottom">
                <div className="strategy-tags">
                  {(s.tags ?? []).map((t) => (
                    <span key={t} className="tag">
                      {t}
                    </span>
                  ))}
                </div>
                {isRunning && (
                  <div className="running-indicator">
                    <span className="dot on" />
                    <span className="status-text">Active</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="strategy-footer">
        <div className="summary-status-bar">
          <div className="status-info">
            <span className="label">Active Strategies</span>
            <span className="count">{runningIds.size}</span>
          </div>
          {runningIds.size > 0 && (
            <button type="button" className="stop-all-btn" onClick={stopAll}>
              전체 정지
            </button>
          )}
        </div>
        <div className="footer-hint">
          * 여러 전략을 동시 가동할 경우 자산 배분에 유의하세요.
        </div>
      </div>
    </aside>
  );
}