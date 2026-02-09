import { useEffect, useState } from "react";
import "./Asset.css";
import Loading from "../Common/Loading";
import { apiFetch } from "../../Lib/apiFetch";
import type { PortfolioAssetsResponse } from "./types";
import { mockAssets } from "../../mocks/mockData";
// import axios from "axios";

/* =======================
   Types
======================= */
type AssetItem = {
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  evaluation_krw: number;
};

type PortfolioSummary = {
  krw_total: number;
  krw_available: number;
  total_buy_krw: number;
  total_assets_krw: number;
  total_pnl_krw: number;
  total_pnl_rate: number;
};

type PortfolioAssetsResponse = {
  summary: PortfolioSummary;
  items: AssetItem[];
};

type RatioItem = {
  symbol: string;
  value_krw: number;
  pct: number;
};

/* =======================
   Utils
======================= */
function formatKRW(value: number): string {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function safeDiv(n: number, d: number): number {
  if (!isFinite(n) || !isFinite(d) || d === 0) return 0;
  return n / d;
}

/* =======================
   Donut Chart
======================= */
const ASSET_COLORS = [
  "#f7d54e",
  "#ef4444",
  "#d4af37",
  "#ed6c02",
  "#64748b",
];

function DonutChart({ ratio }: { ratio: RatioItem[] }) {
  // ✅ 1) ratio가 없거나 비면 차트 대신 안내 문구
  if (!Array.isArray(ratio) || ratio.length === 0) {
    return (
      <div className="donut-card">
        <h2 className="asset-title">자산 비중</h2>
        <div style={{ padding: "40px", textAlign: "center", color: "#888" }}>
          자산 비중 데이터 없음
        </div>
      </div>
    );
  }

  // ✅ 2) pct가 NaN/undefined여도 안전하게 누적
  let acc = 0;
  const stops = ratio.map((r, idx) => {
    const start = acc;

    const safePct = Number.isFinite(r.pct) ? r.pct : 0;
    acc += safePct;

    const color = ASSET_COLORS[idx % ASSET_COLORS.length];
    return `${color} ${start}% ${acc}%`;
  });

  return (
    <div className="donut-card">
      <h2 className="asset-title">자산 비중</h2>

      <div className="donut-wrap">
        <div
          className="donut"
          style={{ background: `conic-gradient(${stops.join(",")})` }}
        />

        <div className="donut-legend">
          {ratio.map((r, idx) => (
            <div key={`${r.symbol}-${idx}`} className="legend-row">
              <span
                className="legend-dot"
                style={{ background: ASSET_COLORS[idx % ASSET_COLORS.length] }}
              />
              <span className="legend-name">{r.symbol}</span>

              {/* ✅ 3) toFixed도 안전하게 */}
              <span className="legend-pct">
                {Number.isFinite(r.pct) ? r.pct.toFixed(1) : "0.0"}%
              </span>

              <span className="legend-val">{formatKRW(r.value_krw)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


/* =======================
   Main Component
======================= */

export default function Assets() {
  // 1️⃣ 모든 Hook은 최상단
  const [data, setData] = useState<PortfolioAssetsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [assetRatio, setAssetRatio] = useState<RatioItem[]>([]);
  const [loading, setLoading] = useState(true);

  // 2️⃣ useEffect도 무조건 위
  useEffect(() => {
    setLoading(true);

    apiFetch<PortfolioAssetsResponse>("/api/portfolio/assets")
      .then(setData)
      .catch(() => {
        // fallback mock
        setData(mockAssets);
      })
      .finally(() => setLoading(false));
  }, []);

  // 3️⃣ 여기서부터 조건 분기 (이 아래에는 Hook ❌)
  if (loading) {
    return <Loading />;
  }

  if (err) {
    return <div>에러 발생: {err}</div>;
  }

  if (!data) {
    return null;
  }


  // 🔹 도넛 차트용 JSON fetch (여기만 바뀐 부분)
  useEffect(() => {
    fetch("/JSON/assetRatio.json")
      .then((res) => res.json())
      .then((rows) => {
        const normalized: RatioItem[] = rows.map((r: any) => ({
          symbol: r.currency,
          value_krw: r.value,
          pct: r.percent,
        }));
        setAssetRatio(normalized);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <Loading />;

  const { summary, items } = data;

  return (

  <div className="asset-summary-grid">
  <div className="asset-card">
    <span>총 보유자산</span>
    <strong>{formatKRW(summary.total_assets_krw)}</strong>
  </div>

  <div className="asset-card">
    <span>보유 KRW</span>
    <strong>{formatKRW(summary.krw_total)}</strong>
  </div>

  <div className="asset-card">
    <span>주문 가능</span>
    <strong>{formatKRW(summary.krw_available)}</strong>
  </div>

  <div className="asset-card">
    <span>총 매수금액</span>
    <strong>{formatKRW(summary.total_buy_krw)}</strong>
  </div>

  <div className="asset-card">
    <span>평가손익</span>
    <strong
      className={summary.total_pnl_krw >= 0 ? "pnl-plus" : "pnl-minus"}
    >
      {formatKRW(summary.total_pnl_krw)}
    </strong>
    <small>{formatPercent(summary.total_pnl_rate)}</small>


         {/* 자산 비중 (JSON 기반) */}
          <DonutChart ratio={assetRatio} />
          </div>
        </div>
      );
}
