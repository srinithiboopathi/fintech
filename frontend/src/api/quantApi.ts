import { apiClient } from "../lib/api";
import {
  IndicatorResponse,
  ReturnsResponse,
  VolatilityResponse,
  RiskMetricsResponse,
  RollingPerformanceResponse,
  AssetQuantSummaryResponse,
} from "../types";

export const quantApi = {
  getIndicators: async (
    asset: string,
    params?: { sma_period?: number; ema_period?: number; start_date?: string; end_date?: string }
  ): Promise<IndicatorResponse> => {
    const res = await apiClient.get<IndicatorResponse>(`/quant/indicators/${asset}`, {
      params,
    });
    return res.data;
  },

  getReturns: async (
    asset: string,
    params?: { start_date?: string; end_date?: string }
  ): Promise<ReturnsResponse> => {
    const res = await apiClient.get<ReturnsResponse>(`/quant/returns/${asset}`, {
      params,
    });
    return res.data;
  },

  getVolatility: async (
    asset: string,
    params?: { window?: number; start_date?: string; end_date?: string }
  ): Promise<VolatilityResponse> => {
    const res = await apiClient.get<VolatilityResponse>(`/quant/volatility/${asset}`, {
      params,
    });
    return res.data;
  },

  getRiskMetrics: async (
    asset: string,
    params?: { start_date?: string; end_date?: string; risk_free_rate?: number }
  ): Promise<RiskMetricsResponse> => {
    const res = await apiClient.get<RiskMetricsResponse>(`/quant/risk-metrics/${asset}`, {
      params,
    });
    return res.data;
  },

  getRollingPerformance: async (
    asset: string,
    params?: { window?: number; start_date?: string; end_date?: string; risk_free_rate?: number }
  ): Promise<RollingPerformanceResponse> => {
    const res = await apiClient.get<RollingPerformanceResponse>(`/quant/rolling/${asset}`, {
      params,
    });
    return res.data;
  },

  getAssetSummary: async (
    asset: string,
    params?: { start_date?: string; end_date?: string; risk_free_rate?: number }
  ): Promise<AssetQuantSummaryResponse> => {
    const res = await apiClient.get<AssetQuantSummaryResponse>(`/quant/summary/${asset}`, {
      params,
    });
    return res.data;
  },
};
