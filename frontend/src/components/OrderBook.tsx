import React, { useState, useEffect } from "react";
import { fetchOrderBook } from "../../api"; // 경로 확인 필요 (components/OrderBook이므로 ../../api)
import "./OrderBook.css";

interface OrderBookUnit {
    ask_price: number;
    bid_price: number;
    ask_size: number;
    bid_size: number;
}

interface OrderBookData {
    market: string;
    timestamp: number;
    total_ask_size: number;
    total_bid_size: number;
    orderbook_units: OrderBookUnit[];
}

export default function OrderBook() {
    const [orderBook, setOrderBook] = useState<OrderBookData | null>(null);

    useEffect(() => {
        const getData = async () => {
            try {
                // api.js가 아직 js라면 타입 에러가 날 수 있으니 any로 처리하거나 api.ts로 변환 필요하지만
                // 일단은 호환성을 위해 그대로 사용
                const data = await fetchOrderBook();
                setOrderBook(data);
            } catch (e) {
                console.error("Failed to fetch orderbook", e);
            }
        };
        getData();
    }, []);

    if (!orderBook) return <div className="loading">로딩중...</div>;

    return (
        <div className="orderbook-container">
            <h3 className="title">호가창 ({orderBook.market})</h3>

            <div className="orderbook-table">
                {/* 매도 물량 (Ask) - 파란색 영역 (순서 뒤집어서 높은 가격이 위로 가게) */}
                {[...orderBook.orderbook_units].reverse().map((unit, index) => (
                    <div className="row ask-row" key={`ask-${index}`}>
                        <div className="col-price price-down">{unit.ask_price.toLocaleString()}</div>
                        <div className="col-size">{unit.ask_size.toFixed(3)}</div>
                    </div>
                ))}

                {/* 매수 물량 (Bid) - 빨간색 영역 */}
                {orderBook.orderbook_units.map((unit, index) => (
                    <div className="row bid-row" key={`bid-${index}`}>
                        <div className="col-price price-up">{unit.bid_price.toLocaleString()}</div>
                        <div className="col-size">{unit.bid_size.toFixed(3)}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}
