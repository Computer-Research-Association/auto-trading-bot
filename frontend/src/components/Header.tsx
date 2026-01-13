// src/components/Header.tsx
import React, { useState, useEffect } from "react";
// CSS가 필요하면 별도로 만드셔도 되고, 공통 CSS를 쓴다면 그대로 둡니다.

export default function Header() {
  // --- 시계 로직 이동 ---
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    });
  };
  // --------------------

  return (
    <header className="top-nav">
      <div className="nav-left">
        <div className="logo">Gold bar</div>
      </div>
      <div className="nav-right">
        <span className="nav-time">{formatTime(currentTime)}</span>
        <button className="nav-small">My</button>
      </div>
    </header>
  );
}