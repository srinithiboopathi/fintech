import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { AssetSelector } from '../components/market/AssetSelector';
import { MetricCard } from '../components/market/MetricCard';
import { PriceChart } from '../components/charts/PriceChart';
import { IndicatorChart } from '../components/charts/IndicatorChart';
import { Card } from '../components/ui/Card';
import { useMarketData } from '../hooks/useMarketData';
import { AnalyticsApi } from '../services/analyticsApi';
import { RiskMetrics, IndicatorData } from '../types';
import { formatPercent, formatNumber } from '../../utils/formatters';
import { Activity, ShieldCheck, TrendingUp, AlertTriangle } from 'lucide-react';

export const MarketAnalysis: React.FC = () => {
  const { assets, selectedSymbol, setSelectedSymbol, historicalBars } = useMarketData();
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [indicators, setIndicators] = useState<IndicatorData | null>(null);

  useEffect(() => {
    if (selectedSymbol) {
      AnalyticsApi.getRiskMetrics(selectedSymbol).then(setRiskMetrics);
      AnalyticsApi.getIndicators(selectedSymbol).then(setIndicators);
    }
  }, [selectedSymbol]);

  return (
    <PageContainer
      title="Multi-Asset Technical & Risk Terminal"
      subtitle="Institutional-grade OHLCV candlestick visualizer and statistical factor decomposition"
      actions={
        <AssetSelector
          assets={assets}
          selectedSymbol={selectedSymbol}
          onSelect={setSelectedSymbol}
        />
      }
    >
      <div className="space-y-6">
        {/* Risk Profile Top Metrics */}
        {riskMetrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              label="CAGR"
              value={formatPercent(riskMetrics.cagr, 2, false)}
              subValue={`Vol: ${formatPercent(riskMetrics.annualized_volatility, 1, false)}`}
              icon={<TrendingUp className="w-4 h-4" />}
            />
            <MetricCard
              label="Sharpe / Sortino"
              value={riskMetrics.sharpe_ratio.toFixed(2)}
              subValue={`Sortino: ${riskMetrics.sortino_ratio.toFixed(2)}`}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              label="Historical VaR (95%)"
              value={formatPercent(riskMetrics.var_95, 2, false)}
              subValue={`CVaR: ${formatPercent(riskMetrics.cvar_95, 2, false)}`}
              icon={<ShieldCheck className="w-4 h-4" />}
            />
            <MetricCard
              label="Benchmark Beta"
              value={riskMetrics.beta_to_sp500.toFixed(2)}
              subValue={`Alpha: +${riskMetrics.alpha_annualized.toFixed(1)}%`}
              icon={<AlertTriangle className="w-4 h-4" />}
            />
          </div>
        )}

        {/* Main Price Action Candlestick Chart */}
        <PriceChart
          bars={historicalBars}
          title={`${selectedSymbol} Candlestick & Trading Volume Matrix`}
          height={380}
        />

        {/* Sub-Chart: Technical Oscillators */}
        <IndicatorChart indicators={indicators} height={200} />

        {/* Deep Dive Statistical Risk Factor Table */}
        {riskMetrics && (
          <Card variant="glass" className="p-5 border border-slate-800">
            <h3 className="text-sm font-bold text-slate-200 mb-3 font-mono">
              Statistical Factor & Tail Risk Attribution ({selectedSymbol})
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Calmar Ratio</span>
                <span className="text-slate-100 font-bold text-sm">{riskMetrics.calmar_ratio.toFixed(2)}</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Max Historical DD</span>
                <span className="text-rose-400 font-bold text-sm">-{riskMetrics.max_drawdown.toFixed(1)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">VaR 99% (1-Day)</span>
                <span className="text-slate-100 font-bold text-sm">{riskMetrics.var_99.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Jensen's Alpha</span>
                <span className="text-emerald-400 font-bold text-sm">+{riskMetrics.alpha_annualized.toFixed(2)}%</span>
              </div>
            </div>
          </Card>
        )}
      </div>
    </PageContainer>
  );
};
