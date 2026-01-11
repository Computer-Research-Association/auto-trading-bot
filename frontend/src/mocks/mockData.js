// Order book
export const mockOrderBook = {
    market: "KRW-BTC",
    timestamp: 170469800000,
    total_ask_size: 1.5,
    total_bid_size: 2.3,
    orderbook_units: [
        { ask_price: 65000000, bid_price: 6499000, ask_size: 0.1, bid_size: 0.05 },
        { ask_price: 65001000, bid_price: 6498000, ask_size: 0.5, bid_size: 0.12 },
        { ask_price: 65002000, bid_price: 6497000, ask_size: 1.2, bid_size: 0.33 },
        { ask_price: 65003000, bid_price: 6496000, ask_size: 0.01, bid_size: 0.8 },
        { ask_price: 65004000, bid_price: 6495000, ask_size: 0.05, bid_size: 1.5 },
    ]
};

// Assets
export const mockAssets = [
    { currency: "KRW", balance: "1000000", avg_buy_price: "0"},
    { currency: "BTC", balance: "0.05", avg_buy_price: "60000000"},
    { currency: "ETH", balance: "2.5", avg_buy_price: "3500000"},
];