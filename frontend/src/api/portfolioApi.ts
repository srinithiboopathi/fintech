import { apiClient } from "../lib/api";
import {
  PortfolioAnalysisRequest,
  PortfolioAnalysisResponse,
  PortfolioOptimizationRequest,
  PortfolioOptimizationResponse,
} from "../types";

export const portfolioApi = {
  analyzePortfolio: async (payload: PortfolioAnalysisRequest): Promise<PortfolioAnalysisResponse> => {
    const res = await apiClient.post<PortfolioAnalysisResponse>("/portfolio/analyze", payload);
    return res.data;
  },
  optimizePortfolio: async (payload: PortfolioOptimizationRequest): Promise<PortfolioOptimizationResponse> => {
    const res = await apiClient.post<PortfolioOptimizationResponse>("/portfolio/optimize", payload);
    return res.data;
  },
};
