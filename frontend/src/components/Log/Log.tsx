import React, { useEffect, useState } from 'react';
import './Log.css';
import Loading from '../Common/Loading';

type LogLevel = 'INFO' | 'WARNING' | 'ERROR';
type LogSlot = 'SYSTEM' | 'SLOT1' | 'SLOT2' | 'SLOT3';

interface LogItem {
  id: number;
  timestamp: string;
  level: LogLevel;
  slot: LogSlot;
  message: string;
}

// 🔹 로그 예시용 mock 데이터
const mockLogs: LogItem[] = [
  {
    id: 1,
    timestamp: '15:41:22',
    level: 'INFO',
    slot: 'SYSTEM',
    message: 'Trading engine started',
  },
  {
    id: 2,
    timestamp: '15:41:30',
    level: 'INFO',
    slot: 'SLOT1',
    message: 'Strategy A initialized',
  },
  {
    id: 3,
    timestamp: '15:42:05',
    level: 'ERROR',
    slot: 'SLOT2',
    message: 'Order failed (insufficient balance)',
  },
  {
    id: 4,
    timestamp: '15:42:07',
    level: 'WARNING',
    slot: 'SLOT3',
    message: 'Execution delay detected (120ms)',
  },
];

const Log: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<LogItem[]>([]);

  useEffect(() => {
    // 🔹 시각적 효과용 로딩
    const timer = setTimeout(() => {
      setLogs(mockLogs);
      setLoading(false);
    }, 400);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return <Loading message="로그 데이터를 불러오는 중입니다..." />;
  }

  return (
    <div className="log-panel">
      <div className="log-header">
        <h2>Log</h2>
        <p className="log-sub">
          ※ 실제 데이터 연동 전, 로그 화면 예시입니다.
        </p>
      </div>

      <div className="log-list">
        {logs.map((log) => (
          <div key={log.id} className={`log-row ${log.level.toLowerCase()}`}>
            <span className="log-time">{log.timestamp}</span>
            <span className="log-level">{log.level}</span>
            <span className="log-slot">{log.slot}</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Log;
