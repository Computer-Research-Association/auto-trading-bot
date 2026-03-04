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

export async function getHistory(): Promise<HistoryResponse> {
    // 로그 기반 엔드포인트: /api/coin/trades (apiClient에 base URL이 있으므로 /coin/trades)
    const { data } = await api.get<HistoryResponse>('/coin/trades');
    return data;
}
