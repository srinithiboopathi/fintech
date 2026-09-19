import React from 'react';
import { GitMerge, Network } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const CorrelationLabPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex items-center justify-between shadow-xl quant-glass">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <GitMerge className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white">Cross-Asset Correlation Lab</h1>
              <Badge variant="cyan" size="xs">Phase 6 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Multi-asset covariance, Pearson correlation matrices, and rolling correlation windows across Gold, Bitcoin, and NVIDIA.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Cross-Asset Correlation Lab"
        description="The Correlation Lab will be activated in Phase 6. It computes pairwise Pearson correlations and rolling multi-window covariance matrices."
        phase={6}
        icon={<Network className="w-6 h-6 text-cyan-400" />}
        details={[
          '3x3 Pearson Correlation Heatmap (Gold vs Bitcoin vs NVIDIA)',
          'Multi-Asset Daily Returns Covariance Matrix',
          'Rolling Correlation Windows (30D, 60D, 90D, 180D)',
          'Decoupling and Flight-to-Safety Regime Detection'
        ]}
      />
    </div>
  );
};
