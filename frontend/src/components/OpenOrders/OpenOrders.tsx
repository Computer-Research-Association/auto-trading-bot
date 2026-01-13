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
          <div>시간</div>
          <div>마켓명</div>
          <div>거래종류</div>
          <div>감시가격</div>
          <div>주문가격</div>
          <div>주문수량</div>
          <div>미체결량</div>
        </div>

        <div className="panel-empty">
          <div className="empty-icon" />
          <p>미체결 주문이 없습니다.</p>
        </div>
      </div>
    </div>
  );
}