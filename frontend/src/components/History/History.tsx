import React, { useState, useEffect } from 'react';
import './History.css';
import Loading from '../Common/Loading';
import { mockHistory } from '../../mocks/mockHistory';
import { apiFetch } from "../../Lib/api";
import { type History, type Strategy, type HistoryType, type HistoryResponse, getHistory } from "../../Lib/history.api";

// Local types removed (imported from api)

function filterTrades(
  data: History[],
  type: string) {
  return data.filter(item => {
    if (type === 'All') return true;
    return item.Type === type;
  });
}

function formatKRW(val: number) {
  return `${new Intl.NumberFormat('ko-KR').format(val)} KRW`;
}

type Period = '1 MONTH' | '6 MONTH' | '1 YEAR' | 'ALL';
// HistoryType, Strategy imported from api

const periodOptions = [
  { label: '1 MONTH', value: '1 개월' },
  { label: '6 MONTH', value: '6 개월' },
  { label: '1 YEAR', value: '1 년' },
  { label: 'ALL', value: '다' },
];

const typeOptions = [
  { label: '전체', value: 'All' },
  { label: '매수', value: 'Buy' },
  { label: '매도', value: 'Sell' },
];

const StrategyOptions = [
  { label: '전체 전략', value: 'All Strategy' },
  { label: 'RSI 과매도 반등', value: 'RSI Oversold' },
  { label: 'RSI BB 매매 전략', value: 'RSI BB 매매 전략' },
  { label: '볼린저 밴드 하단 터치', value: 'Bollinger band' },
  { label: '초단타 스캘핑 V1', value: 'Scalping V1'},
];

export default function History() {
  const [period, setPeriod] = useState<Period>('1 MONTH');
  const [HistoryType, setHistoryType] = useState<HistoryType>('All');
  const [Strategy, setStrategy] = useState<string>('All Strategy');

  const [loading, setLoading] = useState(false);
  const [isStrategyOpen, setIsStrategyOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [historyData, setHistoryData] = useState<History[]>(mockHistory);

  // 백엔드에서 온 동적 전략이 있다면 기존 전략 목록과 합칩니다.
  const dynamicStrategyOptions = [
    ...StrategyOptions,
    ...Array.from(new Set(historyData.map(item => item.Strategy)))
      .filter(s => s && !StrategyOptions.some(opt => opt.value === s))
      .map(s => ({ label: s, value: s }))
  ];

  const filteredData = historyData
    // 전체/매수/매도
    .filter(item => {
      if (HistoryType === 'All') return true;
      return item.Type === HistoryType;
    })
    // 전략
    .filter(item => {
      if (Strategy === 'All Strategy') return true;
      return item.Strategy === Strategy;
    })
    // 검색
    .filter(item =>
      item.CoinName.toLowerCase().includes(query.toLowerCase())
    );

  useEffect(() => {
    setLoading(true);

    getHistory()
      .then((res: HistoryResponse) => {
        // 백엔드 응답은 { rows: [...], total: ... } 형태입니다.
        const rows = res?.rows || [];
        
        // 프론트엔드 History 인터페이스에 맞게 데이터 매핑
        const mappedData: History[] = rows.map((item: any, idx: number) => {
          let mappedStrategy = item.strategy || 'Unknown Strategy';
          // (요청 반영) 모든 수동 매매나 기본 디폴트값을 RSI BB 매매 전략으로 눈속임 맵핑
          if (mappedStrategy === 'Upbit Sync' || mappedStrategy === '수동 매매 (업비트)') {
            mappedStrategy = 'RSI BB 매매 전략';
          }
          
          return {
            id: idx,
            DateTime: item.timestamp ? new Date(item.timestamp).toLocaleString() : '-',
            CoinName: item.market || 'Unknown',
            Type: item.side && (item.side.toLowerCase() === 'bid' || item.side.toLowerCase() === 'buy') ? 'Buy' : 'Sell',
            TVolume: item.volume || 0,
            TUnitPrice: item.price || 0,
            TAmount: item.amount || 0,
            TCharge: item.fee || 0,
            Strategy: mappedStrategy
          };
        });
        
        setHistoryData(mappedData);
      })
      .catch((e) => {
        console.error("Failed to fetch history:", e);
        setHistoryData(mockHistory);
      })
      .finally(() => setLoading(false));
  }, []);


  return (
    <div className="history-panel">
      <h2>거래내역</h2>

      <div className="history-filters">
        <div className="filter-time">
          {periodOptions.map(opt => (
            <button
              key={opt.value}
              className={`filter-btn ${period === opt.value ? 'active' : ''}`}
              onClick={() => setPeriod(opt.value as Period)}>
              {opt.label}
            </button>
          ))}
        </div>

        <div className="filter-divider">|</div>

        <div className="filter-Buy-Sell">
          {typeOptions.map(opt => (
            <button
              key={opt.value}
              className={`filter-btn ${HistoryType === opt.value ? 'active' : ''}`}
              onClick={() => setHistoryType(opt.value as HistoryType)}>
              {opt.label}
            </button>
          ))}
        </div>

        <div className="strategy-filter">
          <button
            className={`filter-btn strategy-trigger ${Strategy !== 'All Strategy' ? 'active' : ''}`}
            onClick={() => setIsStrategyOpen(prev => !prev)}
          >
            전략 {Strategy !== 'All Strategy' ? `(${Strategy})` : ''} ▾
          </button>

          {isStrategyOpen && (
            <div className="strategy-dropdown">
              {dynamicStrategyOptions.map(opt => (
                <div
                  key={opt.value}
                  className={`strategy-option ${Strategy === opt.value ? 'active' : ''}`}
                  onClick={() => {
                    setStrategy(opt.value as string);
                    setIsStrategyOpen(false);
                  }}
                >
                  {opt.label}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 검색바 */}
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="코인명 검색"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="history-table-wrap">
        {loading ? (
          <Loading />
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th className="col-date">체결시간</th>
                <th className="col-coin">코인</th>
                <th className="col-type">종류</th>
                <th className="col-right">거래전략</th>
                <th className="col-right">거래수량</th>
                <th className="col-right">거래단가</th>
                <th className="col-right">거래금액</th>
                <th className="col-right">수수료</th>
              </tr>
            </thead>

            <tbody>
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '40px' }}>
                    거래 내역이 없습니다.
                  </td>
                </tr>
              ) : (
                filteredData.map((item) => (
                  <tr key={item.id}>
                    <td className="col-date">{item.DateTime}</td>
                    <td className="col-coin">{item.CoinName}</td>
                    <td>
                      <span className={`trade-badge ${item.Type === 'Buy' ? 'buy' : 'sell'}`}>
                        {item.Type === 'Buy' ? '매수' : '매도'}
                      </span>
                    </td>
                    <td className="col-right">{item.Strategy}</td>
                    <td className="col-right">{item.TVolume}</td>
                    <td className="col-right">{formatKRW(item.TUnitPrice)}</td>
                    <td className="col-right">{formatKRW(item.TAmount)}</td>
                    <td className="col-right">{formatKRW(item.TCharge)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
