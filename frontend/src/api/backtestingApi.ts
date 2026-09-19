import { apiClient } from "../lib/api";
import { BacktestRequest, BacktestResponse, StrategyInfoListResponse } from "../types";

export const backtestingApi = {
  getBacktestStrategies: async (): Promise<StrategyInfoListResponse> => {
    const res = await apiClient.get<StrategyInfoListResponse>("/backtesting/strategies");
    return res.data;
  },

  runBacktest: async (payload: BacktestRequest): Promise<BacktestResponse> => {
    const res = await apiClient.post<BacktestResponse>("/backtesting/run", payload);
    return res.data;
  },
};
