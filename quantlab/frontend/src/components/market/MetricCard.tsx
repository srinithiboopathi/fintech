import React from 'react';
import { Card } from '../ui/Card';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  change?: number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  tooltip?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  change,
  icon,
  trend = 'neutral',
  tooltip,
}) => {
  return (
    <Card variant="glass" className="flex flex-col justify-between hover:border-slate-700">
      <div className="flex items-center justify-between text-slate-400 mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider font-mono" title={tooltip}>
          {label}
        </span>
        {icon && <span className="text-cyan-400/80">{icon}</span>}
      </div>
      <div>
        <div className="text-xl lg:text-2xl font-black text-slate-100 font-mono tracking-tight">
          {value}
        </div>
        <div className="flex items-center gap-2 mt-1">
          {change !== undefined && (
            <span
              className={`text-xs font-semibold font-mono ${
                change > 0
                  ? 'text-emerald-400'
                  : change < 0
                  ? 'text-rose-400'
                  : 'text-slate-400'
              }`}
            >
              {change > 0 ? '+' : ''}
              {change.toFixed(2)}%
            </span>
          )}
          {subValue && <span className="text-xs text-slate-400 font-mono">{subValue}</span>}
        </div>
      </div>
    </Card>
  );
};
