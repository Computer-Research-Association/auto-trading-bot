import { useEffect, useMemo, useState } from "react";
import "./ProfitLoss.css";
import Loading from "../Common/Loading";

type Period = "30d" | "90d" | "1y" | "all";

type PerfSummary = {
  period_label: string;
  pnl_krw: number;
  pnl_rate: number;
  start_assets_krw: number;
  end_assets_krw: number;
};

type PerfChartPoint = {
  date: string;        // YYYY-MM-DD
  pnl_krw: number;     // 누적 손익
  assets_krw: number;  // 자산가치
};

type PerfDailyRow = {
  date: string;
  pnl_krw: number;
  pnl_rate: number;
  assets_krw: number;
};

type PerfResponse = {
  summary: PerfSummary;
  chart: PerfChartPoint[];
  daily: PerfDailyRow[];
};

function formatKRW(v: number) {
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
    maximumFractionDigits: 0,
  }).format(v);
}
function formatPercent(v: number) {
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

// 아주 단순한 SVG 라인 차트 (나중에 recharts로 교체 가능)
function LineChart({
  points,
  mode,
}: {
  points: PerfChartPoint[];
  mode: "pnl" | "assets";
}) {
  const w = 720;
  const h = 220;
  const pad = 18;

  const ys = points.map((p) => (mode === "pnl" ? p.pnl_krw : p.assets_krw));
  const minY = Math.min(...ys, 0);
  const maxY = Math.max(...ys, 0);

  const xStep = points.length <= 1 ? 0 : (w - pad * 2) / (points.length - 1);
  const yScale = (val: number) => {
    if (maxY === minY) return h / 2;
    const t = (val - minY) / (maxY - minY);
    return h - pad - t * (h - pad * 2);
  };

  const d = points
    .map((p, i) => {
      const x = pad + i * xStep;
      const y = yScale(mode === "pnl" ? p.pnl_krw : p.assets_krw);
      return `${i === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} className="perf-chart">
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

export default function Performance() {
  const [period, setPeriod] = useState<Period>("30d");
  const [mode, setMode] = useState<"pnl" | "assets">("pnl");
  const [data, setData] = useState<PerfResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    setData(null);

    fetch(`http://127.0.0.1:8000/api/performance/summary?period=${period}`)
      .then(async (r) => {
        if (!r.ok) throw new Error((await r.text()) || `HTTP ${r.status}`);
        return r.json() as Promise<PerfResponse>;
      })
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)));
  }, [period]);

  const summary = data?.summary;
  const chart = data?.chart ?? [];
  const daily = data?.daily ?? [];

  const pnlPositive = (summary?.pnl_krw ?? 0) >= 0;

  const periodButtons: { key: Period; label: string }[] = [
    { key: "30d", label: "30일" },
    { key: "90d", label: "3개월" },
    { key: "1y", label: "1년" },
    { key: "all", label: "전체" },
  ];

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <Loading />;

  return (
    <div className="main-panel">
      {/* 상단 요약 */}
      <div className="perf-top">
        <div className="perf-hero">
          <div className="perf-hero-title">투자손익</div>
          <div className={`perf-hero-value ${pnlPositive ? "pos" : "neg"}`}>
            {formatKRW(summary!.pnl_krw)}
          </div>
          <div className={`perf-hero-sub ${pnlPositive ? "pos" : "neg"}`}>
            {formatPercent(summary!.pnl_rate)}
            <span className="perf-hero-period"> · {summary!.period_label}</span>
          </div>
        </div>

        <div className="perf-filters">
          <div className="perf-seg">
            {periodButtons.map((b) => (
              <button
                key={b.key}
                className={`seg-btn ${period === b.key ? "active" : ""}`}
                onClick={() => setPeriod(b.key)}
              >
                {b.label}
              </button>
            ))}
          </div>

          <div className="perf-seg">
            <button
              className={`seg-btn ${mode === "pnl" ? "active" : ""}`}
              onClick={() => setMode("pnl")}
            >
              누적손익
            </button>
            <button
              className={`seg-btn ${mode === "assets" ? "active" : ""}`}
              onClick={() => setMode("assets")}
            >
              자산가치
            </button>
          </div>
        </div>
      </div>

      {/* 차트 */}
      <div className="perf-card">
        <div className="perf-card-head">
          <div className="perf-card-title">
            {mode === "pnl" ? "누적 손익 추이" : "자산가치 추이"}
          </div>
          <div className="perf-card-meta">
            시작 {formatKRW(summary!.start_assets_krw)} → 현재{" "}
            {formatKRW(summary!.end_assets_krw)}
          </div>
        </div>

        <LineChart points={chart} mode={mode} />
      </div>

      {/* 일별 테이블 */}
      <div className="perf-card">
        <div className="perf-card-head">
          <div className="perf-card-title">일별 손익</div>
        </div>

        {daily.length === 0 ? (
          <div className="perf-empty">표시할 데이터가 없습니다.</div>
        ) : (
          <div className="perf-table-wrap">
            <table className="perf-table">
              <thead>
                <tr>
                  <th className="left">날짜</th>
                  <th className="right">손익</th>
                  <th className="right">수익률</th>
                  <th className="right">자산가치</th>
                </tr>
              </thead>
              <tbody>
                {daily.map((r) => {
                  const pos = r.pnl_krw >= 0;
                  return (
                    <tr key={r.date}>
                      <td className="left">{r.date}</td>
                      <td className={`right ${pos ? "pos" : "neg"}`}>
                        {formatKRW(r.pnl_krw)}
                      </td>
                      <td className={`right ${pos ? "pos" : "neg"}`}>
                        {formatPercent(r.pnl_rate)}
                      </td>
                      <td className="right">{formatKRW(r.assets_krw)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
