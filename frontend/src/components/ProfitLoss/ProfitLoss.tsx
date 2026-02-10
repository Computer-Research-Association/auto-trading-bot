import { useEffect, useMemo, useState } from "react";
import "./ProfitLoss.css";
import Loading from "../Common/Loading";
import { mockPerformance, type PerfResponse, type PerfChartPoint, type PerfSummary, type PerfDailyRow } from "../../mocks/mockPerformance";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

type Period = "30d" | "90d" | "1y" | "all";

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
  const w = 800;
  const h = 300;
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
}

export default function Performance() {
  const [period, setPeriod] = useState<Period>("30d");
  const [mode, setMode] = useState<"pnl" | "assets">("pnl");
  const [data, setData] = useState<PerfResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    // Mock 데이터 사용 (서버 구현 전)
    setData(mockPerformance);
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
      {/* 👇 상단 3개 KPI 카드 */}
      <div className="kpi-cards">
        <div className="kpi-card">
          <div className="kpi-label">총 자산</div>
          <div className="kpi-value-large">
            {formatKRW(summary!.total_assets_krw)}
          </div>
          <div className="kpi-sub">
            <span className={summary!.pnl_krw >= 0 ? "pos" : "neg"}>
              {formatKRW(summary!.pnl_krw)} ({summary!.pnl_rate.toFixed(2)}%)
            </span>
            <span className="kpi-period">지난 달 이후</span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">누적손익</div>
          <div className={`kpi-value-large ${summary!.pnl_krw >= 0 ? "pos" : "neg"}`}>
            {formatKRW(summary!.pnl_krw)}
          </div>
          <div className="kpi-sub">
            <span className={summary!.pnl_krw >= 0 ? "pos" : "neg"}>
              ↗ {summary!.pnl_rate.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">금일 변동</div>
          <div className={`kpi-value-large ${summary!.today_change_krw >= 0 ? "pos" : "neg"}`}>
            {formatKRW(summary!.today_change_krw)}
          </div>
          <div className="kpi-sub">
            <span className={summary!.today_change_krw >= 0 ? "pos" : "neg"}>
              {summary!.today_change_krw >= 0 ? "↗" : "↘"} {summary!.today_change_rate.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* 👇 차트 섹션 */}
      <div className="perf-section">
        <div className="section-header">
          <h2>손익 성과</h2>
          <div className="chart-legend">
            <span className="legend-gain">● 이익구간</span>
            <span className="legend-loss">● 손실구간</span>
          </div>
        </div>

        <div className="period-tabs">
          {periodButtons.map((b) => (
            <button
              key={b.key}
              className={`period-tab ${period === b.key ? "active" : ""}`}
              onClick={() => setPeriod(b.key)}
            >
              {b.label.toUpperCase()}
            </button>
          ))}
        </div>

        {/* 👇 Recharts로 차트 그리기 */}
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chart}>
            <defs>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => {
                const date = new Date(value);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `₩${(value / 1000000).toFixed(0)}M`}
            />
            <Tooltip 
              formatter={(value) => {
              if (typeof value !== 'number') return '';
              return formatKRW(value);
              }}
              labelFormatter={(label) => `날짜: ${label}`}
            />
            <ReferenceLine y={0} stroke="#999" strokeDasharray="3 3" />
            <Area 
              type="monotone" 
              dataKey="pnl_krw" 
              stroke="#ef4444" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorPnl)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* 👇 Daily Breakdown 테이블 */}
      <div className="perf-section">
        <h2>일일 손익 상세</h2>
        {daily.length === 0 ? (
          <div className="perf-empty">데이터가 없습니다.</div>
        ) : (
          <table className="perf-table">
            <thead>
              <tr>
                <th>날짜</th>
                <th>손익</th>
                <th>수익률</th>
                <th>자산가치</th>
              </tr>
            </thead>
            <tbody>
              {daily.map((r) => (
                <tr key={r.date}>
                  <td>{r.date}</td>
                  <td className={r.pnl_krw >= 0 ? "pos" : "neg"}>
                    {formatKRW(r.pnl_krw)}
                  </td>
                  <td className={r.pnl_rate >= 0 ? "pos" : "neg"}>
                    {formatPercent(r.pnl_rate)}
                  </td>
                  <td>{formatKRW(r.assets_krw)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
