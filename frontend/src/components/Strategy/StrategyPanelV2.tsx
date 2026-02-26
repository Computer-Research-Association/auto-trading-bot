import React, { useState, useMemo, useEffect } from "react";
import "./StrategyPanelV2.css";
import { mockStrategiesV2, type StrategyV2 } from "../../mocks/mockStrategyV2";
import { AreaChart, Area, ResponsiveContainer, YAxis } from "recharts";
import { apiFetch, apiPost } from "../../Lib/api";
// 필요한 타입만 부분적으로 정의 (전체 import 대신)

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
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set([]));
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"return" | "default">("default");
  
  const [botLog, setBotLog] = useState<any>(null); // ✅ 추가: 봇 세부 상태 저장
  const [isDryRun, setIsDryRun] = useState<boolean>(false);
  const [totalTrades, setTotalTrades] = useState<number>(0);

  // 📊 총 체결 횟수: 마운트 시 초기값 조회 + Log SSE로 실시간 반영
  useEffect(() => {
    // ① 최초 누적 카운트 1회 조회
    apiFetch<{ items: any[]; total_count: number }>(
      "/v1/logs?eventname=BUY&eventname=SELL&filter_op=OR&limit=1"
    )
      .then(res => setTotalTrades(res?.total_count ?? 0))
      .catch(() => setTotalTrades(0));

    // ② Log SSE 구독 — BUY / SELL 이벤트 수신 시마다 +1
    const es = new EventSource("http://localhost:8000/api/v1/logs/stream");
    es.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        const name = (log?.eventname ?? log?.event_name ?? "").toUpperCase();
        if (name === "BUY" || name === "SELL") {
          setTotalTrades(prev => prev + 1);
        }
      } catch { /* ignore */ }
    };
    es.onerror = () => es.close();

    return () => es.close(); // 언마운트 시 구독 해제
  }, []);

  // 🟢 봇 상태 SSE (Server-Sent Events) 최적화로 대체
  useEffect(() => {
    let eventSource: EventSource | null = null;
    
    const connectSSE = () => {
      // 프록시 환경 혹은 백엔드 주소로 연결
      eventSource = new EventSource("http://localhost:8000/api/bot/stream");
      
      eventSource.onmessage = (event) => {
        try {
          const res = JSON.parse(event.data);
          setBotLog(res); // 전체 상태 보존
          if (res && res.is_active) {
            setRunningIds(new Set(["rsi_bb_core"])); // 본 봇 활성화 동기화
          } else {
            setRunningIds(new Set());
          }
          
          if (res && res.is_dry_run !== undefined) {
            setIsDryRun(res.is_dry_run);
          }
        } catch (e) {
          console.error("SSE 데이터 파싱 실패", e);
        }
      };

      eventSource.onerror = (error) => {
        console.error("❌ 봇 상태 SSE 스트림 오류:", error);
        eventSource?.close();
      };
    };

    connectSSE();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
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

    const isCurrentlyRunning = runningIds.has(id);

    // 1️⃣ [낙관적 업데이트] 통신 전에 일단 React 화면(Toggle)부터 즉시 뒤집어 줌
    setRunningIds((prev) => {
      const next = new Set(prev);
      isCurrentlyRunning ? next.delete(id) : next.add(id);
      return next;
    });

    // 2️⃣ [백그라운드 통신] 서버에 명령을 하달함
    try {
      if (isCurrentlyRunning) {
        // 백엔드 중지 API 호출
        await apiPost("/bot/stop");
      } else {
        // 백엔드 가동 API 호출
        await apiPost("/bot/start");
      }
    } catch (err) {
      // 3️⃣ [롤백 처리] 서버에서 에러가 났다면, 조용히 아까 바꿨던 토글을 원상복구시켜줌
      console.error("Failed to toggle bot strategy:", err);
      alert("봇 상태 변경 실패. 롤백합니다.");
      setRunningIds((prev) => {
        const next = new Set(prev);
        isCurrentlyRunning ? next.add(id) : next.delete(id); // 다시 반대로 돌리기
        return next;
      });
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
            onClick={() => setSortBy(prev => prev === "return" ? "default" : "return")}
          >수익률순</button>
        </div>
      </div>

      <div className="strategy-list-v2">
        {sortedStrategies.map((s) => {
          let isRunning = runningIds.has(s.id);
          const isExpanded = expandedId === s.id;
          
          // 🔥 보조 계산 로직 (목표 익절/손절 퍼센트)
          let estProfitPct = 0;
          let estLossPct = 0;
          if (botLog && botLog.target_buy_price && botLog.target_buy_price > 0) {
            if (botLog.target_sell_price && botLog.target_sell_price > botLog.target_buy_price) {
              estProfitPct = ((botLog.target_sell_price - botLog.target_buy_price) / botLog.target_buy_price) * 100;
            }
            if (botLog.target_stop_loss && botLog.target_stop_loss > 0 && botLog.target_stop_loss < botLog.target_buy_price) {
              estLossPct = ((botLog.target_stop_loss - botLog.target_buy_price) / botLog.target_buy_price) * 100;
            }
          }

          // 🔥 진짜 백엔드 데이터 연동 (RSI BB 코어 한정)
          let displayPnl = s.rateOfReturn;
          let chartData = s.sparklineData; // 기본값은 목업 데이터
          
          if (s.id === "rsi_bb_core") {
            // 백엔드가 살아있다면 서비스단의 수익률을 최우선으로 사용
            if (botLog) {
              // 백엔드의 profit_rate (미보유 시 0.0)
              displayPnl = Number(botLog.profit_rate?.toFixed(2) || 0);

              // 백엔드에서 sparkline_data 배열을 줬다면 그걸로 차트 렌더링
              if (botLog.sparkline_data && Array.isArray(botLog.sparkline_data) && botLog.sparkline_data.length > 0) {
                chartData = botLog.sparkline_data.map((val: number) => ({ value: val }));
              }
            } else {
              displayPnl = 0.00;
            }
          }
          const isPositive = displayPnl >= 0;
          const isDisabled = s.id !== "rsi_bb_core";

          return (
            <div 
              key={s.id} 
              className={`strategy-card ${isRunning ? "active-border" : ""} ${isExpanded ? "expanded" : ""} ${isDisabled ? "disabled-card" : ""}`}
              style={isDisabled ? { opacity: 0.6 } : {}}
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
                     {isPositive ? "+" : ""}{displayPnl}%
                   </div>
                   <div className="pnl-label">수익률</div>
                </div>

                <div className="action-col">
                  {/* Custom Toggle Switch */}
                  {!isDisabled ? (
                    <div 
                      className={`toggle-switch ${isRunning ? "on" : "off"}`}
                      onClick={(e) => toggleStrategy(s.id, e)}
                    >
                      <div className="toggle-handle"></div>
                    </div>
                  ) : (
                    <div style={{fontSize: "1.2rem", opacity: 0.5, cursor: "not-allowed"}} title="준비 중인 전략입니다." onClick={(e) => e.stopPropagation()}>
                      🔒
                    </div>
                  )}
                </div>
              </div>

              {/* Sparkline (Mini Chart) - 보여주기용 */}
              <div className="card-sparkline">
                <ResponsiveContainer width="100%" height={35}>
                  <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 0 }}>
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
                      dot={(props) => <CustomDot {...props} isPositive={isPositive} payload={chartData} />}
                    />
                    <YAxis domain={['dataMin', 'dataMax']} hide />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Expanded Details (Accordion) */}
              {isExpanded && (
                <div className="card-details">
                  {!isDisabled ? (
                    <>
                      <div className="bot-log-section">
                        <div className="section-title">
                          <div className="status-dot-icon">
                            <div className={`status-dot-inner ${isRunning ? 'active' : ''}`}></div>
                          </div>
                          현재 봇 상태
                        </div>
                        <div className="premium-card">
                          <div className="status-text-content">
                            <span style={{color: '#94a3b8', marginRight: '4px'}}>&gt;</span> 
                            {botLog?.last_reason ? botLog.last_reason : "대기 중..."}
                          </div>
                        </div>
                      </div>

                      <div className="bot-target-section">
                        <div className="section-title muted-title">
                          <svg className="bullseye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <circle cx="12" cy="12" r="5"></circle>
                            <circle cx="12" cy="12" r="1"></circle>
                          </svg>
                          작전 목표 <span className="title-sub">TARGET</span>
                        </div>
                        
                        <div className="premium-card target-card-full mb-2">
                          <span className="target-label">다음 진입 목표가</span>
                          {botLog?.target_buy_price && botLog.target_buy_price > 0 
                            ? <span className="target-val">{Math.floor(botLog.target_buy_price).toLocaleString()} 원</span>
                            : botLog?.profit_rate !== undefined && botLog?.profit_rate !== 0
                              ? <span className="target-val" style={{color: '#3b82f6'}}>현재 코인 등락 감시 중... (보유 중)</span>
                              : <span className="target-val muted">(대기 - RSI 미충족)</span>}
                        </div>

                        <div className="target-grid">
                          <div className="premium-card target-card-col">
                            <span className="target-label">
                              목표 익절가
                              {estProfitPct > 0 && <span className="target-percent positive">(+{estProfitPct.toFixed(2)}%)</span>}
                            </span>
                            <div className="target-val-wrapper">
                              <div className="status-dot-icon" style={{width: 10, height: 10, marginTop: 4, background: 'transparent'}}><div className="status-dot-inner" style={{width: 5, height: 5}}></div></div>
                              {botLog?.target_sell_price && botLog.target_sell_price > 0 
                                ? <span className="target-val">
                                    {Math.floor(botLog.target_sell_price).toLocaleString()}
                                  </span>
                                : <span className="target-val muted">대기 -<br/>분석 중</span>}
                            </div>
                          </div>
                          <div className="premium-card target-card-col">
                            <span className="target-label">
                              목표 손절가
                              {estLossPct < 0 && <span className="target-percent negative">({estLossPct.toFixed(2)}%)</span>}
                            </span>
                            <div className="target-val-wrapper">
                              <div className="status-dot-icon" style={{width: 10, height: 10, marginTop: 4, background: 'transparent'}}><div className="status-dot-inner" style={{width: 5, height: 5}}></div></div>
                              {botLog?.target_stop_loss && botLog.target_stop_loss > 0 
                                ? <span className="target-val">
                                    {Math.floor(botLog.target_stop_loss).toLocaleString()}
                                  </span>
                                : <span className="target-val muted">대기 -<br/>분석 중</span>}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="strategy-run-section">
                        <div className="strategy-stats-row">
                          <div className="stat-box blue">
                            <span className="stat-label">총 체결 횟수</span>
                            <span className="stat-value">{totalTrades}회</span>
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="dummy-details">
                      <div className="dummy-icon">🛠️</div>
                      <div className="dummy-title">
                        이 전략 모듈은 현재 백엔드(서버)에 플러그인되지 않아 <br/>
                        <span style={{color: "#EF4444"}}>준비 중</span>입니다.
                      </div>
                      <div className="dummy-desc">{s.descriptionDetail}</div>
                    </div>
                  )}
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
