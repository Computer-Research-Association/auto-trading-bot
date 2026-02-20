import React, { useEffect, useState, useMemo } from 'react';
import './Log.css';
import Loading from '../Common/Loading';
import { mockLog } from '../../mocks/mockLog';
import { apiFetch } from "../../Lib/api";
import { getLogs, type LogItem, type LogLevel } from "../../Lib/log.api"; // API & Types

// Local types removed (imported from api)
// type LogLevel = 'INFO' | 'WARNING' | 'ERROR';
// ...

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

const Filters: Array<{ key: 'ALL' | LogLevel; label: string }> = [
  { key: 'ALL', label: 'All Logs' },
  { key: 'INFO', label: 'Info' },
  { key: 'WARNING', label: 'Warning' },
  { key: 'ERROR', label: 'Error' },
];

const Log: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [query, setQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<'ALL' | LogLevel>('ALL');


  const pageSize = 5;
  const [page, setPage] = useState(1);

  useEffect(() => {
    setLoading(true);
    apiFetch<{ items: LogItem[] }>("/logs")
      .then((res) => {
        setLogs(res.items);
      })
      .catch(() => {
        setLogs(mockLog); // Fallback
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // SSE 실시간 로그 업데이트 (EventSource 연결)
  useEffect(() => {
    // 📌 SSE 엔드포인트 URL (백엔드에서 구현 필요)
    const SSE_URL = 'http://localhost:8000/api/v1/logs/stream';
    
    let eventSource: EventSource | null = null;

    // 로딩이 완료된 후에만 SSE 연결 시작
    if (!loading) {
      try {
        // EventSource 객체 생성 - 서버와 지속적인 연결 시작
        eventSource = new EventSource(SSE_URL);

        // 🔗 연결 성공 시
        eventSource.onopen = () => {
          console.log('✅ [SSE] 실시간 로그 연결 성공');
        };

        // 📨 새로운 메시지(로그) 수신 시
        // 📨 새로운 메시지(로그) 수신 시
        eventSource.onmessage = (event) => {
          try {
            // 1. 서버에서 보낸 JSON 데이터를 객체로 변환
            const newLog: LogItem = JSON.parse(event.data);
            
            console.log('📩 [SSE] 새 로그 수신:', newLog);
            
            // 2. 상태 업데이트 (기존 로그 맨 위에 추가)
            setLogs((prevLogs) => [newLog, ...prevLogs]);
            
          } catch (error) {
            console.error('❌ [SSE] 데이터 파싱 에러:', error);
          }
        };

        // ⚠️ 에러 발생 시
        eventSource.onerror = (error) => {
          console.error('⚠️ [SSE] 연결 에러:', error);
          // EventSource는 자동으로 재연결을 시도합니다 (브라우저 기본 동작)
        };
      } catch (error) {
        console.error('❌ [SSE] EventSource 생성 실패:', error);
      }
    }

    // 🔌 컴포넌트 언마운트 시 연결 종료 (cleanup 함수)
    return () => {
      if (eventSource) {
        console.log('🔌 [SSE] 연결 종료');
        eventSource.close();
      }
    };
  }, [loading]); // loading이 false가 되면 실행

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    return logs
      // 1. 등급 필터 (버튼) 적용
      .filter((l) => (levelFilter === 'ALL' ? true : l.level === levelFilter))
      // 2. 검색어 필터 적용
      .filter((l) => {
        if (!q) return true;

        // 데이터 안전성 체크
        const timestamp = l.timestamp ? l.timestamp.toLowerCase() : '';
        const category = l.category ? l.category.toLowerCase() : '';
        const eventname = l.eventname ? l.eventname.toLowerCase() : '';
        const level = l.level ? l.level.toLowerCase() : '';
        const message = l.message ? l.message.toLowerCase() : '';

        // 레벨 필터링 강화: startsWith 사용 (IN -> INFO 매칭, WARNING 제외)
        // 한글 검색 지원 (정보, 경고, 에러)
        const isLevelMatch =
          level.startsWith(q) ||
          (q === '정보' && level === 'info') ||
          (q === '경고' && level === 'warning') ||
          (q === '에러' && level === 'error');

        return (
          timestamp.includes(q) ||
          category.includes(q) ||
          eventname.includes(q) ||
          isLevelMatch ||
          message.includes(q)
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
            placeholder="등급 검색..."
          />
        </div>
        <div className="actions">
          <button className="btn ghost" type="button" onClick={onClearView}>
            🗑 Clear View
          </button>
        </div>
      </div>

      {/* Title*/}
      <div className="logHeader">
        <div>
          <h1 className="title">시스템 활동 로그</h1>
          {/* <p className="subtitle">
            Real-time monitoring and event history across all services.
          </p> */}
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
          <div>날짜 및 시간</div>
          <div>분류</div>
          <div>이벤트명</div>
          <div>등급</div>
          <div>상세내용</div>
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
