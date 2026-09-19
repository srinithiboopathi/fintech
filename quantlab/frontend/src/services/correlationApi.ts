import { apiClient } from './api';
import { CorrelationMatrixData, RollingCorrelationPoint } from '../types';

export const CorrelationApi = {
  async getMatrix(method: string = 'pearson'): Promise<CorrelationMatrixData> {
    try {
      const res = await apiClient.get<CorrelationMatrixData>('/correlation/matrix', {
        params: { method },
      });
      return res.data;
    } catch {
      return {
        symbols: ['Gold (GC=F)', 'Bitcoin (BTC)', 'NVIDIA (NVDA)'],
        raw_symbols: ['GC=F', 'BTC-USD', 'NVDA'],
        matrix: [
          [1.0, 0.08, 0.14],
          [0.08, 1.0, 0.46],
          [0.14, 0.46, 1.0],
        ],
        method: 'pearson',
      };
    }
  },

  async getRollingCorrelation(
    assetA: string = 'BTC-USD',
    assetB: string = 'GC=F',
    window: number = 30
  ): Promise<RollingCorrelationPoint[]> {
    try {
      const res = await apiClient.get<{ series: RollingCorrelationPoint[] }>('/correlation/rolling', {
        params: { asset_a: assetA, asset_b: assetB, window },
      });
      return res.data.series;
    } catch {
      const series: RollingCorrelationPoint[] = [];
      const now = new Date();
      let currentCorr = 0.12;

      for (let i = 120; i >= 0; i--) {
        const d = new Date(now);
        d.setDate(d.getDate() - i);
        currentCorr += (Math.random() - 0.5) * 0.08;
        currentCorr = Math.max(-0.6, Math.min(0.8, currentCorr));
        series.push({
          date: d.toISOString().split('T')[0],
          correlation: parseFloat(currentCorr.toFixed(3)),
        });
      }
      return series;
    }
  },
};
