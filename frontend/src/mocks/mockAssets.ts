export type AssetItem = {
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  evaluation_krw: number;
};

export type PortfolioSummary = {
  krw_total: number;
  krw_available: number;
  total_buy_krw: number;
  total_assets_krw: number;
  total_pnl_krw: number;
  total_pnl_rate: number;
};

export type PortfolioAssetsResponse = {
  summary: PortfolioSummary;
  items: AssetItem[];
};

export const mockAssets: PortfolioAssetsResponse = {
  summary: {
    krw_total: 5000000,
    krw_available: 4500000,
    total_buy_krw: 15000000,
    total_assets_krw: 18250000,
    total_pnl_krw: 3250000,
    total_pnl_rate: 21.67,
  },
  items: [
    {
      symbol: "BTC",
      quantity: 0.05,
      avg_buy_price: 60000000,
      current_price: 65000000,
      evaluation_krw: 3250000,
    },
    {
      symbol: "ETH",
      quantity: 2.5,
      avg_buy_price: 3500000,
      current_price: 4000000,
      evaluation_krw: 10000000,
    },
  ],
};