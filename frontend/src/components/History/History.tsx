import React, { useState, useEffect } from 'react';
import './History.css';
import Loading from '../Common/Loading';

interface TradeHistory {
  id: string;
  date: string;
  market: string; // e.g. KRW-BTC
  type: 'buy' | 'sell' | 'deposit' | 'withdraw';
  price: number;
  volume: number;
  amount: number; // 거래금액
  fee: number;
  strategyId?: string; // 연결된 전략 ID
}

// 목업 데이터 (전략 ID 추가)
const MOCK_DATA: TradeHistory[] = [
  { id: '1', date: '2026.01.27 14:30', market: 'KRW-BTC', type: 'buy', price: 136200000, volume: 0.005, amount: 681000, fee: 340, strategyId: 'ma_cross' },
  { id: '2', date: '2026.01.26 09:15', market: 'KRW-XRP', type: 'sell', price: 3440, volume: 100, amount: 344000, fee: 172, strategyId: 'rsi_rebound' },
  { id: '3', date: '2026.01.25 18:20', market: 'KRW', type: 'deposit', price: 1, volume: 1000000, amount: 1000000, fee: 0 },
  { id: '4', date: '2026.01.24 11:00', market: 'KRW-ETH', type: 'buy', price: 4680000, volume: 0.1, amount: 468000, fee: 234, strategyId: 'ma_cross' },
  { id: '5', date: '2026.01.20 15:45', market: 'KRW-SOL', type: 'sell', price: 200300, volume: 5, amount: 1001500, fee: 500, strategyId: 'bb_lower' },
];

const STRATEGIES = [
  { id: 'all', name: '전체 전략' },
  { id: 'ma_cross', name: '이동평균선 골든크로스' },
  { id: 'rsi_rebound', name: 'RSI 과매도 반등' },
  { id: 'bb_lower', name: '볼린저 밴드 하단 터치' },
];

function formatKRW(val: number) {
  return new Intl.NumberFormat('ko-KR').format(val);
}

export default function History() {
  const [period, setPeriod] = useState('1m');
  const [filterType, setFilterType] = useState('all');
  const [selectedStrategy, setSelectedStrategy] = useState('all');
  const [showStrategyModal, setShowStrategyModal] = useState(false);

  const periodOptions = [
    { label: '1주일', value: '1w' },
    { label: '1개월', value: '1m' },
    { label: '3개월', value: '3m' },
    { label: '6개월', value: '6m' },
  ];

  const typeOptions = [
    { label: '전체', value: 'all' },
    { label: '매수', value: 'buy' },
    { label: '매도', value: 'sell' },
    { label: '입금', value: 'deposit' },
    { label: '출금', value: 'withdraw' },
  ];

  // 필터링 로직
  const filteredData = MOCK_DATA.filter(item => {
    // 1. 거래 종류 필터
    const matchType = filterType === 'all' || item.type === filterType;
    // 2. 전략 필터
    const matchStrategy = selectedStrategy === 'all' || item.strategyId === selectedStrategy;

    const [loading, setLoading] = useState(true);

    useEffect(() => {
      // 탭 전환 시 부드러운 전환을 위해 아주 짧은 로딩 시뮬레이션
      const timer = setTimeout(() => setLoading(false), 500);
      return () => clearTimeout(timer);
    }, []);

    if (loading) return <Loading />;

    return matchType && matchStrategy;
  });

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'buy': return '매수';
      case 'sell': return '매도';
      case 'deposit': return '입금';
      case 'withdraw': return '출금';
      default: return type;
    }
  };

  const getStrategyName = (id?: string) => {
    if (!id) return '-';
    return STRATEGIES.find(s => s.id === id)?.name || id;
  };

  return (
    <div className="history-panel">
      <div className="history-header">
        <h2 className="history-title">거래내역</h2>
      </div>

      <div className="history-filters">
        <div className="filter-group">
          {periodOptions.map(opt => (
            <button
              key={opt.value}
              className={`filter-btn ${period === opt.value ? 'active' : ''}`}
              onClick={() => setPeriod(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="filter-group" style={{ marginLeft: '16px', borderLeft: '1px solid #e5e7eb', paddingLeft: '16px', position: 'relative' }}>
          {typeOptions.map(opt => (
            <button
              key={opt.value}
              className={`filter-btn ${filterType === opt.value ? 'active' : ''}`}
              onClick={() => setFilterType(opt.value)}
            >
              {opt.label}
            </button>
          ))}

          {/* 전략 필터 버튼 */}
          <button
            className={`filter-btn strategy-filter-trigger ${selectedStrategy !== 'all' ? 'active' : ''}`}
            onClick={() => setShowStrategyModal(!showStrategyModal)}
          >
            전략 {selectedStrategy !== 'all' ? `(${getStrategyName(selectedStrategy)})` : '▾'}
          </button>

          {/* 전략 선택 모달 (Dropdown 형태) */}
          {showStrategyModal && (
            <div className="strategy-modal">
              <div className="modal-header">
                전략 선택
                <button className="close-btn" onClick={() => setShowStrategyModal(false)}>×</button>
              </div>
              <div className="strategy-options">
                {STRATEGIES.map(s => (
                  <div
                    key={s.id}
                    className={`strategy-opt ${selectedStrategy === s.id ? 'active' : ''}`}
                    onClick={() => {
                      setSelectedStrategy(s.id);
                      setShowStrategyModal(false);
                    }}
                  >
                    {s.name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input type="text" className="search-input" placeholder="코인명/심볼 검색" />
        </div>
      </div>

      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>체결시간</th>
              <th>코인</th>
              <th>종류</th>
              <th className="col-right">거래수량</th>
              <th className="col-right">거래단가</th>
              <th className="col-right">거래금액</th>
              <th className="col-right">수수료</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px' }}>
                  거래 내역이 없습니다.
                </td>
              </tr>
            ) : (
              filteredData.map(item => (
                <tr key={item.id}>
                  <td className="col-date">{item.date}</td>
                  <td className="col-coin">{item.market}</td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span className={`badge ${item.type}`}>
                        {getTypeLabel(item.type)}
                      </span>
                      {item.strategyId && (
                        <span className="strategy-tag">
                          {getStrategyName(item.strategyId)}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="col-right">{item.volume}</td>
                  <td className="col-right">{formatKRW(item.price)} KRW</td>
                  <td className="col-right" style={{ fontWeight: 600 }}>{formatKRW(item.amount)} KRW</td>
                  <td className="col-right" style={{ color: '#888' }}>{formatKRW(item.fee)} KRW</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
