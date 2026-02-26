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
                <div className="logo">
                    {/* 아주 귀엽고 사랑스러운 핑크 돼지 저금통 멀티컬러 SVG */}
                    <svg width="38" height="38" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="logo-icon">
                        {/* 귀 */}
                        <path d="M22 18L14 8C14 8 10 14 16 22L22 18Z" fill="#FFAEC9"/>
                        <path d="M42 18L50 8C50 8 54 14 48 22L42 18Z" fill="#FFAEC9"/>
                        <path d="M21 19L15 11C15 11 12 15 17 21L21 19Z" fill="#F48FB1"/>
                        <path d="M43 19L49 11C49 11 52 15 47 21L43 19Z" fill="#F48FB1"/>
                        {/* 다리 */}
                        <rect x="18" y="44" width="8" height="12" rx="4" fill="#FFAEC9"/>
                        <rect x="38" y="44" width="8" height="12" rx="4" fill="#FFAEC9"/>
                        <rect x="26" y="46" width="6" height="8" rx="3" fill="#F48FB1"/>
                        <rect x="44" y="42" width="6" height="8" rx="3" fill="#F48FB1"/>
                        {/* 꼬리 */}
                        <path d="M54 36C58 34 58 28 54 28" stroke="#FFAEC9" strokeWidth="3" strokeLinecap="round"/>
                        {/* 몸통 */}
                        <circle cx="32" cy="32" r="22" fill="#FFC0CB"/>
                        {/* 동전 구멍 */}
                        <rect x="25" y="14" width="14" height="3" rx="1.5" fill="#D81B60"/>
                        {/* 눈 */}
                        <circle cx="24" cy="28" r="2.5" fill="#424242"/>
                        <circle cx="40" cy="28" r="2.5" fill="#424242"/>
                        <circle cx="23" cy="27" r="1" fill="#FFFFFF"/>
                        <circle cx="39" cy="27" r="1" fill="#FFFFFF"/>
                        {/* 코 (돼지코) */}
                        <ellipse cx="32" cy="36" rx="8" ry="6" fill="#F48FB1"/>
                        <circle cx="29" cy="36" r="1.5" fill="#D81B60"/>
                        <circle cx="35" cy="36" r="1.5" fill="#D81B60"/>
                        {/* 볼터치 */}
                        <ellipse cx="18" cy="34" rx="3" ry="2" fill="#FF8A80" opacity="0.6"/>
                        <ellipse cx="46" cy="34" rx="3" ry="2" fill="#FF8A80" opacity="0.6"/>
                    </svg>
                    <span>GOLD BAR</span>
                </div>
            </div>
            <div className="nav-right">
                <span className="nav-time">{formatTime(currentTime)}</span>
                <button className="nav-small">My Wallet</button>
            </div>
        </header>
    );
}
