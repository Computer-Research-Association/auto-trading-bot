// src/pages/Dashboard.tsx
import React, { useState } from "react";

// 컴포넌트 불러오기
// FIXME: 각 컴포넌트가 .tsx로 변환되면 확장자 없이 import 가능 또는 명시적 .tsx 필요 여부는 tsconfig 설정에 따라 다름
// import StrategyPanel from "../components/Strategy/StrategyPanel"; // V1
import StrategyPanelV2 from "../components/Strategy/StrategyPanelV2"; // V2 Prototype

import Assets from "../components/Assets/Assets";
import ProfitLoss from "../components/ProfitLoss/ProfitLoss";
import History from "../components/History/History";
import Log from "../components/Log/Log";

type TabType = "balance" | "profit" | "history" | "log";

const VALID_TABS: TabType[] = ["balance", "profit", "history", "log"];

export default function Dashboard() {
    // 새로고침 후에도 마지막 탭을 유지 (localStorage 사용)
    const [tab, setTab] = useState<TabType>(() => {
        const saved = localStorage.getItem("activeTab");
        return VALID_TABS.includes(saved as TabType) ? (saved as TabType) : "balance";
    });

    const handleTabChange = (newTab: TabType) => {
        setTab(newTab);
        localStorage.setItem("activeTab", newTab);
    };

    return (
        <div className="page-wrap">
            {/* 1. 상단 탭 버튼 영역 */}
            <div className="sub-tab-bar">
                <button
                    className={`sub-tab ${tab === "balance" ? "active" : ""}`}
                    onClick={() => handleTabChange("balance")}
                >
                    보유자산
                </button>
                <button
                    className={`sub-tab ${tab === "profit" ? "active" : ""}`}
                    onClick={() => handleTabChange("profit")}
                >
                    투자손익
                </button>
                <button
                    className={`sub-tab ${tab === "history" ? "active" : ""}`}
                    onClick={() => handleTabChange("history")}
                >
                    거래내역
                </button>
                <button
                    className={`sub-tab ${tab === "log" ? "active" : ""}`}
                    onClick={() => handleTabChange("log")}
                >
                    로그
                </button>
            </div>

            {/* 2. 실제 컨텐츠 표시 영역 */}
            <div className="page-content">
                <div className="content-left">
                    {tab === "balance" && <Assets />}
                    {tab === "profit" && <ProfitLoss />}
                    {tab === "history" && <History />}
                    {tab === "log" && <Log />}
                </div>

                {/* 오른쪽 전략 패널 V2 적용 */}
                <StrategyPanelV2 />
            </div>
        </div>
    );
}
