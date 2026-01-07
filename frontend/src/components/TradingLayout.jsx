// src/components/TradingLayout.jsx
import React, { useState } from "react";

export default function TradingLayout() {
  // 아래 흰색 탭바 상태
  const [tab, setTab] = useState("open"); // balance, profit, history, open, wait

  return (
    <div className="app-root">
      {/* 맨 위 파란 Upbit 같은 바 */}
      <header className="top-nav">
        <div className="nav-left">
          <div className="logo">Gold bar</div>

          <nav className="top-menu">
            <button className="nav-link active">투자내역</button>
          </nav>
        </div>

        <div className="nav-right">
          <span className="nav-time">02:41</span>
          <button className="nav-small">My</button>
        </div>
      </header>

      {/* 여기부터가 밑에 영역 전체 */}
      <div className="page-wrap">
        {/* 2번째 탭바 (보유자산 / 투자손익 / … / 입출금대기) */}
        <div className="sub-tab-bar">
          <button
            className={tab === "balance" ? "sub-tab active" : "sub-tab"}
            onClick={() => setTab("balance")}
          >
            보유자산
          </button>
          <button
            className={tab === "profit" ? "sub-tab active" : "sub-tab"}
            onClick={() => setTab("profit")}
          >
            투자손익
          </button>
          <button
            className={tab === "history" ? "sub-tab active" : "sub-tab"}
            onClick={() => setTab("history")}
          >
            거래내역
          </button>
          <button
            className={tab === "open" ? "sub-tab active" : "sub-tab"}
            onClick={() => setTab("open")}
          >
            미체결
          </button>
          <button
            className={tab === "wait" ? "sub-tab active" : "sub-tab"}
            onClick={() => setTab("wait")}
          >
            입출금대기
          </button>
        </div>

        {/* 아래 큰 칸 + 오른쪽 코인 리스트 */}
        <div className="page-content">
          {/* 왼쪽 큰 칸 */}
          <div className="main-panel">
            {tab === "open" && (
              <>
                <div className="panel-toolbar">
                  <button className="toolbar-select">전체주문 ▾</button>
                  <button className="toolbar-btn" disabled>
                    일괄취소
                  </button>
                </div>

                <div className="panel-table">
                  <div className="panel-table-header">
                    <span>시간</span>
                    <span>마켓명</span>
                    <span>거래종류</span>
                    <span>감시가격</span>
                    <span>주문가격</span>
                    <span>주문수량</span>
                    <span>미체결량</span>
                  </div>

                  <div className="panel-empty">
                    <div className="empty-icon" />
                    <p>미체결 주문이 없습니다.</p>
                  </div>
                </div>
              </>
            )}

            {tab === "balance" && (
              <div className="panel-placeholder">보유자산 탭 내용 자리</div>
            )}
            {tab === "profit" && (
              <div className="panel-placeholder">투자손익 탭 내용 자리</div>
            )}
            {tab === "history" && (
              <div className="panel-placeholder">거래내역 탭 내용 자리</div>
            )}
            {tab === "wait" && (
              <div className="panel-placeholder">입출금대기 탭 내용 자리</div>
            )}
          </div>

          {/* 오른쪽 코인 리스트 칸  */}
          <aside className="market-panel">
            <div className="market-header">
              <div className="market-tabs">
                <button className="market-tab active">원화</button>
                <button className="market-tab">BTC</button>
                <button className="market-tab">USDT</button>
              </div>
              <input
                className="market-search"
                placeholder="코인명/심볼검색"
              />
            </div>

            <div className="market-table-header">
              <span>한글명</span>
              <span>현재가</span>
              <span>전일대비</span>
              <span>거래대금</span>
            </div>

            <div className="market-empty">
              오른쪽 코인 리스트 자리 (나중에 데이터 넣기)
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
