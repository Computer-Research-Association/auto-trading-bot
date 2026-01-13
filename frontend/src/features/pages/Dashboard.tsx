// src/pages/Dashboard.jsx
import React, { useState } from "react";

// 컴포넌트 불러오기
import Assets from './features/components/Assets/Assets';
import ProfitLoss from './features/components/ProfitLoss/ProfitLoss';
import History from './features/components/History/History';
import OpenOrders from './features/components/OpenOrders/OpenOrders';
import StrategyPanel from './features/components/Strategy/StrategyPanel'; // 폴더명이 Strategy네요
import Auto_Strategy from './features/components/Auto_Strategy/Auto_Strategy';

export default function Dashboard() {
  // 탭 상태 관리 (기본값: 'open')
  const [tab, setTab] = useState("open");

  return (
    <div className="page-wrap">
      {/* 1. 상단 탭 버튼 영역 (여기에 버튼 4개를 다 넣어야 합니다) */}
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

        <button
          className={`sub-tab ${tab === "auto" ? "active" : ""}`} 
          onClick={() => setTab("auto")}
        >

          자동매매
        </button>
      </div>

      {/* 2. 실제 컨텐츠 표시 영역 */}
      <div className="page-content">
        <div className="content-left">
           {/* 탭 상태(tab)에 따라 보여줄 컴포넌트를 갈아끼웁니다 */}
           {tab === "balance" && <Assets />}
           {tab === "profit" && <ProfitLoss />}
           {tab === "history" && <History />}
           {tab === "open" && <OpenOrders />}
           {tab === "auto" && <Auto_Strategy />}
        </div>

        {/* 오른쪽 전략 패널은 항상 고정 */}
        <StrategyPanel />
      </div>
    </div>
  );
}