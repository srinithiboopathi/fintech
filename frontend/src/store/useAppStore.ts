import { create } from 'zustand';
import { AssetType } from '../types';

interface AppState {
  selectedAsset: AssetType;
  setSelectedAsset: (asset: AssetType) => void;
  backendHealthy: boolean | null;
  setBackendHealthy: (healthy: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedAsset: 'gold',
  setSelectedAsset: (asset) => set({ selectedAsset: asset }),
  backendHealthy: null,
  setBackendHealthy: (healthy) => set({ backendHealthy: healthy }),
}));
