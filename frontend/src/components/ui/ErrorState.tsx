import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from './Button';
import { cn } from '../../lib/utils';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Telemetry Connection Error",
  message,
  onRetry,
  className
}) => {
  return (
    <div className={cn("bg-rose-950/20 border border-rose-900/40 rounded-lg p-6 text-center max-w-lg mx-auto", className)}>
      <div className="w-10 h-10 rounded-full bg-rose-950/60 border border-rose-800/60 flex items-center justify-center mx-auto mb-3 text-rose-400">
        <AlertCircle className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-semibold text-rose-300 font-mono mb-1">{title}</h4>
      <p className="text-xs text-rose-400/80 mb-4">{message}</p>
      {onRetry && (
        <Button variant="danger" size="xs" onClick={onRetry} className="inline-flex items-center gap-1.5">
          <RotateCcw className="w-3 h-3" />
          <span>Retry Operation</span>
        </Button>
      )}
    </div>
  );
};
