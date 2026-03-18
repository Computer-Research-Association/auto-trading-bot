import { api } from './api';

export interface OrderBookUnit {
    ask_price: number;
    bid_price: number;
    ask_size: number;
    bid_size: number;
}

export interface OrderBookData {
    market: string;
    timestamp: number;
    total_ask_size: number;
    total_bid_size: number;
    orderbook_units: OrderBookUnit[];
}

export async function getOrderBook(symbol: string = 'KRW-BTC'): Promise<OrderBookData> {
    // 예상 엔드포인트: /orderbook
    const { data } = await api.get<OrderBookData>('/orderbook', {
        params: { symbol }
    });
    return data;
}
