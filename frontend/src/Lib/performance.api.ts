import { api } from './api';

export interface PerfSummary {
    period_label: string;
    start_assets_krw: number;
    end_assets_krw: number;
    pnl_krw: number;
    pnl_rate: number;
    // today_change는 백엔드에서 제공하지 않으므로 프론트에서 계산
    today_change_krw?: number;
    today_change_rate?: number;
}

export interface PerfChartPoint {
    date: string;
    pnl_krw: number;
    assets_krw: number;
}

export interface PerfDailyRow {
    date: string;
    pnl_krw: number;
    pnl_rate: number;
    assets_krw: number;
}

export interface PerfResponse {
    summary: PerfSummary;
    chart: PerfChartPoint[];
    daily: PerfDailyRow[];
}

export async function getPerformance(period: string): Promise<PerfResponse> {
    // 로그 기반 엔드포인트: /api/performance/summary?period=...
    const { data } = await api.get<PerfResponse>('/performance/summary', {
        params: { period }
    });
    return data;
}
