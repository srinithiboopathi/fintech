import React from 'react';
import { Layers, ArrowRight } from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../lib/utils';

export interface EmptyStateProps {
  title: string;
  description: string;
  phase?: number;
  icon?: React.ReactNode;
  actionText?: string;
  actionPath?: string;
  details?: string[];
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  phase,
  icon,
  actionText = "Return to Dashboard",
  actionPath = "/dashboard",
  details,
  className,
}) => {
  const navigate = useNavigate();

  return (
    <div className={cn("bg-[#111722] border border-[#232E42] rounded-lg p-8 md:p-12 text-center max-w-2xl mx-auto shadow-xl", className)}>
      <div className="w-14 h-14 rounded-lg bg-cyan-950/40 border border-cyan-800/40 flex items-center justify-center mx-auto mb-4 text-cyan-400">
        {icon || <Layers className="w-7 h-7" />}
      </div>

      <div className="flex items-center justify-center gap-2 mb-2">
        <h3 className="text-lg font-semibold text-slate-100 font-mono tracking-tight">{title}</h3>
        {phase !== undefined && (
          <Badge variant="cyan" size="xs">
            Phase {phase} Module
          </Badge>
        )}
      </div>

      <p className="text-xs text-slate-400 max-w-lg mx-auto mb-6 leading-relaxed">
        {description}
      </p>

      {details && details.length > 0 && (
        <div className="bg-[#161F2E] border border-[#232E42] rounded p-4 mb-6 text-left max-w-md mx-auto">
          <div className="text-[11px] font-mono text-slate-400 uppercase mb-2">Planned Specifications:</div>
          <ul className="space-y-1.5 text-xs text-slate-300 font-mono">
            {details.map((item, idx) => (
              <li key={idx} className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button
        variant="secondary"
        size="sm"
        onClick={() => navigate(actionPath)}
        className="inline-flex items-center gap-1.5"
      >
        <span>{actionText}</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </Button>
    </div>
  );
};
