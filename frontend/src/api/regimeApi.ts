import { apiClient } from "../lib/api";
import { RegimeResponse } from "../types";

export const regimeApi = {
  getMarketRegimes: async (
    asset: string,
    params?: {
      trend_window?: number;
      volatility_window?: number;
      threshold_mode?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<RegimeResponse> => {
    const res = await apiClient.get<RegimeResponse>(`/regimes/${asset}`, {
      params,
    });
    return res.data;
  },
};
