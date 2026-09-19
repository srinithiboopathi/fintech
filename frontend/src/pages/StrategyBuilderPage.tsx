import React from 'react';
import { Cpu, Sliders } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const StrategyBuilderPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex items-center justify-between shadow-xl quant-glass">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white">Quantitative Strategy Builder</h1>
              <Badge variant="cyan" size="xs">Phase 7 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Formulate quantitative trading logic and signal generation algorithms.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Strategy Builder Module"
        description="The Strategy Builder engine will be implemented in Phase 7 to configure algorithmic signal models with strict look-ahead bias elimination."
        phase={7}
        icon={<Sliders className="w-6 h-6 text-cyan-400" />}
        details={[
          'SMA Fast/Slow Crossover Strategy (e.g., 20/50 SMA, 50/200 Golden Cross)',
          'EMA Trend Inflection Strategy',
          'Momentum Strategy (RSI / Rate of Change)',
          'Mean Reversion Strategy (Bollinger Band standard deviations / Z-scores)',
          'Signal Overlay & Position State Matrix (+1 Long, 0 Flat, -1 Short)'
        ]}
      />
    </div>
  );
};
