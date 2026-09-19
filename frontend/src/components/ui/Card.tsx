import React, { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'subpanel' | 'bordered' | 'glass';
}

export const Card: React.FC<CardProps> = ({
  className,
  variant = 'default',
  children,
  ...props
}) => {
  const variants = {
    default: "bg-[#111722] border border-[#232E42] shadow-lg shadow-black/40",
    subpanel: "bg-[#161F2E] border border-[#232E42]",
    bordered: "bg-transparent border border-[#232E42]",
    glass: "bg-[#111722]/80 backdrop-blur-md border border-[#232E42]/80 shadow-xl shadow-black/50",
  };

  return (
    <div className={cn("rounded-lg overflow-hidden transition-all duration-200", variants[variant], className)} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("px-5 py-4 border-b border-[#232E42]/70 flex items-center justify-between", className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => (
  <h3 className={cn("text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono", className)} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<HTMLAttributes<HTMLParagraphElement>> = ({ className, children, ...props }) => (
  <p className={cn("text-xs text-slate-400 mt-0.5", className)} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("p-5", className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("px-5 py-3 border-t border-[#232E42]/70 bg-[#0E131C]/60 flex items-center justify-between text-xs text-slate-400", className)} {...props}>
    {children}
  </div>
);
