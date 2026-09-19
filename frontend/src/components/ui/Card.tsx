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
    default: "bg-[#0D111A] border border-[#1E293B] shadow-xl shadow-black/50",
    subpanel: "bg-[#121824] border border-[#1E293B]",
    bordered: "bg-transparent border border-[#1E293B]",
    glass: "bg-[#0D111A]/85 backdrop-blur-md border border-[#1E293B]/80 shadow-2xl shadow-black/60",
  };

  return (
    <div className={cn("rounded-lg overflow-hidden transition-all duration-200", variants[variant], className)} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("px-4 py-3.5 border-b border-[#1E293B]/70 flex items-center justify-between bg-[#0A0E17]/40", className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => (
  <h3 className={cn("text-xs sm:text-sm font-semibold tracking-wide text-slate-100 uppercase font-mono", className)} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<HTMLAttributes<HTMLParagraphElement>> = ({ className, children, ...props }) => (
  <p className={cn("text-[11px] text-slate-400 mt-0.5 font-mono", className)} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("p-4 sm:p-5", className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<HTMLAttributes<HTMLDivElement>> = ({ className, children, ...props }) => (
  <div className={cn("px-4 py-2.5 border-t border-[#1E293B]/70 bg-[#080B12]/60 flex items-center justify-between text-xs text-slate-400", className)} {...props}>
    {children}
  </div>
);
