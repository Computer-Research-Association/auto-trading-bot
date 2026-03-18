import { api } from './api';

// Define the types based on Assets.tsx
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

export async function getAssets(): Promise<PortfolioAssetsResponse> {
    // Based on the logs, the endpoint seems to be '/portfolio/assets'
    // URL: https://gold.cra206.org/api/portfolio/assets
    const { data } = await api.get<PortfolioAssetsResponse>('/portfolio/assets');
    return data;
}
