import { apiClient } from "../lib/api";
import { RobustnessRequest, RobustnessResponse, StrategyInfoListResponse } from "../types";

export const robustnessApi = {
  getRobustnessStrategies: async (): Promise<StrategyInfoListResponse> => {
    const res = await apiClient.get<StrategyInfoListResponse>("/robustness/strategies");
    return res.data;
  },

  runRobustnessSweep: async (payload: RobustnessRequest): Promise<RobustnessResponse> => {
    const res = await apiClient.post<RobustnessResponse>("/robustness/run", payload);
    return res.data;
  },
};
