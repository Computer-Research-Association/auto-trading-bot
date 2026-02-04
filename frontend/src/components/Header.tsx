// src/components/Header.tsx
import React, { useState, useEffect } from "react";

export default function Header() {
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

    return (
        <header className="top-nav">
            <div className="nav-left">
                <div className="logo">GOLD BAR</div>
            </div>
            <div className="nav-right">
                <span className="nav-time">{formatTime(currentTime)}</span>
                <button className="nav-small">My Wallet</button>
            </div>
        </header>
    );
}
