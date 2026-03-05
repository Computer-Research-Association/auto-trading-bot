import { api } from './api';

export type Strategy = 'All Strategy' | 'Moving Average' | 'RSI Oversold' | 'Bollinger band' | 'Scalping V1';
export type HistoryType = 'Buy' | 'Sell' | 'All';

export interface History {
    id: number;
    DateTime: string;
    CoinName: string;
    Type: string;
    TVolume: number;
    TUnitPrice: number;
    TAmount: number;
    TCharge: number;
    Strategy: Strategy;
}

// 여기

export interface HistoryResponse {
    rows: History[];
    total: number;
    page: number;
    limit: number;
}

export async function getHistory(period: string = '1 개월'): Promise<HistoryResponse> {
    const periodMap: Record<string, string> = {
        '1 개월': '30d',
        '6 개월': '180d',
        '1 년': '180d',
        '다': 'all',
    };
    const backendPeriod = periodMap[period] ?? '30d';
    const { data } = await api.get<HistoryResponse>('/coin/trades', { params: { period: backendPeriod } });
    return data;
}
