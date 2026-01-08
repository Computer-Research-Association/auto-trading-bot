import React from 'react';
import './OpenOrders.css';

export default function OpenOrders() {
  return (
    <div className="main-panel">
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
    </div>
  );
}