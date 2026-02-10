export type PerfSummary = {
    period_label: string;
    pnl_krw: number;
    pnl_rate: number;
    start_assets_krw: number;
    end_assets_krw: number;
    total_assets_krw: number;  // 총 자산
    today_change_krw: number;  // 당일 변동 금액
    today_change_rate: number; // 당일 변동률
};

export type PerfChartPoint = {
    date: string;
    pnl_krw: number;
    assets_krw: number;
};

export type PerfDailyRow = {
    date: string;
    pnl_krw: number;
    pnl_rate: number;
    assets_krw: number;
};

export type PerfResponse = {
    summary: PerfSummary;
    chart: PerfChartPoint[];
    daily: PerfDailyRow[];
};

export const mockPerformance: PerfResponse = {
    summary: {
        period_label: "30일",
        pnl_krw: 3250000,
        pnl_rate: 21.67,
        start_assets_krw: 15000000,
        end_assets_krw: 18250000,
        total_assets_krw: 125000000,
        today_change_krw: -120000,
        today_change_rate: -0.1,
    },
    chart: [
        { date: "2026-01-10", pnl_krw: -1500000, assets_krw: 13500000 },
        { date: "2026-01-15", pnl_krw: -500000, assets_krw: 14500000 },
        { date: "2026-01-20", pnl_krw: 800000, assets_krw: 15800000 },
        { date: "2026-01-25", pnl_krw: -250000, assets_krw: 14750000 },
        { date: "2026-01-30", pnl_krw: 1200000, assets_krw: 16200000 },
        { date: "2026-02-04", pnl_krw: 3250000, assets_krw: 18250000 },
        { date: "2026-08-07", pnl_krw: 3240000, assets_krw: 18050000 },
        { date: "2026-12-09", pnl_krw: 9890000, assets_krw: 37950000 },
    ],
    daily: [
        { date: "2026-12-09", pnl_krw: 760000, pnl_rate: 0.87, assets_krw: 98760000 },
        { date: "2026-08-07", pnl_krw: 290000, pnl_rate: 1.76, assets_krw: 19220000 },
        { date: "2026-08-06", pnl_krw: 290000, pnl_rate: 1.66, assets_krw: 17220000 },
        { date: "2026-02-04", pnl_krw: 450000, pnl_rate: 2.53, assets_krw: 18250000 },
        { date: "2026-02-03", pnl_krw: 380000, pnl_rate: 2.19, assets_krw: 17800000 },
        { date: "2026-02-02", pnl_krw: 320000, pnl_rate: 1.87, assets_krw: 17420000 },
        { date: "2026-01-31", pnl_krw: -120000, pnl_rate: -0.68, assets_krw: 17100000 },
        { date: "2026-01-30", pnl_krw: 280000, pnl_rate: 1.66, assets_krw: 17220000 },
    ],
};
