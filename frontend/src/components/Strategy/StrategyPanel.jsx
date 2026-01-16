import React from 'react';
import './StrategyPanel.css'; // 스타일 파일 import

export default function StrategyPanel() {
  return (
    <aside className="strategy-panel">
      <div className="strategy-header">
        <h2 className="strategy-title">자동매매 전략 선택</h2>
        <input className="strategy-search" placeholder="전략 명칭 검색" />
      </div>

      <hr className="strategy-divider" />

      <div className="strategy-list">
        {/* 나중에 데이터를 map으로 뿌릴 수 있게 구조화 */}
        <div className="strategy-item active">
          <span className="strategy-name">이동평균선 골든크로스</span>
          <p className="strategy-desc">단기 이평선이 장기 이평선을 돌파할 때 매수</p>
          <button className="strategy-select-btn">선택</button>
        </div>

        <div className="strategy-item">
          <span className="strategy-name">RSI 과매도 반등</span>
          <p className="strategy-desc">RSI 30 이하에서 매수 후 기술적 반등 노림</p>
          <button className="strategy-select-btn">선택</button>
        </div>

        <div className="strategy-item">
          <span className="strategy-name">볼린저 밴드 하단 터치</span>
          <p className="strategy-desc">변동성 하단 터치 시 반등 매수 전략</p>
          <button className="strategy-select-btn">선택</button>
        </div>
      </div>

      <div className="strategy-footer">
        <button className="bot-start-btn">자동매매 시작</button>
      </div>
    </aside>
  );
}