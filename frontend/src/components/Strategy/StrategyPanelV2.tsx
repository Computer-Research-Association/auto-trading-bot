import React, { useState, useMemo } from "react";
import "./StrategyPanelV2.css";
import { mockStrategiesV2, type StrategyV2 } from "../../mocks/mockStrategyV2";
import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";

const CustomDot = (props: any) => {
  const { cx, cy, index, payload, isPositive } = props;
  if (index === payload.length - 1) {
    return (
      <svg x={cx - 4} y={cy - 4} width={8} height={8}>
        <circle cx="4" cy="4" r="3" fill={isPositive ? "#ef4444" : "#3b82f6"} stroke="white" strokeWidth="1">
          <animate attributeName="r" values="3;4;3" dur="1.5s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="1;0.6;1" dur="1.5s" repeatCount="indefinite" />
        </circle>
      </svg>
    );
  }
  return null;
};

export default function StrategyPanelV2() {
  const [strategies, setStrategies] = useState<StrategyV2[]>(mockStrategiesV2);
// ... existing code ...

  const [runningIds, setRunningIds] = useState<Set<string>>(new Set(["rsi_rebound"]));
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"return" | "winRate">("return");

  const toggleStrategy = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setRunningIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const stopAll = () => {
    if (window.confirm("모든 전략을 정지하시겠습니까?")) {
      setRunningIds(new Set());
    }
  };

  const sortedStrategies = useMemo(() => {
    return [...strategies].sort((a, b) => {
      if (sortBy === "return") return b.rateOfReturn - a.rateOfReturn;
      if (sortBy === "winRate") return b.winRate - a.winRate;
      return 0;
    });
  }, [strategies, sortBy]);

  const getRiskClass = (tag: string) => {
    if (tag.includes("낮은")) return "risk-low";
    if (tag.includes("중간") && tag.includes("높음")) return "risk-high"; // 중간~높음 -> High
    if (tag.includes("중간")) return "risk-mid";
    if (tag.includes("높은")) return "risk-high";
    return "";
  };

  return (
    <aside className="strategy-panel-v2">
      <div className="panel-header">
        <h2>자동매매 전략</h2>
        <div className="header-actions">
          <button 
            className={`sort-btn ${sortBy === "return" ? "active" : ""}`}
            onClick={() => setSortBy("return")}
          >수익률순</button>
          <button 
            className={`sort-btn ${sortBy === "winRate" ? "active" : ""}`}
            onClick={() => setSortBy("winRate")}
          >승률순</button>
        </div>
      </div>

      <div className="strategy-list-v2">
        {sortedStrategies.map((s) => {
          const isRunning = runningIds.has(s.id);
          const isExpanded = expandedId === s.id;
          const isPositive = s.rateOfReturn >= 0;

          return (
            <div 
              key={s.id} 
              className={`strategy-card ${isRunning ? "active-border" : ""} ${isExpanded ? "expanded" : ""}`}
              onClick={() => toggleExpand(s.id)}
            >
              {/* Card Top: Always Visible */}
              <div className="card-main">
                <div className="info-col">
                  <div className="strategy-name-row">
                    <span className="name">{s.name}</span>
                    {isRunning && <span className="status-dot"></span>}
                  </div>
                  <div className="strategy-tags">
                    {s.tags.slice(0, 2).map(t => (
                      <span key={t} className={`mini-tag ${getRiskClass(t)}`}>{t}</span>
                    ))}
                  </div>
                </div>

                <div className="pnl-col">
                   <div className={`pnl-value ${isPositive ? "pos" : "neg"}`}>
                     {isPositive ? "+" : ""}{s.rateOfReturn}%
                   </div>
                   <div className="pnl-label">수익률</div>
                </div>

                <div className="action-col">
                  {/* Custom Toggle Switch */}
                  <div 
                    className={`toggle-switch ${isRunning ? "on" : "off"}`}
                    onClick={(e) => toggleStrategy(s.id, e)}
                  >
                    <div className="toggle-handle"></div>
                  </div>
                </div>
              </div>

              {/* Sparkline (Mini Chart) - 보여주기용 */}
              <div className="card-sparkline">
                <ResponsiveContainer width="100%" height={35}>
                  <AreaChart data={s.sparklineData} margin={{ top: 5, right: 5, left: 5, bottom: 0 }}>
                    <defs>
                      <linearGradient id={`grad-${s.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={isPositive ? "#ef4444" : "#3b82f6"} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={isPositive ? "#ef4444" : "#3b82f6"} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke={isPositive ? "#ef4444" : "#3b82f6"}
                      fill={`url(#grad-${s.id})`}
                      strokeWidth={2}
                      isAnimationActive={true}
                      animationDuration={1500}
                      dot={(props) => <CustomDot {...props} isPositive={isPositive} payload={s.sparklineData} />}
                    />
                    <YAxis domain={['dataMin', 'dataMax']} hide />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Expanded Details (Accordion) */}
              {isExpanded && (
                <div className="card-details">
                  <p className="description">{s.descriptionDetail}</p>
                  
                  <div className="detail-metrics">
                    <div className="d-metric">
                      <span className="label">승률</span>
                      <span className="value">{s.winRate}%</span>
                    </div>

                    <div className="d-metric">
                      <span className="label">일일 손익</span>
                      <span className={`value ${s.dailyPnl >= 0 ? "pos" : "neg"}`}>
                        {s.dailyPnl.toLocaleString()}원
                      </span>
                    </div>
                  </div>


                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="panel-footer">
        <button className="stop-all-btn" onClick={stopAll}>
          모든 전략 중지 
        </button>
      </div>
    </aside>
  );
}
