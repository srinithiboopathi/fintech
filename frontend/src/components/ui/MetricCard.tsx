import React from 'react';
import { Card } from './Card';
import { cn } from '../../lib/utils';

export interface MetricCardProps {
  title: string;
  value: string | number | null | undefined;
  subtitle?: string;
  change?: number | null;
  changeLabel?: string;
  isPositiveGood?: boolean;
  prefix?: string;
  suffix?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  tooltip?: string;
  className?: string;
  variant?: 'default' | 'subpanel' | 'bordered';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  isPositiveGood = true,
  prefix = '',
  suffix = '',
  icon,
  badge,
  className,
  variant = 'default',
}) => {
  const formatValue = (val: string | number | null | undefined) => {
    if (val === null || val === undefined) return '—';
    if (typeof val === 'number') {
      if (isNaN(val)) return '—';
      return val.toLocaleString('en-US', { maximumFractionDigits: 4 });
    }
    return val;
  };

  const getChangeColor = (c: number) => {
    if (c === 0) return 'text-slate-400';
    if (isPositiveGood) {
      return c > 0 ? 'text-emerald-400' : 'text-rose-400';
    }
    return c > 0 ? 'text-rose-400' : 'text-emerald-400';
  };

  return (
    <Card variant={variant} className={cn("p-4 flex flex-col justify-between", className)}>
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider truncate">
          {title}
        </span>
        <div className="flex items-center space-x-1.5 shrink-0">
          {badge}
          {icon && <div className="text-slate-400">{icon}</div>}
        </div>
      </div>

      <div className="flex items-baseline space-x-1">
        {prefix && <span className="text-sm font-mono text-slate-400">{prefix}</span>}
        <span className="text-lg sm:text-xl font-bold font-mono text-slate-100 tracking-tight">
          {formatValue(value)}
        </span>
        {suffix && <span className="text-xs font-mono text-slate-400">{suffix}</span>}
      </div>

      {(subtitle || change !== undefined) && (
        <div className="mt-2 flex items-center justify-between text-[11px] font-mono border-t border-[#1E293B]/40 pt-1.5">
          {subtitle && <span className="text-slate-500 truncate">{subtitle}</span>}
          {change !== undefined && change !== null && (
            <span className={cn("font-medium ml-auto", getChangeColor(change))}>
              {change > 0 ? '+' : ''}
              {(change * 100).toFixed(2)}% {changeLabel}
            </span>
          )}
        </div>
      )}
    </Card>
  );
};
