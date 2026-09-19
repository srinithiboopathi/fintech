import { create } from 'zustand';
import { AssetType, BacktestResponse, AssetItem } from '../types';

interface AppState {
  selectedAsset: AssetType;
  setSelectedAsset: (asset: AssetType) => void;
  selectedDateRange: { start_date?: string; end_date?: string };
  setSelectedDateRange: (range: { start_date?: string; end_date?: string }) => void;
  lastBacktestResult: BacktestResponse | null;
  setLastBacktestResult: (result: BacktestResponse | null) => void;
  availableAssets: AssetItem[];
  setAvailableAssets: (assets: AssetItem[]) => void;
  backendHealthy: boolean | null;
  setBackendHealthy: (healthy: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedAsset: 'gold',
  setSelectedAsset: (asset) => set({ selectedAsset: asset }),
  selectedDateRange: {},
  setSelectedDateRange: (range) => set({ selectedDateRange: range }),
  lastBacktestResult: null,
  setLastBacktestResult: (result) => set({ lastBacktestResult: result }),
  availableAssets: [],
  setAvailableAssets: (assets) => set({ availableAssets: assets }),
  backendHealthy: null,
  setBackendHealthy: (healthy) => set({ backendHealthy: healthy }),
}));
