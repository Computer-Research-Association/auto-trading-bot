import {mockOrderBook} from "./mocks/mockOrderBook";

export const fetchOrderBook = () => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(mockOrderBook);
        }, 300); // 0.3초 딜레이 흉내내기
    });
};