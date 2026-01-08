// src/pages/Dashboard.jsx
import React, { useState } from "react";

// 컴포넌트 import 경로 주의! (..로 한 번 더 나가야 함)
import StrategyPanel from "../components/Strategy/StrategyPanel";
import OpenOrders from "../components/OpenOrders/OpenOrders";
import Assets from "../components/Assets/Assets";
import ProfitLoss from "../components/ProfitLoss/ProfitLoss";
import History from "../components/History/History";

export default function Dashboard() {
  const [tab, setTab] = useState("open"); // 탭 상태는 여기서 관리

  return (
    <div className="page-wrap">
      {/* 상단 탭 버튼들 */}
      <div className="sub-tab-bar">
        <button className={`sub-tab ${tab === "balance" ? "active" : ""}`} onClick={() => setTab("balance")}>보유자산</button>
        {/* ... 나머지 탭 버튼들 ... */}
        <button className={`sub-tab ${tab === "open" ? "active" : ""}`} onClick={() => setTab("open")}>미체결</button>
      </div>

      {/* 실제 컨텐츠 내용 */}
      <div className="page-content">
        <div className="content-left">
           {tab === "balance" && <Assets />}
           {/* ... 나머지 조건부 렌더링 ... */}
           {tab === "open" && <OpenOrders />}
        </div>
        <StrategyPanel />
      </div>
    </div>
  );
}