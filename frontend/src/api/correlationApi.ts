import { apiClient } from "../lib/api";
import {
  CorrelationMatrixResponse,
  PairCorrelationResponse,
  RollingCorrelationResponse,
  AssetComparisonResponse,
} from "../types";

export const correlationApi = {
  getCorrelationMatrix: async (params?: {
    assets?: string[];
    start_date?: string;
    end_date?: string;
  }): Promise<CorrelationMatrixResponse> => {
    const res = await apiClient.get<CorrelationMatrixResponse>("/correlation/matrix", {
      params,
    });
    return res.data;
  },

  getPairCorrelation: async (params: {
    asset_a: string;
    asset_b: string;
    start_date?: string;
    end_date?: string;
  }): Promise<PairCorrelationResponse> => {
    const res = await apiClient.get<PairCorrelationResponse>("/correlation/pair", {
      params,
    });
    return res.data;
  },

  getRollingCorrelation: async (params: {
    asset_a: string;
    asset_b: string;
    window?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<RollingCorrelationResponse> => {
    const res = await apiClient.get<RollingCorrelationResponse>("/correlation/rolling", {
      params,
    });
    return res.data;
  },

  getAssetComparison: async (params?: {
    assets?: string[];
    start_date?: string;
    end_date?: string;
    risk_free_rate?: number;
  }): Promise<AssetComparisonResponse> => {
    const res = await apiClient.get<AssetComparisonResponse>("/correlation/comparison", {
      params,
    });
    return res.data;
  },
};
