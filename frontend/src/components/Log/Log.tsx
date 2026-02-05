import React, { useEffect, useState, useMemo } from 'react';
import './Log.css';
import Loading from '../Common/Loading';
import {mockLogs} from '../../mocks/mockData';

type LogLevel = 'INFO' | 'WARNING' | 'ERROR';
type tpstring = 'System' | 'Data' | 'Strategy' | 'Trade';

interface LogItem {
  id: number;
  timestamp: string;
  category: tpstring;
  eventname: string;
  level: LogLevel;
  message: string;
}

function getPageItems(page: number, total: number) {
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
  if (page <= 2) return [1, 2, "...", total];
  if (page >= total - 1) return [1, "...", total - 1, total];
  return [1, "...", page, "...", total];
}

export function PageBlock({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  const items = getPageItems(page, totalPages);

  return (
    <div className="pagination">
      <button
        className="pageNav"
        onClick={() => onChange(Math.max(1, page - 1))}
        disabled={page === 1}
      >
        ‹
      </button>

      {items.map((it, idx) =>
        it === "..." ? (
          <span key={`dots-${idx}`} className="pageDots">…</span>
        ) : (
          <button
            key={it}
            className={`pageBtn ${page === it ? "active" : ""}`}
            onClick={() => onChange(it as number)}
          >
            {it}
          </button>
        )
      )}

      <button
        className="pageNav"
        onClick={() => onChange(Math.min(totalPages, page + 1))}
        disabled={page === totalPages}
      >
        ›
      </button>
    </div>
  );
}



const Filters: Array<{key: 'ALL' | LogLevel; label: string}> = [
    {key: 'ALL', label: 'All Logs'},
    {key: 'INFO', label: 'Info'},
    {key: 'WARNING', label: 'Warning'},
    {key: 'ERROR', label: 'Error'},
];

const Log: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [query, setQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<'ALL' | LogLevel>('ALL');
  

    const pageSize = 5;
    const [page, setPage] = useState(1);

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
          l.category.toLowerCase().includes(q) ||
          l.eventname.toLowerCase().includes(q) ||
          l.level.toLowerCase().includes(q) ||
          l.message.toLowerCase().includes(q)
        );
      });
  }, [logs, query, levelFilter]);

  const totalPages = Math.ceil(filtered.length / pageSize);
  const startIndex = filtered.length === 0 ? 0 : (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, filtered.length);


    const pagedLogs = useMemo<LogItem[]>(() => {
    const start = (page - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
    }, [filtered, page]);

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
          Active
        </div>
      </div>

      {/* Title + actions */}
        <div className="logHeader">
        <div>
          <h1 className="title">System Activity Logs</h1>
          <p className="subtitle">
            Real-time monitoring and event history across all services.
          </p>
        </div>

        <div className="actions">
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
        <div>CATEGORY</div>
        <div>EVENT NAME</div>
        <div>LEVEL</div>
        <div>MESSAGE</div>
      </div>

      <div className="tableBody">
        {pagedLogs.map((l) => (
          <div className="row" key={l.id}>
            <div className="cell mono">{l.timestamp}</div>
            <div className="cell">{l.category}</div>
            <div className="cell">{l.eventname}</div>
            <div className="cell level">
              <div className={`badge ${l.level.toLowerCase()}`}>
                {l.level}
              </div>
            </div>
              <div className="cell message">{l.message}</div>
          </div>
        ))}
        {pagedLogs.length === 0 && (
          <div className="empty">검색/필터 결과가 없습니다.</div>
        )}
      </div>
        <PageBlock
          page={page}
          totalPages={Math.ceil(filtered.length / pageSize)}
          onChange={setPage}
          />

        <div className="tableFooter">
          <span className="footerText">
            Showing {startIndex}-{endIndex} of {filtered.length} logs
          </span>
        </div>
      </div>

      <p className="demoNote">※ 실제 데이터 연동 전, UI 예시 화면입니다.</p>
    </div>
  );
};


export default Log;
