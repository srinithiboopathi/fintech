import React from 'react';
import { Gauge } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const MarketRegimesPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex items-center justify-between shadow-xl quant-glass">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Gauge className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white">Market Regime Classification</h1>
              <Badge variant="cyan" size="xs">Phase 12 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Classify market environments across Bullish, Bearish, Sideways, and Volatility states.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Market Regime Analysis"
        description="The Market Regime Analysis module will be implemented in Phase 12. It measures strategy performance across distinct macroeconomic and volatility regimes."
        phase={12}
        icon={<Gauge className="w-6 h-6 text-cyan-400" />}
        details={[
          'Volatility Regimes (Low Volatility vs High Volatility Clustering)',
          'Trend Regimes (Bullish Expansion vs Bearish Contraction vs Range-Bound)',
          'Conditional Strategy Performance by Market State',
          'Regime Transition Probability Matrix'
        ]}
      />
    </div>
  );
};
