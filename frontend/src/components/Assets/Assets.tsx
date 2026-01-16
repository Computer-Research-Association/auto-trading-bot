import React from "react";
import "./Asset.css";


export default function Assets() {
  return (
    <div className="main-panel">
      <section className="asset-summary-card">
        <h3 className="asset-title">자산 요약</h3>

        <div className="asset-total">
          <div className="asset-total-label">총 보유자산</div>
          <div className="asset-total-value">0원</div>
        </div>

        <div className="asset-kpi-grid">
          <KPI label="보유 KRW" value="0원" />
          <KPI label="주문가능" value="0원" />
          <KPI label="총 매수" value="0원" />
          <KPI label="평가손익" value="0원" tone="neutral" />
          <KPI label="평가수익률" value="0%" tone="neutral" />
        </div>
      </section>

      <div className="assets-content">
        <h3>보유자산 내역</h3>
        <div className="panel-placeholder">보유자산 데이터가 없습니다.</div>
      </div>
    </div>
  );
}

type KPIProps = {
  label: string;
  value: string;
  tone?: "positive" | "negative" | "neutral";
};

function KPI({ label, value, tone = "neutral" }: KPIProps) {
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${tone}`}>{value}</div>
    </div>
  );

axios.get("/api/upbit/assets")
}