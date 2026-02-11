import { api } from './api';

export type Strategy = 'All Strategy' | 'Moving Average' | 'RSI Oversold' | 'Bollinger band';
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

export async function getHistory(): Promise<History[]> {
    // 로그 기반 엔드포인트: /api/trades/history (apiClient에 base URL이 있으므로 /trades/history)
    const { data } = await api.get<History[]>('/trades/history');
    return data;
}
