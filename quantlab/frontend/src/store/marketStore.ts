import { create } from 'zustand';
import { AssetOverview, OHLCVBar } from '../types';
import { MarketApi } from '../services/marketApi';

interface MarketState {
  assets: AssetOverview[];
  selectedSymbol: string;
  selectedAsset: AssetOverview | null;
  historicalBars: OHLCVBar[];
  isLoading: boolean;
  timeframe: string;
  loadAssets: () => Promise<void>;
  setSelectedSymbol: (symbol: string) => void;
  loadHistoricalBars: (symbol: string) => Promise<void>;
}

export const useMarketStore = create<MarketState>((set, get) => ({
  assets: [],
  selectedSymbol: 'NVDA',
  selectedAsset: null,
  historicalBars: [],
  isLoading: false,
  timeframe: '1D',

  loadAssets: async () => {
    set({ isLoading: true });
    try {
      const assets = await MarketApi.getAssets();
      const currentSym = get().selectedSymbol;
      const asset = assets.find((a) => a.symbol === currentSym) || assets[0];
      set({ assets, selectedAsset: asset, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  setSelectedSymbol: (symbol: string) => {
    const asset = get().assets.find((a) => a.symbol === symbol) || null;
    set({ selectedSymbol: symbol, selectedAsset: asset });
    get().loadHistoricalBars(symbol);
  },

  loadHistoricalBars: async (symbol: string) => {
    set({ isLoading: true });
    try {
      const bars = await MarketApi.getHistoricalBars(symbol);
      set({ historicalBars: bars, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },
}));
