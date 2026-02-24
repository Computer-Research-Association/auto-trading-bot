import React, { useState, useMemo, useEffect } from "react";
import "./StrategyPanelV2.css";
import { mockStrategiesV2, type StrategyV2 } from "../../mocks/mockStrategyV2";
import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";
import { apiFetch, apiPost } from "../../Lib/api";
// 필요한 타입만 부분적으로 정의 (전체 import 대신)
interface AssetItem {
  currency: string;
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  evaluation_krw: number;
}
interface PortfolioAssetsResponse {
  items: AssetItem[];
  summary: any;
}

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

// 🟢 Position Card Component
const PositionCard = ({ items }: { items: AssetItem[] }) => {
  // KRW 제외하고 보유수량 있는 코인만 필터링
  const coins = items.filter(i => i.symbol !== "KRW" && Number(i.quantity) > 0);

  if (coins.length === 0) {
    return (
      <div className="pos-card-empty">
        <span className="empty-text">보유 포지션 없음</span>
      </div>
    );
  }

  return (
    <div className="pos-card-list">
      {coins.map(coin => {
        // 목표가 (가상: 평단가 + 5%)
        const targetPrice = coin.avg_buy_price * 1.05; 
        
        return (
          <div key={coin.symbol} className="pos-card">
            <div className="pos-header">
              <div className="coin-icon-circle">
                {coin.symbol[0]}
              </div>
              <div className="pos-title">
                <span className="pos-symbol">{coin.symbol}</span>
                <span className="pos-status">(보유 중)</span>
              </div>
            </div>

            <div className="pos-body">
              {/* Row 1: Avg Price / Target */}
              <div className="pos-row">
                <span className="pos-label">평단가</span>
                <span className="pos-label target">목표가</span>
              </div>
              <div className="pos-row mb-2">
                <span className="pos-val">
                  {Math.floor(coin.avg_buy_price).toLocaleString()}
                </span>
                <span className="pos-val target">
                  {Math.floor(targetPrice).toLocaleString()}
                </span>
              </div>

              {/* Row 2: Current Price / PnL Rate */}
              <div className="pos-row">
                <span className="pos-label">현재가</span>
                <span className="pos-label">수익률</span>
              </div>
              <div className="pos-row">
                <span className={`pos-val ${coin.current_price >= coin.avg_buy_price ? "pos" : "neg"}`}>
                  {Math.floor(coin.current_price).toLocaleString()}
                </span>
                <span className={`pos-val ${coin.current_price >= coin.avg_buy_price ? "pos" : "neg"}`}>
                  {(coin.current_price >= coin.avg_buy_price ? "+" : "")}
                  {((coin.current_price - coin.avg_buy_price) / coin.avg_buy_price * 100).toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default function StrategyPanelV2() {
  const [strategies, setStrategies] = useState<StrategyV2[]>(mockStrategiesV2);
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set(["rsi_rebound"]));
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"return" | "winRate">("return");
  
  // 🟢 자산 데이터 상태
  const [assets, setAssets] = useState<AssetItem[]>([]);

  const [isDryRun, setIsDryRun] = useState<boolean>(false);

  // 🟢 봇 초기 상태 풀링 (시작 시 1회)
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await apiFetch<any>("/bot/status");
        if (res.is_active) {
          setRunningIds(new Set(["rsi_bb_core"])); // 백엔드가 켜져있으면 패널도 켜짐 상태로 동기화
        } else {
          setRunningIds(new Set());
        }
        
        if (res.is_dry_run !== undefined) {
          setIsDryRun(res.is_dry_run);
        }
      } catch (e) {
        console.error("Failed to fetch bot status on load", e);
      }
    };
    fetchStatus();
  }, []);

  // 🟢 자산 데이터 폴링 (1초)
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await apiFetch<PortfolioAssetsResponse>("/portfolio/assets");
        if (res && res.items) {
          setAssets(res.items);
        }
      } catch (err) {
        console.error("Failed to fetch assets for sidebar:", err);
      }
    };

    fetchAssets(); // 즉시 실행
    const interval = setInterval(fetchAssets, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleDryRun = async () => {
    try {
      const nextState = !isDryRun;
      // 백엔드 Dry Run API 호출
      await apiPost(`/bot/dry-run?enable=${nextState}`);
      setIsDryRun(nextState);
    } catch (err) {
      console.error("Failed to toggle dry run", err);
      alert("모의투자 모드 변경에 실패했습니다.");
    }
  };

  const toggleStrategy = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    // 이 패널 자체가 오직 RSI BB(rsi_bb_core) 전략과 직결되며 다른 전략은 보여주기용(mock)
    if (id !== "rsi_bb_core") {
      alert("현재 버전에서는 'RSI BB 매매 전략'만 실가동이 지원됩니다.");
      return;
    }

    try {
      const isCurrentlyRunning = runningIds.has(id);
      if (isCurrentlyRunning) {
        // 백엔드 중지 API 호출
        await apiPost("/bot/stop");
        setRunningIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      } else {
        // 백엔드 가동 API 호출
        await apiPost("/bot/start");
        setRunningIds((prev) => {
          const next = new Set(prev);
          next.add(id);
          return next;
        });
      }
    } catch (err) {
      console.error("Failed to toggle bot strategy:", err);
      alert("봇 설정 변경에 실패했습니다. 서버를 확인해주세요.");
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const stopAll = async () => {
    if (window.confirm("모든 전략을 정지하시겠습니까? (백엔드 봇이 중지됩니다)")) {
      try {
        await apiPost("/bot/stop");
        setRunningIds(new Set());
      } catch (err) {
        console.error("Failed to stop all strategies:", err);
        alert("봇 중지에 실패했습니다.");
      }
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
          <div 
            className={`dry-run-pill ${isDryRun ? "active" : ""}`}
            onClick={toggleDryRun}
            title="모의투자(실제 주문 X) 전용 모드 전환"
          >
            {isDryRun ? "모의투자 중" : "모의투자 OFF"}
          </div>
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

                  {/* 🟢 Position Card (New) - assets props 전달 */}
                  <div className="position-section">
                    <PositionCard items={assets} />
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
