import { useEffect, useState } from "react";
import "./Asset.css";
import Loading from "../Common/Loading";
import { mockAssets } from "../../mocks/mockAssets";
import { 
  PieChart, 
  Pie, 
  ResponsiveContainer, 
  Tooltip, 
  Legend,
  Cell // Cell은 import만 하고 사용하지 않음 (Recharts 4.0 호환)
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
  fullName: string;
  value: number;
  pct: number;
  fill?: string;
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

// 심볼 -> 풀네임 매핑 (예시)
const FULL_NAMES: Record<string, string> = {
  BTC: "Bitcoin",
  ETH: "Ethereum",
  SOL: "Solana",
  XRP: "Ripple",
  KRW: "Won",
};

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
      fullName: "Won",
      value: krwValue,
      pct: safeDiv(krwValue, total) * 100,
    },
    ...items.map((it) => ({
      name: it.symbol,
      fullName: FULL_NAMES[it.symbol] || it.symbol,
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
// 이미지와 유사한 노랑/빨강/주황/라임 계열 색상
const COLORS = ["#EAB308", "#EF4444", "#F97316", "#84CC16", "#3B82F6"]; 

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
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    // Mock 데이터 로드
    setData(mockAssets);
  }, []);

  if (err) return <div className="main-panel">에러: {err}</div>;
  if (!data) return <Loading />;

  const { summary, items } = data;
  
  // 차트 데이터 (색상 주입)
  const ratioRaw = buildRatio(summary, items).length > 0
    ? buildRatio(summary, items)
    : [{ name: "KRW", fullName: "Won", value: summary.krw_total, pct: 100 }];

  const ratio = ratioRaw.map((item, index) => ({
    ...item,
    fill: COLORS[index % COLORS.length]
  }));

  // 필터링된 리스트
  const filteredItems = items.filter(item => 
    item.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="main-panel">
      
      {/* 상단 2단 그리드 */}
      <div className="assets-top-grid">
        
        {/* 1. 자산 요약 (좌측) */}
        <div className="asset-summary-section">
          {/* 총 보유자산 (Hero) - Row 1 */}
          <div className="summary-card hero">
            <div className="card-label">총 보유자산</div>
            <div className="hero-row">
              <span className="card-value-hero">
                {formatKRW(summary.total_assets_krw)}
              </span>
              <span className={`hero-pct ${summary.total_pnl_rate >= 0 ? "pos" : "neg"}`}>
                {formatPercent(summary.total_pnl_rate)}
              </span>
            </div>
          </div>

          {/* 3열 그리드 - Row 2 */}
          <div className="summary-row-3">
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
          </div>

          {/* 2열 그리드 - Row 3 */}
          <div className="summary-row-2">
            <div className="summary-card">
              <div className="card-label">평가손익</div>
              <div className={`card-value ${summary.total_pnl_krw >= 0 ? "pos" : "neg"}`}>
                {summary.total_pnl_krw > 0 ? "+" : ""}{formatKRW(summary.total_pnl_krw)}
              </div>
            </div>
            <div className="summary-card">
              <div className="card-label">수익률</div>
              <div className={`card-value ${summary.total_pnl_rate >= 0 ? "pos" : "neg"}`}>
                {formatPercent(summary.total_pnl_rate)}
              </div>
            </div>
          </div>
        </div>

        {/* 2. 자산 비중 (우측) */}
        <div className="asset-chart-section">
          <div className="chart-header">
            <h2 className="section-title">자산 비중</h2>
            <button className="chart-more-btn">•••</button>
          </div>
          
          <div className="chart-content">
            <div className="chart-wrapper">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={ratio}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}   /* 얇게 */
                    outerRadius={85}
                    paddingAngle={0}   /* 붙이기 */
                    dataKey="value"
                    startAngle={90}
                    endAngle={-270}
                  >
                    {/* 데이터 자체의 fill 속성 사용 (Cell 제거) */}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              
              {/* 도넛 중앙 텍스트 삭제됨 (요청 반영) */}
            </div>

            {/* 커스텀 Legend */}
            <div className="custom-legend-list">
              {ratio.map((item, idx) => (
                <div key={item.name} className="legend-item">
                  <div className="legend-left">
                    <span 
                      className="legend-dot" 
                      style={{ background: item.fill }}
                    />
                    <span className="legend-name">{item.name}</span>
                    <span 
                      className="legend-badge"
                      style={{ 
                        backgroundColor: `${item.fill}15`, // 투명도 15% 적용 (Hex 6자리일 때만 동작, 여기선 동작함)
                        color: item.fill 
                      }}
                    >
                      {item.fullName}
                    </span>
                  </div>
                  <div className="legend-right">
                    <div className="legend-pct">{item.pct.toFixed(1)}%</div>
                    <div className="legend-val">{formatKRW(item.value)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. 보유 자산 테이블 */}
      <div className="assets-table-wrap">
        <div className="table-header-row">
          <h2 className="section-title">보유 자산</h2>
          <div className="assets-search-bar">
            <span className="assets-search-icon">🔍</span>
            <input 
              type="text" 
              placeholder="검색..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        {filteredItems.length === 0 ? (
          <div className="empty-message">검색 결과가 없습니다.</div>
        ) : (
          <table className="asset-table">
            <thead>
              <tr>
                <th style={{ width: 60 }}></th> {/* 아이콘용 */}
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
              {filteredItems.map((item, index) => {
                const pnl = item.evaluation_krw - item.avg_buy_price * item.quantity;
                const pnlRate = item.avg_buy_price > 0
                  ? ((item.current_price - item.avg_buy_price) / item.avg_buy_price) * 100
                  : 0;
                
                // 아이콘 색상 (차트 색상과 매칭하거나 랜덤)
                const iconColor = COLORS[index % COLORS.length];

                return (
                  <tr key={item.symbol}>
                    <td className="icon-cell">
                      <div className="coin-icon-placeholder" style={{ background: `${iconColor}20`, color: iconColor }}>
                        {item.symbol[0]}
                      </div>
                    </td>
                    <td>
                      <div className="symbol-wrap">
                        <div className="symbol-name">{item.symbol}</div>
                        <div className="symbol-full">{FULL_NAMES[item.symbol] || item.symbol}</div>
                      </div>
                    </td>
                    <td className="right">{item.quantity.toLocaleString()}</td>
                    <td className="right">{formatKRW(item.avg_buy_price)}</td>
                    <td className="right">{formatKRW(item.current_price)}</td>
                    <td className="right bold">{formatKRW(item.evaluation_krw)}</td>
                    <td className={`right bold ${pnl >= 0 ? "pos" : "neg"}`}>
                      {pnl > 0 ? "+" : ""}{formatKRW(pnl)}
                    </td>
                    <td className={`right bold ${pnlRate >= 0 ? "pos" : "neg"}`}>
                      {formatPercent(pnlRate)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        
        <div className="table-footer">
          <button className="expand-btn">전체 자산 상세 보기 ⌄</button>
        </div>
      </div>
    </div>
  );
}
