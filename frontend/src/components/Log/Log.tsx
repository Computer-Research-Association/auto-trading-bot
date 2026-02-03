import React, { useEffect, useState, useMemo } from 'react';
import './Log.css';
import Loading from '../Common/Loading';

type LogLevel = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';

interface LogItem {
  id: number;
  timestamp: string;
  level: LogLevel;
  source: string;
  message: string;
}

const mockLogs: LogItem[] = [
  {
    id: 1,
    timestamp: '2026-01-14 15:30:22.451',
    level: 'SUCCESS',
    source: 'Strategy: Scalp_V1',
    message: 'Order Placed: 0.5 BTC at 42,100 KRW',
  },
  {
    id: 2,
    timestamp: '2026-01-14 15:31:05.112',
    level: 'ERROR',
    source: 'System',
    message: 'Connection Timeout: API endpoint /v1/orders unreachable',
  },
  {
    id: 3,
    timestamp: '2026-01-14 15:32:01.002',
    level: 'INFO',
    source: 'Strategy: Momentum',
    message: 'Analyzing trend data for USDT pairs across 4 exchanges',
  },
  {
    id: 4,
    timestamp: '2026-01-14 15:32:45.890',
    level: 'WARNING',
    source: 'System',
    message: 'High volatility detected in KRW markets. Adjusting risk parameters...',
  },
  {
    id: 5,
    timestamp: '2026-01-14 15:33:10.221',
    level: 'SUCCESS',
    source: 'Strategy: Scalp_V1',
    message: 'Take profit executed: 0.1 BTC sold at $43,250',
  },
  {
    id: 6,
    timestamp: '2026-01-14 15:34:00.005',
    level: 'INFO',
    source: 'System',
    message: 'Periodic health check: All services operational. Database latency: 12ms.',
  },
  {
    id: 7,
    timestamp: '2026-01-14 15:34:45.001',
    level: 'INFO',
    source: 'Strategy: Grid_Bot',
    message: 'Rebalancing grid levels for ETH/USDT. Range: 2,400 - 2,800.',
  },
  {
    id: 8,
    timestamp: '2026-01-14 15:35:12.887',
    level: 'WARNING',
    source: 'Exchange: Private',
    message: 'Rate limit approaching (85% of quota used). Throttling requests for 180s.',
  },
  {
    id: 9,
    timestamp: '2026-01-14 15:36:01.002',
    level: 'SUCCESS',
    source: 'Strategy: Arbitrage',
    message: 'Cycle complete: Profit +$14.22 across gap between endpoints.',
  },
];

const Filters: Array<{key: 'ALL' | LogLevel; label: string}> = [
    {key: 'ALL', label: 'All Logs'},
    {key: 'INFO', label: 'Info'},
    {key: 'SUCCESS', label: 'Success'},
    {key: 'WARNING', label: 'Warning'},
    {key: 'ERROR', label: 'Error'},
];

const Log: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [query, setQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<'ALL' | LogLevel>('ALL');

  useEffect(() => {
    const timer = setTimeout(() => {
      setLogs(mockLogs);
      setLoading(false);
    }, 400);
    return () => clearTimeout(timer);
  }, []);

    const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return logs
      .filter((l) => (levelFilter === 'ALL' ? true : l.level === levelFilter))
      .filter((l) => {
        if (!q) return true;
        return (
          l.timestamp.toLowerCase().includes(q) ||
          l.level.toLowerCase().includes(q) ||
          l.source.toLowerCase().includes(q) ||
          l.message.toLowerCase().includes(q)
        );
      });
  }, [logs, query, levelFilter]);

  const onClearView = () => {
    setQuery('');
    setLevelFilter('ALL');
  };

  if (loading) {
    return <Loading message="로그 데이터를 불러오는 중입니다..." />;
  }

  return (
    <div className="logPage">
      {/* Top bar */}
      <div className="logTopbar">
        <div className="brand">
          <div className="brandIcon" aria-hidden />
          <div className="brandName">SystemLog Dashboard</div>
        </div>

        <div className="searchWrap">
          <span className="searchIcon" aria-hidden>🔎</span>
          <input
            className="searchInput"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search logs..."
          />
        </div>

        <div className="rightHint">
          <span className="dotLive" aria-hidden />
          Live Streaming Enabled
        </div>
      </div>

      {/* Title + actions */}
      <div className="logHeader">
        <div>
          <h1 className="title">System Activity Logs</h1>
          <p className="subtitle">Real-time monitoring and event history across all services.</p>
        </div>

        <div className="actions">
          <button className="btn primary" type="button">
            ⬇ Export CSV
          </button>
          <button className="btn ghost" type="button" onClick={onClearView}>
            🗑 Clear View
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filterRow">
        {Filters.map((f) => (
          <button
            key={f.key}
            type="button"
            className={`pill ${levelFilter === f.key ? 'active' : ''}`}
            onClick={() => setLevelFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="tableCard">
        <div className="tableHead">
          <div>TIMESTAMP</div>
          <div>LEVEL</div>
          <div>SOURCE</div>
          <div>MESSAGE</div>
        </div>

        <div className="tableBody">
          {filtered.map((l) => (
            <div className="row" key={l.id}>
              <div className="cell mono">{l.timestamp}</div>
              <div className="cell">
                <span className={`badge ${l.level.toLowerCase()}`}>{l.level}</span>
              </div>
              <div className="cell">
                <span className="sourceTag">{l.source}</span>
              </div>
              <div className="cell message">{l.message}</div>
            </div>
          ))}

          {filtered.length === 0 && (
            <div className="empty">
              검색/필터 결과가 없습니다.
            </div>
          )}
        </div>

        <div className="tableFooter">
          <span className="footerText">
            Showing 1-{Math.min(filtered.length, 50)} of {filtered.length} logs
          </span>

          <div className="pager">
            <button className="iconBtn" type="button" disabled>‹</button>
            <button className="iconBtn" type="button" disabled>›</button>
          </div>
        </div>
      </div>

      <p className="demoNote">※ 실제 데이터 연동 전, UI 예시 화면입니다.</p>
    </div>
  );
};

export default Log;
