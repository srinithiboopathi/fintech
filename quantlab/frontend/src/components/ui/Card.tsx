import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'glow' | 'subtle';
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  variant = 'glass',
  hoverEffect = false,
  ...props
}) => {
  const baseStyles = 'rounded-xl p-5 relative overflow-hidden transition-all duration-200';

  const variants = {
    default: 'bg-slate-900 border border-slate-800 shadow-xl',
    glass: 'glass-card',
    glow: 'glass-panel-glow',
    subtle: 'bg-slate-900/40 border border-slate-800/60',
  };

  return (
    <div
      className={clsx(
        baseStyles,
        variants[variant],
        hoverEffect && 'hover:-translate-y-1 hover:border-cyan-500/40 hover:shadow-xl hover:shadow-cyan-500/5',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
