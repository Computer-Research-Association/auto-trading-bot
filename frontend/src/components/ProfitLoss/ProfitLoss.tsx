import { useEffect, useMemo, useState } from "react";
import "./ProfitLoss.css";
import Loading from "../Common/Loading";
import { apiFetch } from "../../Lib/api";
import { getPerformance, type PerfResponse, type PerfChartPoint } from "../../Lib/performance.api"; // API & Types
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

type Period = "30d" | "180d" | "1y" | "all";

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
    setErr(null);

    // 1. 현재 날짜 구하기 (?? "" 를 붙여서 에러 방지)
    const now = new Date();
    const endDateStr: string = now.toISOString().split('T')[0] ?? "";

    // 2. 시작 날짜 계산 함수 (반환 타입 명시 및 ?? "" 적용)
    const getStartDate = (p: string): string => {
      const d = new Date();
      if (p === "30d") d.setDate(d.getDate() - 30);
      else if (p === "180d") d.setMonth(d.getMonth() - 6);
      else if (p === "1y") d.setFullYear(d.getFullYear() - 1);
      else return "2020-01-01";
      return d.toISOString().split('T')[0] ?? "";
    };

    const startDateStr: string = getStartDate(period);

    // 3. API 파라미터 설정
    const params = new URLSearchParams({
      start_date: startDateStr,
      end_date: endDateStr,
      period: period,
    });

    // 4. 서버 데이터 호출 (res 타입 명시로 any 에러 해결)
    apiFetch<PerfResponse>("/performance/summary?" + params.toString())
      .then((res: PerfResponse) => {
        setData(res); // 서버에서 온 데이터를 바로 저장 (필터링은 서버가 이미 해서 보냄)
      })
      .catch((e: unknown) => {
        setErr(e instanceof Error ? e.message : String(e));
      });
  }, [period]);


  const summary = data?.summary;
  const chart = data?.chart ?? [];
  const daily = data?.daily ?? [];

  const pnlPositive = (summary?.pnl_krw ?? 0) >= 0;

  const periodButtons: { key: Period; label: string }[] = [
    { key: "30d", label: "30일" },
    { key: "180d", label: "6개월" },
    { key: "1y", label: "1년" },
    { key: "all", label: "전체" },
  ];

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <Loading />;


  const gradientOffset = () => {
    if (chart.length === 0) return 0;
    const dataMax = Math.max(...chart.map((i) => i.pnl_krw));
    const dataMin = Math.min(...chart.map((i) => i.pnl_krw));

    if (dataMax <= 0) return 0;
    if (dataMin >= 0) return 1;

    return dataMax / (dataMax - dataMin);
  };

  const off = gradientOffset();

  return (
    <div className="main-panel">
      {/* 👇 상단 3개 KPI 카드 */}
      <div className="kpi-cards">
        <div className="kpi-card">
          <div className="kpi-label">누적손익</div>
          <div className={`kpi-value-large ${summary!.pnl_krw >= 0 ? "pos" : "neg"}`}>
            {formatKRW(summary!.pnl_krw)}
          </div>
          <div className="kpi-sub">
            <span className={summary!.pnl_krw >= 0 ? "pos" : "neg"}>
              {summary!.pnl_krw >= 0 ? "↗" : "↘"} {summary!.pnl_rate.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">금일 변동</div>
          <div className={`kpi-value-large ${(summary?.today_change_krw ?? 0) >= 0 ? "pos" : "neg"}`}>
            {formatKRW(summary?.today_change_krw ?? 0)}
          </div>
          <div className="kpi-sub kpi-sub-col">
            <span className={((summary?.today_change_krw ?? 0) >= 0) ? "pos" : "neg"}>
              {(summary?.today_change_krw ?? 0) >= 0 ? "↗" : "↘"} {(summary?.today_change_rate ?? 0).toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">누적 수익률</div>
          <div className={`kpi-value-large ${summary!.pnl_rate >= 0 ? "pos" : "neg"}`}>
            {formatPercent(summary!.pnl_rate)}
          </div>
          <div className="kpi-sub">
            <span className="kpi-period">지난 달 이후</span>
          </div>
        </div>
      </div>

      {/* 👇 차트 섹션 */}
      <div className="perf-section">
        <div className="section-header">
          <h2>손익 성과</h2>
          <div className="chart-legend">
            <div className="legend-item-row">
              <div className="legend-dot gain"></div> <span className="legend-text">이익구간</span>
            </div>
            <div className="legend-item-row">
              <div className="legend-dot loss"></div> <span className="legend-text">손실구간</span>
            </div>
          </div>
        </div>

        <div className="period-tabs">
          {periodButtons.map((b) => (
            <button
              key={b.key}
              className={`period-tab ${period === b.key ? "active" : ""}`}
              onClick={() => setPeriod(b.key)}
            >
              {b.label}
            </button>
          ))}
        </div>

        {/* 👇 Recharts로 차트 그리기 */}
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chart}>
            <defs>
              <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                <stop offset={off} stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset={off} stopColor="#3b82f6" stopOpacity={0.3} />
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
              stroke="#8884d8"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#splitColor)"
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
