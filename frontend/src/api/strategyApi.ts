import { apiClient } from "../lib/api";
import { StrategyResponse, StrategyInfoListResponse } from "../types";

export const strategyApi = {
  getAvailableStrategies: async (): Promise<StrategyInfoListResponse> => {
    const res = await apiClient.get<StrategyInfoListResponse>("/strategies/catalog");
    return res.data;
  },

  getStrategySignals: async (
    asset: string,
    strategy: string,
    params?: {
      start_date?: string;
      end_date?: string;
      fast_period?: number;
      slow_period?: number;
      short_period?: number;
      long_period?: number;
      lookback?: number;
      window?: number;
      threshold?: number;
      [key: string]: any;
    }
  ): Promise<StrategyResponse> => {
    const res = await apiClient.get<StrategyResponse>(`/strategies/${asset}/${strategy}`, {
      params,
    });
    return res.data;
  },
};
