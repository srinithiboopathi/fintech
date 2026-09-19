import { apiClient } from './api';
import { IndicatorData, RiskMetrics, RegimeDetectionResponse, MonteCarloResult } from '../types';

export const AnalyticsApi = {
  async getIndicators(symbol: string): Promise<IndicatorData> {
    try {
      const res = await apiClient.get<IndicatorData>(`/analytics/indicators/${symbol}`);
      return res.data;
    } catch {
      // Mock calculation for standalone frontend
      return {
        symbol,
        dates: [],
        sma_20: [],
        sma_50: [],
        ema_9: [],
        ema_21: [],
        rsi: [],
        bb_upper: [],
        bb_middle: [],
        bb_lower: [],
        macd: [],
        macd_signal: [],
        macd_hist: [],
        atr: [],
      };
    }
  },

  async getRiskMetrics(symbol: string): Promise<RiskMetrics> {
    try {
      const res = await apiClient.get<RiskMetrics>(`/analytics/risk/${symbol}`);
      return res.data;
    } catch {
      const isNvda = symbol.includes('NVDA');
      const isBtc = symbol.includes('BTC');
      return {
        symbol,
        cagr: isNvda ? 68.4 : isBtc ? 54.2 : 11.5,
        annualized_volatility: isBtc ? 54.0 : isNvda ? 42.0 : 13.0,
        sharpe_ratio: isNvda ? 2.34 : isBtc ? 1.95 : 1.28,
        sortino_ratio: isNvda ? 3.12 : isBtc ? 2.45 : 1.65,
        calmar_ratio: isNvda ? 2.15 : isBtc ? 1.48 : 0.88,
        max_drawdown: isBtc ? 52.4 : isNvda ? 38.6 : 14.2,
        max_drawdown_duration_days: 142,
        var_95: isBtc ? 4.8 : isNvda ? 3.6 : 1.2,
        var_99: isBtc ? 7.2 : isNvda ? 5.8 : 2.1,
        cvar_95: isBtc ? 6.5 : isNvda ? 4.9 : 1.8,
        beta_to_sp500: isNvda ? 1.65 : isBtc ? 1.35 : 0.12,
        alpha_annualized: isNvda ? 24.8 : isBtc ? 19.4 : 3.8,
      };
    }
  },

  async getRegimeDetection(symbol: string): Promise<RegimeDetectionResponse> {
    try {
      const res = await apiClient.get<RegimeDetectionResponse>(`/regimes/detect/${symbol}`);
      return res.data;
    } catch {
      return {
        symbol,
        current_regime: {
          date: '2024-09-02',
          regime: 'Bull Trend',
          volatility_rank: 'Moderate',
          trend_direction: 'Bullish',
          realized_volatility: 28.5,
          confidence: 0.88,
        },
        distribution_pct: {
          'Bull Trend': 48.5,
          'Bear Trend': 18.2,
          'Volatile Choppy': 21.3,
          'Consolidation': 12.0,
        },
        series: [],
      };
    }
  },

  async getMonteCarlo(symbol: string, simulations: number = 300, horizon: number = 252): Promise<MonteCarloResult> {
    try {
      const res = await apiClient.get<MonteCarloResult>(`/robustness/monte-carlo/${symbol}`, {
        params: { simulations, horizon },
      });
      return res.data;
    } catch {
      const initial = 100000;
      const p5: number[] = [initial];
      const p50: number[] = [initial];
      const p95: number[] = [initial];
      const samples: number[][] = [];

      for (let s = 0; s < 10; s++) {
        let eq = initial;
        const line = [initial];
        for (let i = 0; i < horizon; i++) {
          eq *= 1 + (Math.random() - 0.48) * 0.02;
          line.push(Math.round(eq));
        }
        samples.push(line);
      }

      let e5 = initial, e50 = initial, e95 = initial;
      for (let i = 0; i < horizon; i++) {
        e5 *= 0.9992;
        e50 *= 1.0006;
        e95 *= 1.0022;
        p5.push(Math.round(e5));
        p50.push(Math.round(e50));
        p95.push(Math.round(e95));
      }

      return {
        symbol,
        num_simulations: simulations,
        horizon_days: horizon,
        p5_equity_curve: p5,
        p50_equity_curve: p50,
        p95_equity_curve: p95,
        sample_trajectories: samples,
        metrics: {
          terminal_wealth_p5: Math.round(e5),
          terminal_wealth_p50: Math.round(e50),
          terminal_wealth_p95: Math.round(e95),
          max_drawdown_p5: 36.4,
          max_drawdown_p50: 18.2,
          max_drawdown_p95: 8.5,
          sharpe_p5: 0.65,
          sharpe_p50: 1.84,
          sharpe_p95: 2.95,
        },
      };
    }
  },
};
