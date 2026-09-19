import React, { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'gold' | 'btc' | 'nvda' | 'cyan' | 'emerald' | 'rose' | 'amber' | 'muted';
  size?: 'xs' | 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'sm',
  children,
  ...props
}) => {
  const baseStyles = "inline-flex items-center font-mono font-medium rounded transition-colors";

  const variants = {
    default: "bg-[#161F2E] text-slate-300 border border-[#232E42]",
    outline: "border border-[#232E42] text-slate-400 bg-transparent",
    gold: "bg-amber-950/60 text-amber-300 border border-amber-700/50",
    btc: "bg-orange-950/60 text-orange-400 border border-orange-700/50",
    nvda: "bg-lime-950/60 text-lime-400 border border-lime-700/50",
    cyan: "bg-cyan-950/60 text-cyan-400 border border-cyan-800/50",
    emerald: "bg-emerald-950/60 text-emerald-400 border border-emerald-800/50",
    rose: "bg-rose-950/60 text-rose-400 border border-rose-800/50",
    amber: "bg-yellow-950/60 text-yellow-400 border border-yellow-800/50",
    muted: "bg-[#111722] text-slate-500 border border-[#1E2A3E]",
  };

  const sizes = {
    xs: "px-1.5 py-0.2 text-[10px] uppercase tracking-wider",
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs",
  };

  return (
    <span className={cn(baseStyles, variants[variant], sizes[size], className)} {...props}>
      {children}
    </span>
  );
};
