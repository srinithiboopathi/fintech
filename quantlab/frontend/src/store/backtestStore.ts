import { create } from 'zustand';
import { StrategyInfo, BacktestRequest, BacktestResult } from '../types';
import { BacktestApi } from '../services/backtestApi';

interface BacktestState {
  strategies: StrategyInfo[];
  selectedStrategyId: string;
  activeResult: BacktestResult | null;
  isRunning: boolean;
  history: BacktestResult[];
  loadStrategies: () => Promise<void>;
  setSelectedStrategyId: (id: string) => void;
  runSimulation: (req: BacktestRequest) => Promise<BacktestResult>;
}

export const useBacktestStore = create<BacktestState>((set, get) => ({
  strategies: [],
  selectedStrategyId: 'sma_crossover',
  activeResult: null,
  isRunning: false,
  history: [],

  loadStrategies: async () => {
    try {
      const list = await BacktestApi.getStrategies();
      set({ strategies: list });
    } catch (e) {
      console.error(e);
    }
  },

  setSelectedStrategyId: (id: string) => {
    set({ selectedStrategyId: id });
  },

  runSimulation: async (req: BacktestRequest) => {
    set({ isRunning: true });
    try {
      const result = await BacktestApi.runBacktest(req);
      set((state) => ({
        activeResult: result,
        history: [result, ...state.history].slice(0, 10),
        isRunning: false,
      }));
      return result;
    } catch (e) {
      set({ isRunning: false });
      throw e;
    }
  },
}));
