import { create } from 'zustand';
import { AssetType, BacktestResponse, AssetItem, User } from '../types';

interface AppState {
  // Authentication state
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isDemo: boolean;
  setAuth: (user: User, token: string) => void;
  setDemoAuth: () => void;
  logout: () => void;

  // Quantitative state
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

// Initial state from localStorage
const storedToken = localStorage.getItem('quantlab_token');
const storedUser = localStorage.getItem('quantlab_user');
const isDemoSession = localStorage.getItem('quantlab_is_demo') === 'true';

let initialUser: User | null = null;
if (storedUser) {
  try {
    initialUser = JSON.parse(storedUser);
  } catch {
    initialUser = null;
  }
}

const initialIsAuthenticated = Boolean((storedToken && initialUser) || isDemoSession);

export const useAppStore = create<AppState>((set) => ({
  // Auth state
  user: initialUser,
  token: storedToken,
  isAuthenticated: initialIsAuthenticated,
  isDemo: isDemoSession,

  setAuth: (user: User, token: string) => {
    localStorage.setItem('quantlab_token', token);
    localStorage.setItem('quantlab_user', JSON.stringify(user));
    localStorage.removeItem('quantlab_is_demo');
    set({
      user,
      token,
      isAuthenticated: true,
      isDemo: false,
    });
  },

  setDemoAuth: () => {
    const demoUser: User = {
      id: 0,
      email: 'demo.analyst@quantlab.local',
      full_name: 'Demo Analyst',
      is_active: true,
      created_at: new Date().toISOString(),
    };
    localStorage.setItem('quantlab_is_demo', 'true');
    localStorage.setItem('quantlab_user', JSON.stringify(demoUser));
    localStorage.removeItem('quantlab_token');
    set({
      user: demoUser,
      token: null,
      isAuthenticated: true,
      isDemo: true,
    });
  },

  logout: () => {
    localStorage.removeItem('quantlab_token');
    localStorage.removeItem('quantlab_user');
    localStorage.removeItem('quantlab_is_demo');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isDemo: false,
      lastBacktestResult: null,
    });
  },

  // Quantitative state
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

