import React, { useState,useEffect } from "react";

// 분리한 컴포넌트들 불러오기
import StrategyPanel from "./Strategy/StrategyPanel";
import OpenOrders from "./OpenOrders/OpenOrders";
import Assets from "./Assets/Assets";
import ProfitLoss from "./ProfitLoss/ProfitLoss";
import History from "./History/History";

export default function TradingLayout() {
  const [tab, setTab] = useState("open"); // 기본값: 미체결
  const [currentTime, setCurrentTime] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date()); // 매초 새로운 시간으로 업데이트
    }, 1000);
    return () => clearInterval(timer);
  }, []);
    const formatTime = (date) => {
      return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    };

  return (
    <div className="app-root">
      {/* 1. 상단 파란색 헤더 */}
      <header className="top-nav">
        <div className="nav-left">
          <div className="logo">Gold bar</div>
        </div>
        <div className="nav-right">
          <span className="nav-time">{formatTime(currentTime)}</span>
          <button className="nav-small">My</button>
        </div>
      </header>

      <div className="page-wrap">
        {/* 2. 탭 선택 바 */}
        <div className="sub-tab-bar">
          <button 
            className={`sub-tab ${tab === "balance" ? "active" : ""}`}
            onClick={() => setTab("balance")}
          >
            보유자산
          </button>
          <button 
            className={`sub-tab ${tab === "profit" ? "active" : ""}`}
            onClick={() => setTab("profit")}
          >
            투자손익
          </button>
          <button 
            className={`sub-tab ${tab === "history" ? "active" : ""}`}
            onClick={() => setTab("history")}
          >
            거래내역
          </button>
          <button 
            className={`sub-tab ${tab === "open" ? "active" : ""}`}
            onClick={() => setTab("open")}
          >
            미체결
          </button>
        </div>

        {/* 3. 메인 콘텐츠 영역 (Grid Layout) */}
        <div className="page-content">
          
          {/* 왼쪽: 탭에 따라 다른 컴포넌트 보여주기 */}
          <div className="content-left">
            {tab === "balance" && <Assets />}
            {tab === "profit" && <ProfitLoss />}
            {tab === "history" && <History />}
            {tab === "open" && <OpenOrders />}
          </div>

          {/* 오른쪽: 전략 패널 (항상 고정) */}
          <StrategyPanel />
          
        </div>
      </div>
    </div>
  );
}