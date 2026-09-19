import React from 'react';
import { TrendingUp, BarChart2 } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';
import { useAppStore } from '../store/useAppStore';

export const MarketAnalysisPage: React.FC = () => {
  const { selectedAsset } = useAppStore();

  const assetLabels: Record<string, { name: string; badge: 'gold' | 'btc' | 'nvda' }> = {
    gold: { name: 'Gold (Safe Haven)', badge: 'gold' },
    bitcoin: { name: 'Bitcoin (BTC-USD)', badge: 'btc' },
    nvidia: { name: 'NVIDIA Corporation (NVDA)', badge: 'nvda' },
  };

  const current = assetLabels[selectedAsset];

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex items-center justify-between shadow-xl quant-glass">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white">Market Analysis & Price Action</h1>
              <Badge variant={current.badge} size="xs">{selectedAsset.toUpperCase()}</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Interactive time-series OHLCV analysis and mathematical indicator overlays.
            </p>
          </div>
        </div>
        <Badge variant="cyan" size="sm">Phase 5 Target</Badge>
      </div>

      {/* Structural Empty State */}
      <EmptyState
        title="Market Analysis Module"
        description="Market Analysis will be available in Phase 5 after Kaggle dataset ingestion (Phase 2) and Python quantitative indicator engine integration (Phases 3 & 4)."
        phase={5}
        icon={<BarChart2 className="w-6 h-6 text-cyan-400" />}
        details={[
          'Interactive Apache ECharts Candlestick & Volume chart',
          'Fast / Slow Simple Moving Averages (SMA) & Exponential Moving Averages (EMA)',
          'Daily Arithmetic and Compounded Cumulative Returns',
          'Historical & Annualized Volatility with rolling windows',
          'Sharpe Ratio & Peak-to-Trough Maximum Drawdown calculation'
        ]}
      />
    </div>
  );
};
