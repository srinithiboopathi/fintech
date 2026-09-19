import { apiClient } from './api';
import { AssetOverview, OHLCVBar } from '../types';

export const FALLBACK_ASSETS: AssetOverview[] = [
  {
    symbol: 'BTC-USD',
    name: 'Bitcoin Core',
    category: 'Digital Asset',
    current_price: 59150.0,
    change_24h: 3.45,
    volatility_30d: 0.54,
    sharpe_1y: 1.95,
    regime: 'High Volatility',
    volume_24h: 28500000000,
    high_52w: 73750.0,
    low_52w: 26800.0,
    sparkline: [56000, 57500, 59200, 58100, 61200, 60400, 59150],
  },
  {
    symbol: 'NVDA',
    name: 'NVIDIA Corporation',
    category: 'Equities',
    current_price: 129.8,
    change_24h: 2.45,
    volatility_30d: 0.42,
    sharpe_1y: 2.34,
    regime: 'Bull Trend',
    volume_24h: 225000000,
    high_52w: 140.76,
    low_52w: 41.2,
    sparkline: [115.0, 118.2, 121.3, 128.6, 120.5, 126.4, 129.8],
  },
  {
    symbol: 'GC=F',
    name: 'Gold Continuous Futures',
    category: 'Commodities',
    current_price: 2524.3,
    change_24h: 0.65,
    volatility_30d: 0.13,
    sharpe_1y: 1.28,
    regime: 'Bull Trend',
    volume_24h: 315000,
    high_52w: 2530.0,
    low_52w: 1827.0,
    sparkline: [2347, 2332, 2410, 2456, 2480, 2502, 2524],
  },
];

export function generateMockBars(symbol: string, days: number = 200): OHLCVBar[] {
  let basePrice = symbol.includes('BTC') ? 35000 : symbol.includes('NVDA') ? 25 : 1800;
  const drift = symbol.includes('NVDA') ? 0.003 : symbol.includes('BTC') ? 0.002 : 0.0005;
  const vol = symbol.includes('BTC') ? 0.035 : symbol.includes('NVDA') ? 0.025 : 0.008;

  const bars: OHLCVBar[] = [];
  const now = new Date();

  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];

    const ret = (Math.random() - 0.47) * vol + drift;
    const open = basePrice * (1 + (Math.random() - 0.5) * 0.005);
    const close = basePrice * (1 + ret);
    const high = Math.max(open, close) * (1 + Math.random() * vol * 0.5);
    const low = Math.min(open, close) * (1 - Math.random() * vol * 0.5);
    const volume = Math.floor(Math.random() * 50000000) + 1000000;

    bars.push({
      date: dateStr,
      symbol,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      adj_close: parseFloat(close.toFixed(2)),
      volume,
      daily_return: ret,
    });

    basePrice = close;
  }
  return bars;
}

export const MarketApi = {
  async getAssets(): Promise<AssetOverview[]> {
    try {
      const res = await apiClient.get<AssetOverview[]>('/market/assets');
      return res.data;
    } catch {
      return FALLBACK_ASSETS;
    }
  },

  async getHistoricalBars(symbol: string, startDate?: string, endDate?: string): Promise<OHLCVBar[]> {
    try {
      const res = await apiClient.get<{ bars: OHLCVBar[] }>(`/market/history/${symbol}`, {
        params: { start_date: startDate, end_date: endDate },
      });
      return res.data.bars;
    } catch {
      return generateMockBars(symbol, 220);
    }
  },
};
