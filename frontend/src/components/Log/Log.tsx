import React, { useEffect, useState } from 'react';
import './Log.css';
import Loading from '../Common/Loading';
import { apiFetch } from "../../Lib/api";
import { type LogItem, type LogLevel } from "../../Lib/log.api";

/* ───────────────────────────────────────────────────────────────
   유틸: 날짜 포맷
─────────────────────────────────────────────────────────────── */
function formatDateKST(utcStr: string): string {
  if (!utcStr) return '';
  const safeStr = utcStr.endsWith('Z') || utcStr.includes('+') ? utcStr : `${utcStr}Z`;
  const date = new Date(safeStr);
  if (isNaN(date.getTime())) return utcStr;
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  }).format(date);
}

/* ───────────────────────────────────────────────────────────────
   페이지네이션
─────────────────────────────────────────────────────────────── */
function getPageItems(page: number, total: number) {
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
  if (page <= 2) return [1, 2, '...', total];
  if (page >= total - 1) return [1, '...', total - 1, total];
  return [1, '...', page, '...', total];
}

export function PageBlock({ page, totalPages, onChange }: {
  page: number; totalPages: number; onChange: (p: number) => void;
}) {
  return (
    <div className="pagination">
      <button className="pageNav" onClick={() => onChange(Math.max(1, page - 1))} disabled={page === 1}>‹</button>
      {getPageItems(page, totalPages).map((it, idx) =>
        it === '...'
          ? <span key={`d${idx}`} className="pageDots">…</span>
          : <button key={it} className={`pageBtn ${page === it ? 'active' : ''}`} onClick={() => onChange(it as number)}>{it}</button>
      )}
      <button className="pageNav" onClick={() => onChange(Math.min(totalPages, page + 1))} disabled={page === totalPages}>›</button>
    </div>
  );
}

/* ───────────────────────────────────────────────────────────────
   상수 / 타입
─────────────────────────────────────────────────────────────── */
const LEVELS: LogLevel[] = ['INFO', 'WARNING', 'ERROR'];

const LEVEL_COLOR: Record<LogLevel, string> = {
  INFO:    '#2563eb',
  WARNING: '#d97706',
  ERROR:   '#dc2626',
};

const CATEGORIES = ['System', 'Data', 'Strategy', 'Trade'] as const;
type CategoryType = typeof CATEGORIES[number];

const CATEGORY_EVENTS: Record<CategoryType, string[]> = {
  System: ['Engine_Start', 'Heartbeat', 'Command', 'Sync', 'Error', 'Kill_Switch', 'Snapshot_Saved', 'Snapshot_Failed', 'Log_Cleanup_Success', 'Log_Cleanup_Failed'],
  Data: ['Fetch_Fail', 'Valid_Fail', 'Type_Error'],
  Strategy: ['Decision'],
  Trade: ['Buy', 'Sell', 'Stoploss']
};

// 사이드바 이벤트명 호버 시 뜨는 툴팁 설명
const EVENT_DESC: Record<string, string> = {
  Engine_Start: '봇 가동 시작 및 설정 정보',
  Heartbeat:    '주기적 생존 신고 및 요약 상태',
  Error:        '시스템 내부 치명적 예외',
  Fetch_Fail:   'API 통신 실패 및 재시도',
  Valid_Fail:   '데이터 개수 부족 또는 규격 미달',
  Decision:     '주기적 매매 판단 (RSI 등 수치 및 목표가 갱신 포함)',
  Buy:          '매수 체결 성공 정보',
  Sell:         '매도 체결 성공 및 수익률',
  Stoploss:     '스탑로스 도달 경고 및 긴급 매도 원인',
  Command:      '외부 명령 수신 이벤트',
  Sync:         '상태 동기화 및 데이터 갱신',
  Kill_Switch:  '시스템 보호를 위한 봇의 긴급 정지',
  Snapshot_Saved: '포트폴리오 스냅샷 백업 성공',
  Snapshot_Failed: '포트폴리오 스냅샷 백업 실패',
  Log_Cleanup_Success: '스케줄러에 의한 오래된 로그 정리 완료',
  Log_Cleanup_Failed: '오래된 로그 자동 삭제 중 오류',
  Type_Error:   '데이터 타입 파싱 실패 혹은 계산 오류'
};

type ActiveFilter =
  | { type: 'level';     value: LogLevel }
  | { type: 'category';  value: string }
  | { type: 'eventname'; value: string }
  | { type: 'date';      value: string; label: string };

/* ───────────────────────────────────────────────────────────────
   메인 컴포넌트
─────────────────────────────────────────────────────────────── */
const Log: React.FC = () => {
  /* ── 기본 상태 ── */
  const [loading, setLoading]           = useState(true);
  const [logs, setLogs]                 = useState<LogItem[]>([]);
  const [totalCount, setTotalCount]     = useState(0);
  const [sseConnected, setSseConnected] = useState(false);

  /* ── 검색 ── */
  const [searchInput, setSearchInput] = useState('');
  const [query, setQuery]             = useState('');

  /* ── 페이지 ── */
  const pageSize = 10;
  const [page, setPage] = useState(1);

  /* ── 사이드바 아코디언 열림 여부 ── */
  const [openSections, setOpenSections] = useState({
    level: true, category: true, date: false,
  });

  /* ── 카테고리 → 이벤트명 드릴다운 ── */
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  /* ── 활성 필터 목록 (칩) ── */
  const [activeFilters, setActiveFilters] = useState<ActiveFilter[]>([]);

  /* ── AND / OR 로직 ── */
  const [filterOp, setFilterOp] = useState<'AND' | 'OR'>('AND');

  /* ── 날짜 범위 ── */
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo]     = useState('');

  /* ─────────────────────────────────────────────────────────────
     검색어 디바운스
  ───────────────────────────────────────────────────────────── */
  useEffect(() => {
    const t = setTimeout(() => {
      setQuery(prev => { if (prev !== searchInput) { setPage(1); return searchInput; } return prev; });
    }, 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  /* ─────────────────────────────────────────────────────────────
     로그 fetch (서버 사이드 페이지네이션 + 필터)
  ───────────────────────────────────────────────────────────── */
  const fetchLogs = async () => {
    setLoading(true);
    try {
      const p = new URLSearchParams();
      p.append('page', page.toString());
      p.append('limit', pageSize.toString());

      activeFilters.forEach(f => {
        if (f.type === 'level')     p.append('level', f.value);
        if (f.type === 'category')  p.append('category', f.value.toUpperCase());
        if (f.type === 'eventname') p.append('eventname', f.value.toUpperCase());
        if (f.type === 'date') {
          const [from, to] = f.value.split('~');
          if (from) p.append('start_date', from.trim());
          if (to)   p.append('end_date', to.trim());
        }
      });

      // filter_op 은 필터 개수와 무관하게 항상 전송
      // (빠뜨리면 백엔드 기본값이 적용되어 toggle 이 무의미해짐)
      p.append('filter_op', filterOp);

      if (query.trim()) p.append('search', query.trim());

      const res = await apiFetch<{ items: LogItem[]; total_count: number }>(
        `/v1/logs?${p.toString()}`
      );
      setLogs(res.items);
      setTotalCount(res.total_count);
    } catch (e) {
      console.error('Failed to fetch logs:', e);
      setLogs([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, [page, activeFilters, filterOp, query]);



  /* ─────────────────────────────────────────────────────────────
     SSE 실시간 업데이트
  ───────────────────────────────────────────────────────────── */
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource('http://localhost:8000/api/v1/logs/stream');
      es.onopen = () => setSseConnected(true);
      es.onmessage = (event) => {
        try {
          const newLog: LogItem = JSON.parse(event.data);
          if (page === 1 && activeFilters.length === 0 && !query) {
            setLogs(prev => {
              if (prev.some(l => l.id === newLog.id)) return prev;
              const updated = [newLog, ...prev];
              if (updated.length > pageSize) updated.pop();
              return updated;
            });
            setTotalCount(prev => prev + 1);
          }
        } catch { /* ignore */ }
      };
      es.onerror = () => { setSseConnected(false); es?.close(); };
    } catch { /* ignore */ }
    return () => { es?.close(); };
  }, [page, activeFilters.length, query]);

  /* ─────────────────────────────────────────────────────────────
     필터 추가/제거 헬퍼
  ───────────────────────────────────────────────────────────── */
  const addFilter = (filter: ActiveFilter) => {
    // 같은 type + value가 이미 있으면 추가 안 함 (toggleFilter가 제거 처리)
    setActiveFilters(prev => {
      if (prev.some(f => f.type === filter.type && f.value === filter.value)) return prev;
      return [...prev, filter];
    });
    setPage(1);
  };

  const removeFilter = (type: string, value?: string) => {
    setActiveFilters(prev => prev.filter(f => !(f.type === type && (!value || f.value === value))));
    setPage(1);
  };

  const toggleFilter = (filter: ActiveFilter) => {
    const exists = activeFilters.find(f => f.type === filter.type && f.value === filter.value);
    if (exists) removeFilter(filter.type, filter.value);
    else addFilter(filter);
  };

  const isActive = (type: string, value: string) =>
    activeFilters.some(f => f.type === type && f.value === value);

  /* ─────────────────────────────────────────────────────────────
     날짜 필터 적용
  ───────────────────────────────────────────────────────────── */
  const applyDateFilter = () => {
    if (!dateFrom && !dateTo) return;
    const label = `${dateFrom || '시작'}~${dateTo || '종료'}`;
    addFilter({ type: 'date', value: `${dateFrom}~${dateTo}`, label });
  };

  /* ─────────────────────────────────────────────────────────────
     아코디언 토글
  ───────────────────────────────────────────────────────────── */
  const toggleSection = (key: keyof typeof openSections) =>
    setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));

  /* ─────────────────────────────────────────────────────────────
     초기화
  ───────────────────────────────────────────────────────────── */
  const clearAll = () => {
    setActiveFilters([]);
    setSearchInput('');
    setQuery('');
    setDateFrom('');
    setDateTo('');
    setExpandedCategory(null);
    setPage(1);
  };


  /* ─────────────────────────────────────────────────────────────
     계산값
  ───────────────────────────────────────────────────────────── */
  const totalPages = Math.ceil(totalCount / pageSize) || 1;
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex   = Math.min(page * pageSize, totalCount);

  /* ═══════════════════════════════════════════════════════════════
     RENDER
  ════════════════════════════════════════════════════════════════ */
  return (
    <div className="logPage">

      {/* ── 상단 Topbar ─────────────────────────────────────────── */}
      <div className="logTopbar">
        <div className="brand">
          <div className={`brandIcon ${sseConnected ? 'online' : 'offline'}`}
               title={sseConnected ? '실시간 연동됨' : '연결 끊김'} />
        </div>
        <div className="searchWrap">
          <span className="searchIcon">🔎</span>
          <input
            className="searchInput"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            placeholder="이벤트명 / 등급 / 상세내용 검색..."
          />
        </div>
        <div className="actions">
          <button className="btn ghost" onClick={clearAll}>🗑 Clear View</button>
        </div>
      </div>

      {/* ── 제목 ─────────────────────────────────────────────────── */}
      <div className="logHeader">
        <h1 className="title">시스템 활동 로그</h1>
      </div>

      {/* ── 활성 필터 칩 ─────────────────────────────────────────── */}
      {activeFilters.length > 0 && (
        <div className="activeChips">
          <span className="activeChipsLabel">적용된 필터</span>
          {activeFilters.map((f, i) => (
            <span key={i} className={`activeChip chip-${f.type}`}>
              {f.type === 'level' && <span className="chipDot" style={{ background: LEVEL_COLOR[f.value as LogLevel] }} />}
              {f.type === 'date' ? (f as any).label : f.value.toUpperCase()}
              <button className="chipClose" onClick={() => removeFilter(f.type, f.value)}>×</button>
            </span>
          ))}

          {/* AND/OR 토글 (필터가 2개 이상일 때만 표시) */}
          {activeFilters.length >= 2 && (
            <div className="filterOpToggle">
              <button
                className={`filterOpBtn ${filterOp === 'AND' ? 'opActive' : ''}`}
                onClick={() => setFilterOp('AND')}
                title="AND: 선택한 조건을 모두 동시에 만족하는 로그만 표시 (같은 필드 여러 개 선택 시 0건)"
              >AND</button>
              <button
                className={`filterOpBtn ${filterOp === 'OR' ? 'opActive' : ''}`}
                onClick={() => setFilterOp('OR')}
                title="OR: 선택한 조건 중 하나라도 맞으면 표시"
              >OR</button>
            </div>
          )}

          <button className="chipClearAll" onClick={clearAll}>전체 초기화</button>
        </div>
      )}

      {/* ── 본문: 사이드바 + 테이블 ──────────────────────────────── */}
      <div className="logBody">

        {/* ━━━━ 좌측 사이드바 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <aside className="filterSidebar">

          {/* 1. Level 섹션 */}
          <div className="accordionItem">
            <button className="accordionHeader" onClick={() => toggleSection('level')}>
              <span>Level</span>
              <span className={`accordionChevron ${openSections.level ? 'open' : ''}`}>›</span>
            </button>
            {openSections.level && (
              <div className="accordionBody">
                {LEVELS.map(lvl => (
                  <button
                    key={lvl}
                    className={`sidebarOption ${isActive('level', lvl) ? 'sidebarOptionActive' : ''}`}
                    onClick={() => toggleFilter({ type: 'level', value: lvl })}
                  >
                    <span className="sidebarDot" style={{ background: LEVEL_COLOR[lvl] }} />
                    <span className="sidebarLabel" style={lvl === 'ERROR' ? { color: '#dc2626', fontWeight: 700 } : {}}>
                      {lvl}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* 2. Category + EventName 드릴다운 */}
          <div className="accordionItem">
            <button className="accordionHeader" onClick={() => toggleSection('category')}>
              <span>Category</span>
              <span className={`accordionChevron ${openSections.category ? 'open' : ''}`}>›</span>
            </button>
            {openSections.category && (
              <div className="accordionBody">
                {CATEGORIES.map(cat => (
                  <div key={cat}>
                    <div className="categoryRow">
                      <button
                        className={`sidebarOption catOption ${isActive('category', cat) ? 'sidebarOptionActive' : ''}`}
                        onClick={() => toggleFilter({ type: 'category', value: cat })}
                      >
                        <span className="sidebarLabel">{cat.toUpperCase()}</span>
                      </button>
                      {/* 드릴다운 토글 화살표 */}
                      <button
                        className="drillToggle"
                        onClick={() => setExpandedCategory(prev => prev === cat ? null : cat)}
                        title="이벤트명 보기"
                      >
                        <span className={`accordionChevron ${expandedCategory === cat ? 'open' : ''}`}>›</span>
                      </button>
                    </div>

                    {/* 이벤트명 서브 메뉴 */}
                    {expandedCategory === cat && (
                      <div className="subMenu">
                        {CATEGORY_EVENTS[cat as CategoryType].map((ev: string) => (
                          <button
                            key={ev}
                            className={`sidebarOption subOption ${isActive('eventname', ev) ? 'sidebarOptionActive' : ''}`}
                            onClick={() => toggleFilter({ type: 'eventname', value: ev })}
                            title={EVENT_DESC[ev]}
                          >
                            <span className="subDot">·</span>
                            <span className="sidebarLabel">{ev.toUpperCase()}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Date Range 섹션 */}
          <div className="accordionItem">
            <button className="accordionHeader" onClick={() => toggleSection('date')}>
              <span>Date Range</span>
              <span className={`accordionChevron ${openSections.date ? 'open' : ''}`}>›</span>
            </button>
            {openSections.date && (
              <div className="accordionBody dateSection">
                <label className="dateLabel">시작일</label>
                <input type="date" className="dateInput" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
                <label className="dateLabel">종료일</label>
                <input type="date" className="dateInput" value={dateTo} onChange={e => setDateTo(e.target.value)} />
                <button className="applyDateBtn" onClick={applyDateFilter}>적용</button>
              </div>
            )}
          </div>
        </aside>

        {/* ━━━━ 우측 테이블 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <div className="tableArea">
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
              ) : logs.map(l => (
                <div className="row" key={l.id}>
                  <div className="cell mono">{formatDateKST(l.timestamp)}</div>
                  <div className="cell">{l.category}</div>
                  <div className="cell">{l.eventname}</div>
                  <div className="cell level">
                    <div className={`badge ${l.level.toLowerCase()}`}>{l.level}</div>
                  </div>
                  <div className="cell message">{l.message}</div>
                </div>
              ))}
              {logs.length === 0 && !loading && (
                <div className="empty">검색/필터 결과가 없습니다.</div>
              )}
            </div>

            <PageBlock page={page} totalPages={totalPages} onChange={setPage} />

            <div className="tableFooter">
              <span className="footerText">
                {totalCount > 0 ? `Showing ${startIndex}–${endIndex} of ${totalCount} logs` : 'No logs'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Log;
