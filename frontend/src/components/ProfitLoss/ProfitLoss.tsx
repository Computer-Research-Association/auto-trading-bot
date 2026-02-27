import { useEffect, useMemo, useState } from "react";
import "./ProfitLoss.css";
import Loading from "../Common/Loading";
import { apiFetch } from "../../Lib/api";
import {
  getPerformance,
  type PerfResponse,
  type PerfChartPoint,
} from "../../Lib/performance.api"; // API & Types
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { getAssets } from "../../Lib/assets.api";

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

export default function Performance() {
  const [period, setPeriod] = useState<Period>("30d");
  const [data, setData] = useState<PerfResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  // 실시간 패치가 1회 이상 완료돼야 차트를 보여줌 → summary API와 realtime fetch간 색상 불일치 깜빡임 방지
  const [realtimeReady, setRealtimeReady] = useState<boolean>(false);

  // 1. 초기 데이터 로드 (기존 로직 유지)
  useEffect(() => {
    setErr(null);
    setLoading(true);

    const now = new Date();
    const endDateStr = now.toISOString().split("T")[0];

    const getStartDate = (p: string) => {
      const d = new Date();
      if (p === "30d") d.setDate(d.getDate() - 30);
      else if (p === "180d") d.setMonth(d.getMonth() - 6);
      else if (p === "1y") d.setFullYear(d.getFullYear() - 1);
      else return "2020-01-01";
      return d.toISOString().split("T")[0];
    };

    const query = `?start_date=${getStartDate(period)}&end_date=${endDateStr}`;

    Promise.all([
      apiFetch<PerfResponse>(`/performance/summary${query}`),
      getAssets()
    ])
      .then(([res, assetsRes]) => {
        const todayStr: string = new Date().toISOString().split("T")[0] ?? "";

        const currentDaily = res.daily;
        const lastRow = currentDaily[currentDaily.length - 1];
        const isToday = lastRow?.date === todayStr;
        const yesterdayRow = isToday ? currentDaily[currentDaily.length - 2] : lastRow;
        const yesterdayAssets = yesterdayRow?.assets_krw ?? res.summary.start_assets_krw ?? 1;

        const newPnlKrw  = assetsRes.summary.total_assets_krw - yesterdayAssets;
        const newPnlRate = yesterdayAssets !== 0 ? (newPnlKrw / yesterdayAssets) * 100 : 0;

        const baseAssets = res.summary.start_assets_krw || 1.0;
        const cumPnlKrw  = assetsRes.summary.total_assets_krw - baseAssets;
        const cumPnlRate = (cumPnlKrw / baseAssets) * 100;

        const newSummary = {
          ...res.summary,
          end_assets_krw: assetsRes.summary.total_assets_krw,
          pnl_krw: cumPnlKrw,
          pnl_rate: cumPnlRate,
        };

        const newPoint = {
          date: todayStr,
          assets_krw: assetsRes.summary.total_assets_krw,
          pnl_krw: cumPnlKrw,
          pnl_rate: cumPnlRate,
        };
        const newChart = [...res.chart];
        const lastChartIdx = newChart.length - 1;
        if (lastChartIdx >= 0 && newChart[lastChartIdx]!.date === todayStr) {
          newChart[lastChartIdx] = newPoint;
        } else {
          newChart.push(newPoint);
        }

        const dailyPoint = {
          date: todayStr,
          assets_krw: assetsRes.summary.total_assets_krw,
          pnl_krw: newPnlKrw,
          pnl_rate: newPnlRate,
        };
        const newDaily = [...res.daily];
        const lastDailyIdx = newDaily.length - 1;
        if (lastDailyIdx >= 0 && newDaily[lastDailyIdx]!.date === todayStr) {
          newDaily[lastDailyIdx] = dailyPoint;
        } else {
          newDaily.push(dailyPoint);
        }

        setData({
          summary: newSummary,
          chart: newChart,
          daily: newDaily,
        });
      })
      .catch((e) => {
        setErr(e instanceof Error ? e.message : "Error");
      })
      .finally(() => setLoading(false));
  }, [period]);

  // 2. 실시간 업데이트 (1초마다)
  useEffect(() => {
    // 실시간 데이터 갱신 로직
    const fetchRealtimeAssets = () => {
      getAssets()
        .then((res) => {
          setData((prev) => {
            if (!prev) return prev;

            const todayStr: string = new Date().toISOString().split("T")[0] ?? "";
            if (!todayStr) return prev;

            // 전날 자산: today 행이 이미 있으면 2번째 마지막 행, 없으면 마지막 행
            const currentDaily = prev.daily;
            const lastRow = currentDaily[currentDaily.length - 1];
            const isToday = lastRow?.date === todayStr;
            const yesterdayRow = isToday
              ? currentDaily[currentDaily.length - 2]
              : lastRow;
            const yesterdayAssets =
              yesterdayRow?.assets_krw ?? prev.summary.start_assets_krw ?? 1;

            // 오늘 pnl = 현재 자산 - 전날 자산
            const newPnlKrw  = res.summary.total_assets_krw - yesterdayAssets;
            const newPnlRate = yesterdayAssets !== 0
              ? (newPnlKrw / yesterdayAssets) * 100
              : 0;

            // 누적 pnl (KPI 카드 및 차트용)
            const baseAssets = prev.summary.start_assets_krw || 1.0;
            const cumPnlKrw  = res.summary.total_assets_krw - baseAssets;
            const cumPnlRate = (cumPnlKrw / baseAssets) * 100;

            const newSummary = {
              ...prev.summary,
              end_assets_krw: res.summary.total_assets_krw,
              pnl_krw: cumPnlKrw,
              pnl_rate: cumPnlRate,
            };

            // 차트: 누적 pnl 포인트 갱신
            const newPoint = {
              date: todayStr,
              assets_krw: res.summary.total_assets_krw,
              pnl_krw: cumPnlKrw,
              pnl_rate: cumPnlRate,
            };
            const newChart = [...prev.chart];
            const lastChartIdx = newChart.length - 1;
            if (lastChartIdx >= 0 && newChart[lastChartIdx]!.date === todayStr) {
              newChart[lastChartIdx] = newPoint;
            } else {
              newChart.push(newPoint);
            }

            // 테이블: 전날 대비 일별 pnl 갱신
            const dailyPoint = {
              date: todayStr,
              assets_krw: res.summary.total_assets_krw,
              pnl_krw: newPnlKrw,
              pnl_rate: newPnlRate,
            };
            const newDaily = [...prev.daily];
            const lastDailyIdx = newDaily.length - 1;
            if (lastDailyIdx >= 0 && newDaily[lastDailyIdx]!.date === todayStr) {
              newDaily[lastDailyIdx] = dailyPoint;
            } else {
              newDaily.push(dailyPoint);
            }

            return { ...prev, summary: newSummary, chart: newChart, daily: newDaily };
          });
        })
        .then(() => {
          // 첫 번째 실시간 패치가 완료됐을 때만 차트를 표시 허용
          setRealtimeReady(true);
        })
        .catch(console.error); // 에러 무시 (다음 틱에 재시도)
    };

    // 1) 탭을 열자마자 1초를 기다리지 않고 즉시 1회 실행
    fetchRealtimeAssets();

    // 2) 그 후부터 1초마다 반복 실행
    const timer = setInterval(fetchRealtimeAssets, 1000);

    return () => clearInterval(timer);
  }, []);

  const summary = data?.summary;
  const chart = data?.chart ?? [];
  const daily = data?.daily ?? [];

  // today_change 계산: daily 데이터에서 마지막 2일 데이터 비교
  let today_change_krw = 0;
  let today_change_rate = 0;
  if (daily.length >= 2) {
    const today = daily[daily.length - 1];
    const yesterday = daily[daily.length - 2];
    if (today && yesterday) {
      today_change_krw = today.assets_krw - yesterday.assets_krw;
      today_change_rate = yesterday.assets_krw !== 0 
        ? (today_change_krw / yesterday.assets_krw) * 100 
        : 0;
    }
  } else if (daily.length === 1 && summary) {
    // 요약 정보만 있거나 하루 데이터만 있을 때 오늘의 변동분 계산을 pnl 통일
    today_change_krw = summary.pnl_krw ?? 0;
    today_change_rate = summary.pnl_rate ?? 0;
  }

  // 🎯 차트 색상 결정: 현재 차트 배열의 마지막 데이터의 pnl_krw 기준
  const pnlPositive = chart.length > 0 
    ? (chart[chart.length - 1]?.pnl_krw ?? 0) >= 0 
    : (summary?.pnl_krw ?? 0) >= 0;

  const periodButtons: { key: Period; label: string }[] = [
    { key: "30d", label: "30일" },
    { key: "180d", label: "6개월" },
    { key: "1y", label: "1년" },
    { key: "all", label: "전체" },
  ];

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <div className="main-panel" />; // 로딩 스피너 대신 빈 패널을 반환 (깜빡임 최소화)

  const gradientOffset = () => {
    if (!Array.isArray(chart) || chart.length === 0) return 0;
    const dataMax = Math.max(...chart.map((i) => i.pnl_krw ?? 0));
    const dataMin = Math.min(...chart.map((i) => i.pnl_krw ?? 0));
    if (dataMax <= 0) return 0;
    if (dataMin >= 0) return 1;
    return dataMax / (dataMax - dataMin);
  };

  const off = gradientOffset();

  return (
    <div className="main-panel">
      {/* 👇 상단 3개 KPI 카드 */}
      <div className="kpi-cards">
        {/* 1. 누적손익 카드 부분 */}
        <div className="kpi-card">
          <div className="kpi-label">누적손익</div>
          {/* summary! 를 summary? 로 바꾸고 뒤에 ?? 0 추가 */}
          <div
            className={`kpi-value-large ${(summary?.pnl_krw ?? 0) >= 0 ? "pos" : "neg"}`}
          >
            {formatKRW(summary?.pnl_krw ?? 0)}
          </div>
          <div className="kpi-sub">
            <span className={(summary?.pnl_krw ?? 0) >= 0 ? "pos" : "neg"}>
              {(summary?.pnl_krw ?? 0) >= 0 ? "↗" : "↘"}{" "}
              {(summary?.pnl_rate ?? 0).toFixed(2)}%
            </span>
          </div>
        </div>
        {/* 2. 금일 변동 카드 부분 */}
        <div className="kpi-card">
          <div className="kpi-label">금일 변동</div>
          <div
            className={`kpi-value-large ${today_change_krw >= 0 ? "pos" : "neg"}`}
          >
            {formatKRW(today_change_krw)}
          </div>
          <div className="kpi-sub kpi-sub-col">
            <span
              className={today_change_krw >= 0 ? "pos" : "neg"}
            >
              {today_change_krw >= 0 ? "↗" : "↘"}{" "}
              {today_change_rate.toFixed(2)}%
            </span>
          </div>
        </div>
        {/* 3. 누적 수익률 카드 부분 */}
        <div className="kpi-card">
          <div className="kpi-label">누적 수익률</div>
          <div
            className={`kpi-value-large ${(summary?.pnl_rate ?? 0) >= 0 ? "pos" : "neg"}`}
          >
            {formatPercent(summary?.pnl_rate ?? 0)}
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
              <div className="legend-dot gain"></div>{" "}
              <span className="legend-text">이익구간</span>
            </div>
            <div className="legend-item-row">
              <div className="legend-dot loss"></div>{" "}
              <span className="legend-text">손실구간</span>
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
        <ResponsiveContainer
          width="100%"
          height={300}
          style={{ outline: "none" }}
        >
          <AreaChart data={chart} style={{ outline: "none" }}>
            <defs>
              <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
                <stop offset={0} stopColor="#ef4444" stopOpacity={0.8} />
                <stop offset={off} stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset={off} stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset={1} stopColor="#3b82f6" stopOpacity={0.8} />
              </linearGradient>
              <linearGradient id="splitColorStroke" x1="0" y1="0" x2="0" y2="1">
                <stop offset={0} stopColor="#ef4444" stopOpacity={1} />
                <stop offset={off} stopColor="#ef4444" stopOpacity={1} />
                <stop offset={off} stopColor="#3b82f6" stopOpacity={1} />
                <stop offset={1} stopColor="#3b82f6" stopOpacity={1} />
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
            <ReferenceLine y={0} stroke="#999" strokeDasharray="3 3" />
            <Area
              type="monotone"
              dataKey="pnl_krw"
              stroke="url(#splitColorStroke)"
              strokeWidth={2}
              fill="url(#splitColor)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
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
                      <td className={`left ${pos ? "pos" : "neg"}`}>
                        {formatKRW(r.pnl_krw)}
                      </td>
                      <td className={`left ${pos ? "pos" : "neg"}`}>
                        {formatPercent(r.pnl_rate)}
                      </td>
                      <td className="left">{formatKRW(r.assets_krw)}</td>
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
