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
  const [totalCount, setTotalCount] = useState(0); // 전체 로그 개수 (서버에서 받음)
  const [query, setQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [levelFilter, setLevelFilter] = useState<'ALL' | LogLevel>('ALL');

  // 검색어 디바운스 처리
  useEffect(() => {
    const timer = setTimeout(() => {
      setQuery((prev) => {
        if (prev !== searchInput) {
          setPage(1); // 검색어가 실제로 변경되었을 때만 1페이지로
          return searchInput;
        }
        return prev;
      });
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const pageSize = 5;
  const [page, setPage] = useState(1);
  const [sseConnected, setSseConnected] = useState(false);

  // 1. 로그 데이터 가져오기 (서버 사이드 페이지네이션 & 필터링)
  const fetchLogs = async () => {
    setLoading(true);
    try {
      // 쿼리 파라미터 구성
      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("limit", pageSize.toString());
      if (levelFilter !== "ALL") params.append("level", levelFilter);
      if (query.trim()) params.append("search", query.trim());

      const res = await apiFetch<{ items: LogItem[]; total_count: number }>(
        `/v1/logs?${params.toString()}`
      );
      setLogs(res.items);
      setTotalCount(res.total_count);
    } catch (e) {
      console.error("Failed to fetch logs:", e);
      // 에러 시 빈 배열 (목 데이터 제거)
      setLogs([]); 
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  // 페이지, 필터, 검색어 변경 시 API 재호출
  useEffect(() => {
    fetchLogs();
  }, [page, levelFilter, query]); // 의존성 배열에 파라미터들 포함

  // 2. SSE 실시간 로그 업데이트 (EventSource 연결)
  useEffect(() => {
    // 📌 SSE 엔드포인트 URL (절대 경로 사용 - 404 방지)
    // 백엔드는 8000 포트, 프론트는 5173 포트이므로 명시적 지정 필요
    // (Vite proxy 설정이 확실하다면 상대 경로도 가능하지만, 안전하게 절대 경로 사용)
    const SSE_URL = 'http://localhost:8000/api/v1/logs/stream';
    
    let eventSource: EventSource | null = null;

    try {
      eventSource = new EventSource(SSE_URL);

      eventSource.onopen = () => {
        console.log('✅ [SSE] 실시간 로그 연결 성공');
        setSseConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const newLog: LogItem = JSON.parse(event.data);
          
          // 🚨 중요: 1페이지를 보고 있고, 필터/검색어가 없을 때만 리스트에 추가
          // (과거 페이지를 보는데 갑자기 새 로그가 끼어들면 안 됨)
          if (page === 1 && levelFilter === 'ALL' && query === '') {
            setLogs((prevLogs) => {
              // 중복 방지 (혹시 몰라서)
              if (prevLogs.some(l => l.id === newLog.id)) return prevLogs;
              
              // 맨 앞에 추가하고 pageSize 개수만큼만 유지 (선택사항, 일단은 그냥 추가)
              const updated = [newLog, ...prevLogs];
              if (updated.length > pageSize) updated.pop(); // 길어지면 뒤에꺼 자름
              return updated;
            });
            // 전체 개수도 1 증가 (실시간 반영)
            setTotalCount(prev => prev + 1);
          } else {
             // 다른 페이지 보고 있을 땐 알림만? (지금은 생략)
             console.log('📩 [SSE] 백그라운드 수신:', newLog);
          }
          
        } catch (error) {
          console.error('❌ [SSE] 데이터 파싱 에러:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('⚠️ [SSE] 연결 에러', error);
        // EventSource는 자동 재연결 시도함.
        // 연결 끊김 상태 표시를 위해 state 업데이트 가능
        setSseConnected(false);
        eventSource?.close(); // 에러 시 닫고 재연결 유도? 아님 브라우저에게 맡김?
        // 보통 닫으면 재연결 안 함. 브라우저가 알아서 하도록 둠.
      };
    } catch (error) {
      console.error('❌ [SSE] EventSource 생성 실패:', error);
    }

    return () => {
      if (eventSource) {
        console.log('🔌 [SSE] 연결 종료');
        eventSource.close();
      }
    };
  }, [page, levelFilter, query]); // 페이지/필터 상태에 따라 SSE 로직(추가 여부)이 달라져야 하므로 의존성 추가?
  // 아니면 내부에서 state ref를 쓰거나 해야 하는데, 
  // 심플하게: 의존성 넣으면 페이지 바뀔 때마다 연결 끊고 다시 맺음. (비효율적일 수 있음)
  // 하지만 구현이 제일 쉬움. -> 'page === 1' 조건이 closure에 갇히지 않게 하려면 의존성 필요.

  // 3. 필터 핸들러 (서버 사이드이므로 페이지 1로 리셋)
  const handleLevelFilter = (lvl: 'ALL' | LogLevel) => {
    setLevelFilter(lvl);
    setPage(1);
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
      setSearchInput(e.target.value);
  };

  const onClearView = () => {
    setSearchInput('');
    setQuery('');
    setLevelFilter('ALL');
    setPage(1);
  };

  // 계산된 totalPages (서버에서 받은 totalCount 기반)
  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, totalCount);

  return (
    <div className="logPage">
      {/* Top bar */}
      <div className="logTopbar">
        <div className="brand">
          <div className={`brandIcon ${sseConnected ? 'online' : 'offline'}`} aria-hidden title={sseConnected ? "실시간 연동됨" : "연결 끊김"} />
        </div>

        <div className="searchWrap">
          <span className="searchIcon" aria-hidden>🔎</span>
          <input
            className="searchInput"
            value={searchInput}
            onChange={handleSearch}
            placeholder="이벤트명/등급/상세내용 검색..."
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
        </div>
      </div>

      {/* Filters */}
      <div className="filterRow">
        {Filters.map((f) => (
          <button
            key={f.key}
            type="button"
            className={`pill ${levelFilter === f.key ? 'active' : ''}`}
            onClick={() => handleLevelFilter(f.key)}
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
          {loading && logs.length === 0 ? (
            <div style={{ padding: '40px 0', display: 'flex', justifyContent: 'center' }}>
              <Loading message="로그 데이터를 불러오는 중입니다..." />
            </div>
          ) : logs.map((l) => (
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
          {logs.length === 0 && !loading && (
            <div className="empty">검색/필터 결과가 없습니다.</div>
          )}
        </div>
        
        {/* 서버 사이드 페이지네이션이므로 totalPages 전달 */}
        <PageBlock
          page={page}
          totalPages={totalPages}
          onChange={setPage}
        />

        <div className="tableFooter">
          <span className="footerText">
             {totalCount > 0 ? `Showing ${startIndex}-${endIndex} of ${totalCount} logs` : 'No logs'}
          </span>
        </div>
      </div>
    </div>
  );
};


export default Log;
