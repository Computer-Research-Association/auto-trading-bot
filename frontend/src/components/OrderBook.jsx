import React, { useState, useEffect } from "react";
import { fetchOrderBook } from "../api"; // API 불러오기
import "./OrderBook.css"; // 스타일 파일

export default function OrderBook() {
  const [orderBook, setOrderBook] = useState(null);

  useEffect(() => {
    // 데이터 가져오기 실행
    const getData = async () => {
      const data = await fetchOrderBook();
      setOrderBook(data);
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
            <div className="col-size">{unit.ask_size}</div>
          </div>
        ))}

        {/* 매수 물량 (Bid) - 빨간색 영역 */}
        {orderBook.orderbook_units.map((unit, index) => (
          <div className="row bid-row" key={`bid-${index}`}>
            <div className="col-price price-up">{unit.bid_price.toLocaleString()}</div>
            <div className="col-size">{unit.bid_size}</div>
          </div>
        ))}
      </div>
    </div>
  );
}