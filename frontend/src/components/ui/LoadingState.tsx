import React from 'react';
import { Activity } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface LoadingStateProps {
  message?: string;
  className?: string;
  rows?: number;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading quantitative telemetry...",
  className,
  rows = 3
}) => {
  return (
    <div className={cn("flex flex-col items-center justify-center p-8 space-y-4", className)}>
      <div className="relative flex items-center justify-center">
        <div className="w-10 h-10 rounded-full border-2 border-cyan-500/20 border-t-cyan-500 animate-spin"></div>
        <Activity className="w-4 h-4 text-cyan-400 absolute animate-pulse" />
      </div>
      <p className="text-xs font-mono text-slate-400 tracking-wide">{message}</p>
      
      {/* Monospace skeleton placeholders */}
      <div className="w-full max-w-md space-y-2 mt-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-4 bg-[#161F2E] border border-[#232E42]/60 rounded animate-pulse"
            style={{ width: `${100 - i * 15}%` }}
          />
        ))}
      </div>
    </div>
  );
};
