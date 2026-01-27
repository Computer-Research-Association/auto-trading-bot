import { useEffect, useState } from "react";
import "./Asset.css";

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

function buildRatio(
  summary: PortfolioSummary,
  items: AssetItem[]
): RatioItem[] {
  const total = Math.max(0, summary.total_assets_krw);

  const coinSum = items.reduce(
    (acc, it) => acc + Math.max(0, it.evaluation_krw),
    0
  );

  const krwValue = Math.max(0, total - coinSum);

  const rows: RatioItem[] = [
    {
      symbol: "KRW",
      value_krw: krwValue,
      pct: safeDiv(krwValue, total) * 100,
    },
    ...items.map((it) => ({
      symbol: it.symbol,
      value_krw: Math.max(0, it.evaluation_krw),
      pct: safeDiv(Math.max(0, it.evaluation_krw), total) * 100,
    })),
  ];

  return rows
    .filter((r) => r.value_krw > 0)
    .sort((a, b) => b.value_krw - a.value_krw);
}

/* =======================
   Donut Chart
======================= */
function DonutChart({ ratio }: { ratio: RatioItem[] }) {
  let acc = 0;
  const stops = ratio.map((r, idx) => {
    const start = acc;
    acc += r.pct;
    return `hsl(${(idx * 55) % 360} 70% 55%) ${start}% ${acc}%`;
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
            <div key={r.symbol} className="legend-row">
              <span
                className="legend-dot"
                style={{
                  background: `hsl(${(idx * 55) % 360} 70% 55%)`,
                }}
              />
              <span className="legend-name">{r.symbol}</span>
              <span className="legend-pct">{r.pct.toFixed(1)}%</span>
              <span className="legend-val">
                {formatKRW(r.value_krw)}
              </span>
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
  const [data, setData] = useState<PortfolioAssetsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/portfolio/assets")
      .then(async (r) => {
        if (!r.ok) {
          const text = await r.text();
          throw new Error(text || `HTTP ${r.status}`);
        }
        return r.json() as Promise<PortfolioAssetsResponse>;
      })
      .then(setData)
      .catch((e: unknown) =>
        setErr(e instanceof Error ? e.message : String(e))
      );
  }, []);

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <div className="main-panel">로딩중...</div>;

  const { summary, items } = data;
  const ratio =
    buildRatio(summary, items).length > 0
      ? buildRatio(summary, items)
      : [{ symbol: "KRW", value_krw: summary.krw_total, pct: 100 }];

  return (
    <div className="main-panel">
      {/* 상단 영역 */}
      <div className="assets-top-row">
        {/* 자산 요약 */}
        <div className="asset-summary-card">
          <h2 className="asset-title">자산 요약</h2>

          <div className="asset-total">
            <div className="asset-total-label">총 보유자산</div>
            <div className="asset-total-value">
              {formatKRW(summary.total_assets_krw)}
            </div>
          </div>

          <div className="asset-kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">보유 KRW</div>
              <div className="kpi-value neutral">
                {formatKRW(summary.krw_total)}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">주문가능</div>
              <div className="kpi-value neutral">
                {formatKRW(summary.krw_available)}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">총 매수금액</div>
              <div className="kpi-value neutral">
                {formatKRW(summary.total_buy_krw)}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">평가손익</div>
              <div
                className={`kpi-value ${
                  summary.total_pnl_krw >= 0 ? "positive" : "negative"
                }`}
              >
                {formatKRW(summary.total_pnl_krw)}
              </div>
            </div>

            <div className="kpi-card">
              <div className="kpi-label">수익률</div>
              <div
                className={`kpi-value ${
                  summary.total_pnl_rate >= 0 ? "positive" : "negative"
                }`}
              >
                {formatPercent(summary.total_pnl_rate)}
              </div>
            </div>
          </div>
        </div>

        {/* 자산 비중 */}
        <DonutChart ratio={ratio} />
      </div>

      {/* 보유 자산 테이블 */}
      <div className="assets-table-wrap">
        <h2 className="asset-title" style={{ marginBottom: "16px" }}>
          보유 자산
        </h2>

        {items.length === 0 ? (
          <div className="asset-empty">
            보유 중인 자산이 없습니다.
          </div>
        ) : (
          <div
            style={{
              background: "#ffffff",
              borderRadius: "12px",
              border: "1px solid #eef0f6",
              overflow: "hidden",
            }}
          >
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f7f8fb" }}>
                    <th className="col-left">종목</th>
                    <th className="col-right">보유수량</th>
                    <th className="col-right">평균매수가</th>
                    <th className="col-right">현재가</th>
                    <th className="col-right">평가금액</th>
                    <th className="col-right">손익</th>
                    <th className="col-right">수익률</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const pnl =
                    item.evaluation_krw -
                    item.avg_buy_price * item.quantity;
                  const pnlRate =
                    item.avg_buy_price > 0
                      ? ((item.current_price - item.avg_buy_price) /
                          item.avg_buy_price) *
                        100
                      : 0;

                  return (
                    <tr key={item.symbol}>
                      <td>{item.symbol}</td>
                      <td>{item.quantity.toLocaleString()}</td>
                      <td>{formatKRW(item.avg_buy_price)}</td>
                      <td>{formatKRW(item.current_price)}</td>
                      <td>{formatKRW(item.evaluation_krw)}</td>
                      <td
                        style={{
                          color: pnl >= 0 ? "#16a34a" : "#ef4444",
                        }}
                      >
                        {formatKRW(pnl)}
                      </td>
                      <td
                        style={{
                          color: pnlRate >= 0 ? "#16a34a" : "#ef4444",
                        }}
                      >
                        {formatPercent(pnlRate)}
                      </td>
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
