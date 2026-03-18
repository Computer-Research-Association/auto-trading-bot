import { api } from './api';

export type LogLevel = 'INFO' | 'WARNING' | 'ERROR';
export type tpstring = 'System' | 'Data' | 'Strategy' | 'Trade';

export interface LogItem {
    id: number;
    timestamp: string;
    category: tpstring;
    eventname: string;
    level: LogLevel;
    message: string;
}

export type LogsResponse = {
    items: LogItem[];
};

export async function getLogs(): Promise<LogItem[]> {
    // 예상 엔드포인트: /logs
    // 응답 구조가 { items: [] } 인지 바로 [] 인지 확인 필요하나, 
    // Log.tsx의 기존 주석 참고: apiFetch<LogsResponse>("/api/logs") -> res.items
    const { data } = await api.get<LogsResponse>('/v1/logs');
    return data.items;
}
