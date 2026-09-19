import React from 'react';
import { ShieldAlert, Shuffle } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const RobustnessLabPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#111722] border border-[#232E42] rounded-lg p-5 flex items-center justify-between shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white">Robustness & Stress Testing Lab</h1>
              <Badge variant="cyan" size="xs">Phase 11 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Stress-test trading strategies against parameter overfitting, random price permutations, and Monte Carlo resampling.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Robustness Lab"
        description="The Robustness Lab will be delivered in Phase 11. It evaluates parameter sensitivity heatmaps and Monte Carlo confidence intervals to identify brittle or overfitted strategies."
        phase={11}
        icon={<Shuffle className="w-7 h-7 text-cyan-400" />}
        details={[
          'Parameter Sensitivity Heatmaps (e.g. Fast SMA vs Slow SMA matrix)',
          'Monte Carlo Bootstrapping and Return Resampling',
          '95% & 99% Value at Risk (VaR) / Expected Shortfall (CVaR)',
          'Overfitting Diagnostics & Stability Score'
        ]}
      />
    </div>
  );
};
