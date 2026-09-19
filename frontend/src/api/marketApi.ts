import { apiClient } from "../lib/api";
import {
  AssetListResponse,
  AssetMetadataResponse,
  MultiAssetDateRangeResponse,
  HistoricalDataResponse,
  MultiAssetHistoricalDataResponse,
} from "../types";

export const marketApi = {
  getAssets: async (): Promise<AssetListResponse> => {
    const res = await apiClient.get<AssetListResponse>("/market/assets");
    return res.data;
  },

  getAssetMetadata: async (asset: string): Promise<AssetMetadataResponse> => {
    const res = await apiClient.get<AssetMetadataResponse>(`/market/metadata/${asset}`);
    return res.data;
  },

  getDateRanges: async (): Promise<MultiAssetDateRangeResponse> => {
    const res = await apiClient.get<MultiAssetDateRangeResponse>("/market/date-ranges");
    return res.data;
  },

  getAssetHistory: async (
    asset: string,
    params?: { start_date?: string; end_date?: string; limit?: number }
  ): Promise<HistoricalDataResponse> => {
    const res = await apiClient.get<HistoricalDataResponse>(`/market/history/${asset}`, {
      params,
    });
    return res.data;
  },

  getMultiAssetHistory: async (params?: {
    assets?: string[];
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<MultiAssetHistoricalDataResponse> => {
    const res = await apiClient.get<MultiAssetHistoricalDataResponse>("/market/history", {
      params,
    });
    return res.data;
  },
};
