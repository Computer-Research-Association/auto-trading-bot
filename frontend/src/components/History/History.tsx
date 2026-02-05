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
}

function formatKRW(val: number) {
  return new Intl.NumberFormat('ko-KR').format(val);
}

 function filterTrades(
  data: History[],
  type: 'Buy' | 'Sell' | 'All') {
    return data.filter(item => {
      if(type === 'All') return true;
      return item.Type === type;
    });
  };

  type Period = '1 MONTH' | '6 MONTH' | '1 YEAR' | 'ALL';

  const periodOptions:{label: string; value:Period }[] = [
    { label: '1 MONTH', value: '1 MONTH' },
    { label: '6 MONTH', value: '6 MONTH' },
    { label: '1 YEAR', value: '1 YEAR' },
    { label: 'ALL', value: 'ALL' },
  ];

  const [period, setPeriod] = useState<Period>('1 MONTH');

  const typeOptions = [
    { label: 'ALL', value: 'All' },
    { label: 'BUY', value: 'Buy' },
    { label: 'SELL', value: 'Sell' },
  ];

 export default function History() {
  const [period, setPeriod] =
    useState<'1 MONTH' | '6 MONTH' | '1 YEAR' | 'ALL'>('1 MONTH');

  const [type, setType] =
    useState<'Buy' | 'Sell' | 'All'>('All');

  const [loading, setLoading] = useState(false);

  const filteredData = filterTrades(mockHistory, type);

  return (
    <div className="history-panel">
      <h2>거래내역</h2>

      <div className="history-filters">
          <div className="filter-Buy-Sell">
            {periodOptions.map(opt => (
              <button 
                key={opt.value} 
                className={`filter-btn ${period === opt.value ? 'active' : ''}`}
                onClick={() => setPeriod(opt.value)}>
                {opt.label}
              </button>
            ))}
          </div>

        <div className="filter-divider">|</div>

        <div className="filter-Buy-Sell">
            {typeOptions.map(opt => (
              <button 
                key={opt.value} 
                className={`filter-btn ${type === opt.value ? 'active' : ''}`}
                onClick={() => setType(opt.value as any)}>
                {opt.label.toUpperCase()}
              </button>
            ))}
        </div>
      </div>

      <div className="history-table-wrap">
        {loading ? (
          <Loading />
        ) : (
          <table className="history-table">
            <thead>
              <tr>
                <th>채결시간</th>
                    <th>코인</th>
                    <th>종류</th>
                    <th>거래수량</th>
                    <th>거래단가</th>
                    <th>거래금액</th>
                    <th>수수료</th>
              </tr>
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
                      <td className={`col-type ${item.Type === 'Buy' ? 'buy' : 'sell'}`}>
                        {item.Type}
                      </td>
                      <td className="col-right">{item.TVolume}</td>
                      <td className="col-right">{formatKRW(item.TUnitPrice)}</td>
                      <td className="col-right">{formatKRW(item.TAmount)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </thead>
          </table>
        )}
      </div>
    </div>
  );
}
