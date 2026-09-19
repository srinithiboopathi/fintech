import React from 'react';
import { StrategyInfo } from '../../types';
import { Card } from '../ui/Card';
import { Zap, TrendingUp, RefreshCw, BarChart2 } from 'lucide-react';

interface StrategySelectorProps {
  strategies: StrategyInfo[];
  selectedId: string;
  onSelect: (id: string) => void;
}

export const StrategySelector: React.FC<StrategySelectorProps> = ({
  strategies,
  selectedId,
  onSelect,
}) => {
  const getIcon = (cat: string) => {
    switch (cat) {
      case 'Trend Following':
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'Mean Reversion':
        return <RefreshCw className="w-4 h-4 text-purple-400" />;
      case 'Breakout':
        return <Zap className="w-4 h-4 text-cyan-400" />;
      default:
        return <BarChart2 className="w-4 h-4 text-amber-400" />;
    }
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {strategies.map((strat) => {
        const isSelected = strat.id === selectedId;
        return (
          <Card
            key={strat.id}
            variant="glass"
            onClick={() => onSelect(strat.id)}
            className={`cursor-pointer transition-all duration-200 text-left p-4 ${
              isSelected
                ? 'border-emerald-400 bg-slate-800/90 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-400/50'
                : 'hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
                {getIcon(strat.category)}
              </div>
              <span className="text-[10px] font-mono text-slate-400 uppercase">{strat.category}</span>
            </div>
            <h4 className="font-bold text-sm text-slate-100 mb-1">{strat.name}</h4>
            <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">{strat.description}</p>
          </Card>
        );
      })}
    </div>
  );
};
