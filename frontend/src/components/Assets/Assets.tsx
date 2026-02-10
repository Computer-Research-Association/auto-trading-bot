import { useEffect, useState } from "react";
import "./Asset.css";
import Loading from "../Common/Loading";
import { mockAssets } from "../../mocks/mockAssets";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip, 
  Legend 
} from "recharts";

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
  name: string;
  value: number;
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
      name: "KRW",
      value: krwValue,
      pct: safeDiv(krwValue, total) * 100,
    },
    ...items.map((it) => ({
      name: it.symbol,
      value: Math.max(0, it.evaluation_krw),
      pct: safeDiv(Math.max(0, it.evaluation_krw), total) * 100,
    })),
  ];

  return rows
    .filter((r) => r.value > 0)
    .sort((a, b) => b.value - a.value);
}

/* =======================
   Chart Settings
======================= */
const COLORS = ["#FBBF24", "#EF4444", "#3B82F6", "#9CA3AF"]; // 노랑, 빨강, 파랑, 회색

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <div className="tooltip-label">{data.name}</div>
        <div className="tooltip-value">{formatKRW(data.value)}</div>
        <div className="tooltip-pct">({data.pct.toFixed(1)}%)</div>
      </div>
    );
  }
  return null;
};

/* =======================
   Main Component
======================= */
export default function Assets() {
  const [data, setData] = useState<PortfolioAssetsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    // Mock 데이터 로드
    setData(mockAssets);
  }, []);

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <Loading />;

  const { summary, items } = data;
  
  // 데이터 가공 및 색상 주입
  const ratioRaw = buildRatio(summary, items).length > 0
    ? buildRatio(summary, items)
    : [{ name: "KRW", value: summary.krw_total, pct: 100 }];

  // Recharts 4.0 호환을 위해 데이터에 직접 fill 속성 주입
  const ratio = ratioRaw.map((item, index) => ({
    ...item,
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <div className="main-panel">
      {/* 상단 2단 레이아웃 (요약 / 차트) */}
      <div className="assets-top-grid">
        
        {/* 1. 자산 요약 섹션 */}
        <div className="asset-summary-section">
          {/* ... (생략) ... */}
          <h2 className="section-title">자산 요약</h2>
          
          <div className="summary-grid">
            {/* 총 보유자산 (Hero) */}
            <div className="summary-card hero">
              <div className="card-label">총 보유자산</div>
              <div className="card-value-hero">
                {formatKRW(summary.total_assets_krw)}
              </div>
            </div>

            {/* 나머지 카드들 */}
            <div className="summary-card">
              <div className="card-label">보유 KRW</div>
              <div className="card-value">{formatKRW(summary.krw_total)}</div>
            </div>

            <div className="summary-card">
              <div className="card-label">주문가능</div>
              <div className="card-value">{formatKRW(summary.krw_available)}</div>
            </div>

            <div className="summary-card">
              <div className="card-label">총 매수금액</div>
              <div className="card-value">{formatKRW(summary.total_buy_krw)}</div>
            </div>

            <div className="summary-card">
              <div className="card-label">평가손익</div>
              <div className={`card-value ${summary.total_pnl_krw >= 0 ? "pos" : "neg"}`}>
                {formatKRW(summary.total_pnl_krw)}
              </div>
            </div>

            {/* 수익률 (독립) */}
            <div className="summary-card">
              <div className="card-label">수익률</div>
              <div className={`card-value ${summary.total_pnl_rate >= 0 ? "pos" : "neg"}`}>
                {formatPercent(summary.total_pnl_rate)}
              </div>
            </div>
          </div>
        </div>

        {/* 2. 자산 비중 차트 섹션 */}
        <div className="asset-chart-section">
          <h2 className="section-title">자산 비중</h2>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={ratio}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {/* Cell 컴포넌트 제거됨 (데이터 자체의 fill 속성 사용) */}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  layout="vertical" 
                  verticalAlign="middle" 
                  align="right"
                  formatter={(value, entry: any) => {
                    // entry.payload에 전체 데이터 객체가 들어있음
                    const item = entry.payload; 
                    return (
                      <span className="legend-text">
                        <span className="legend-name">{item.name}</span>
                        <span className="legend-percent">{item.pct.toFixed(1)}%</span>
                        <span className="legend-money">{formatKRW(item.value)}</span>
                      </span>
                    );
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 3. 보유 자산 테이블 */}
      <div className="assets-table-section">
        <h2 className="section-title">보유 자산</h2>
        
        {items.length === 0 ? (
          <div className="empty-message">보유 중인 자산이 없습니다.</div>
        ) : (
          <table className="asset-table">
            <thead>
              <tr>
                <th>종목</th>
                <th className="right">보유수량</th>
                <th className="right">평균매수가</th>
                <th className="right">현재가</th>
                <th className="right">평가금액</th>
                <th className="right">손익</th>
                <th className="right">수익률</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const pnl = item.evaluation_krw - item.avg_buy_price * item.quantity;
                const pnlRate = item.avg_buy_price > 0
                  ? ((item.current_price - item.avg_buy_price) / item.avg_buy_price) * 100
                  : 0;

                return (
                  <tr key={item.symbol}>
                    <td className="symbol-cell">{item.symbol}</td>
                    <td className="right">{item.quantity.toLocaleString()}</td>
                    <td className="right">{formatKRW(item.avg_buy_price)}</td>
                    <td className="right">{formatKRW(item.current_price)}</td>
                    <td className="right">{formatKRW(item.evaluation_krw)}</td>
                    <td className={`right ${pnl >= 0 ? "pos" : "neg"}`}>
                      {formatKRW(pnl)}
                    </td>
                    <td className={`right ${pnlRate >= 0 ? "pos" : "neg"}`}>
                      {formatPercent(pnlRate)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
