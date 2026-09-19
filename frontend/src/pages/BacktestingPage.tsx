import React from 'react';
import { PlayCircle, Scale } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const BacktestingPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#111722] border border-[#232E42] rounded-lg p-5 flex items-center justify-between shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <PlayCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white">Portfolio Backtest Engine</h1>
              <Badge variant="cyan" size="xs">Phase 8 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Simulate full portfolio equity curves with realistic transaction fees and slippage modeling.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Backtesting Engine"
        description="The Backtesting Engine will be implemented in Phase 8. It simulates full capital allocation, order execution frictions, and compare strategy returns against the Buy-and-Hold benchmark."
        phase={8}
        icon={<Scale className="w-7 h-7 text-cyan-400" />}
        details={[
          'Initial Capital & Position Sizing Configuration',
          'Configurable Transaction Costs (Basis Points & Fixed Execution Slippage)',
          'Daily Portfolio Cash vs Asset Holdings Valuation Tracking',
          'Equity Curve vs Buy-and-Hold Benchmark Visual Comparison',
          'CAGR, Win Rate, Profit Factor, and Calmar Ratio metrics'
        ]}
      />
    </div>
  );
};
