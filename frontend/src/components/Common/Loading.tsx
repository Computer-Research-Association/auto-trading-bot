import React from 'react';
import './Loading.css';

interface LoadingProps {
    message?: string;
    subMessage?: string;
}

const Loading: React.FC<LoadingProps> = ({
    message = "데이터를 불러오는 중입니다...",
    subMessage = "귀여운 아기 돼지가 정보를 가져오고 있으니 잠시만 기다려 주세요! 🐷✨"
}) => {
    return (
        <div className="loading-container">
            <div className="loading-content">
                <img src="/loading_piggy.svg" alt="Loading Piggy" className="loading-piggy" />
                <div className="loading-text">{message}</div>
                <div className="loading-subtext">{subMessage}</div>
            </div>
        </div>
    );
};

export default Loading;
