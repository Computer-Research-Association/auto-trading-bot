import React, {useState} from 'react';

// 구조체 인터페이스 선언
interface Auto_Strategy {
    strategyName: string;
    strategyDescription: string;
    rateofreturn: number;
    transaction: number;
}

// 이게 데이터 선언하는 방법이다.
const types_strategies: Auto_Strategy[] = [
    {
        strategyName: "전략 1",
        strategyDescription: "이것저것 1",
        rateofreturn: +12.5,
        transaction: 30
    },
    {
        strategyName: "전략 2",
        strategyDescription: "이것저것 2",
        rateofreturn: +13,
        transaction: 60
    },
    {
        strategyName: "전략 3",
        strategyDescription: "이것저것 3",
        rateofreturn: -9.8,
        transaction: 45
    },
];

// useState는 기억장치 역할
const Auto_strategy = () => {
    const [r, setR] = useState<number>(0);
    const [t, setT] = useState<number>(0);

    // .map은 for문과 같다. 여기서 전략 이름, 설명, 수익률, 총 거래를 불러온다.
    return (
            <div className="main-panel">
    {types_strategies.map((strategy: Auto_Strategy) => (
      <div className="card" key={strategy.strategyName}>
        <h2>{strategy.strategyName}</h2>
        <p>{strategy.strategyDescription}</p>
        <div>수익률: {strategy.rateofreturn}%</div>
        <div>총 거래: {strategy.transaction}</div>
            </div> 
        ))}
    </div>
    );
};

export default Auto_strategy;