import React, { useState, useEffect } from 'react';
import './History.css';
import Loading from '../Common/Loading';
import {mockHistory} from '../../mocks/mockData';

interface History {
  id: number;
  DateTime: string;
  CoinName: string; // e.g. KRW-BTC
  Type: string;
  TVolume: number;
  TUnitPrice: number;
  TAmount: number; // 거래금액
  TCharge: number; // 수수료
  Strategy: Strategy;
}

   function filterTrades(
  data: History[],
  type: string) {
    return data.filter(item => {
      if(type === 'All') return true;
      return item.Type === type;
    });
  }

    function formatKRW(val: number) {
      return `${new Intl.NumberFormat('ko-KR').format(val)} KRW`;
  }

  type Period = '1 MONTH' | '6 MONTH' | '1 YEAR' | 'ALL';
  type HistoryType = 'Buy' | 'Sell' | 'All';
  type Strategy = 'All Strategy' | 'Moving Average Golden Cross' 
                  | 'RSI Oversold Reaction' | 'Bollinger band bottom touch';

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
    { label: '전체 전략', value: 'All Strategy'},
    { label: '이동평균선 골든크로스', value: 'Moving Average Golden Cross'},
    { label: 'RSI 과매도 반동', value: 'RSI Oversold Reaction'},
    { label: '볼린저 밴드 하단 터치', value: 'Bollinger band bottom touch'},
  ];

 export default function History() {
  const [period, setPeriod] =
    useState<Period>('1 MONTH');

  const [HistoryType, setHistory] =
    useState<HistoryType>('All');

  const [Strategy, setStrategy] = 
    useState<Strategy>('All Strategy');

  const [loading, setLoading] = useState(false);
  const [isStrategyOpen, setIsStrategyOpen] = useState(false);
  const [query, setQuery] = useState('');
const historyData: History[] = mockHistory as History[];
const filteredData = historyData
  .filter(item => {
    if (HistoryType === 'All') return true;
    return item.Type === HistoryType;
  })
  .filter(item => {
    if (Strategy === 'All Strategy') return true;
    return item.Strategy === Strategy;
  })
  .filter(item =>
    item.CoinName.toLowerCase().includes(query.toLowerCase())
  );



  return (
    <div className="history-panel">
      <h2>거래내역</h2>

      <div className="history-filters">
          <div className="filter-time">
            {periodOptions.map(opt => (   //이게 위에 있는 periodOptions 읽어와서 버튼으로 바꿔주는 기계
              <button 
                key={opt.value} 
                className={`filter-btn ${period === opt.value ? 'active' : ''}`} // 버튼이 선택되면 active 클래스 붙여라
                onClick={() => setPeriod(opt.value as Period)}>
                {opt.label}
              </button>
            ))}
          </div>

        <div className="filter-divider">|</div>

        <div className="filter-Buy-Sell">
            {typeOptions.map(opt => (
              <button
                className={`filter-btn ${HistoryType === opt.value ? 'active' : ''}`}
                onClick={() => setHistory(opt.value as HistoryType)}>
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
              {StrategyOptions.map(opt => (
                <div
                  key={opt.value}
                  className={`strategy-option ${Strategy === opt.value ? 'active' : ''}`}
                  onClick={() => {
                    setStrategy(opt.value as Strategy);
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
                  filteredData.map((item) => (
                    <tr>
                      <td className="col-date">{item.DateTime}</td>
                      <td className="col-coin">{item.CoinName}</td>
                      <td>
                        <span className={`trade-badge ${item.Type === 'Buy' ? 'buy' : 'sell'}`}>
                        {item.Type === 'Buy' ? '매수' : '매도'}
                        </span>
                      </td>

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
