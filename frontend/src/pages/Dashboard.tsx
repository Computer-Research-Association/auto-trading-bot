// src/pages/Dashboard.tsx
import React, { useState } from "react";

// 컴포넌트 불러오기
// FIXME: 각 컴포넌트가 .tsx로 변환되면 확장자 없이 import 가능 또는 명시적 .tsx 필요 여부는 tsconfig 설정에 따라 다름
import StrategyPanel from "../components/Strategy/StrategyPanel";
import Assets from "../components/Assets/Assets";
import ProfitLoss from "../components/ProfitLoss/ProfitLoss";
import History from "../components/History/History";
import Log from "../components/Log/Log";

type TabType = "balance" | "profit" | "history" | "log";

export default function Dashboard() {
    // 탭 상태 관리 (기본값: 'balance'로 변경 - 사용자가 요청한 주요 화면이므로)
    const [tab, setTab] = useState<TabType>("balance");

    return (
        <div className="page-wrap">
            {/* 1. 상단 탭 버튼 영역 */}
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
                    className={`sub-tab ${tab === "log" ? "active" : ""}`}
                    onClick={() => setTab("log")}
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

                {/* 오른쪽 전략 패널은 항상 고정 */}
                <StrategyPanel />
            </div>
        </div>
    );
}
