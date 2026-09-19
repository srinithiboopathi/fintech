import { apiClient } from "../lib/api";
import { PortfolioAnalysisRequest, PortfolioAnalysisResponse } from "../types";

export const portfolioApi = {
  analyzePortfolio: async (payload: PortfolioAnalysisRequest): Promise<PortfolioAnalysisResponse> => {
    const res = await apiClient.post<PortfolioAnalysisResponse>("/portfolio/analyze", payload);
    return res.data;
  },
};
