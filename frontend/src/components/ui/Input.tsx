import React, { InputHTMLAttributes, SelectHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, icon, id, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={id} className="block text-xs font-mono font-medium text-slate-300">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {icon && (
            <div className="absolute left-3 text-slate-400 pointer-events-none">
              {icon}
            </div>
          )}
          <input
            id={id}
            ref={ref}
            className={cn(
              "w-full bg-[#161F2E] border border-[#232E42] text-slate-100 placeholder-slate-500 rounded px-3 py-2 text-xs font-mono transition-colors",
              "focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              icon ? "pl-9" : "",
              error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500" : "",
              className
            )}
            {...props}
          />
        </div>
        {error && <p className="text-[11px] font-mono text-rose-400">{error}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, children, id, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={id} className="block text-xs font-mono font-medium text-slate-300">
            {label}
          </label>
        )}
        <select
          id={id}
          ref={ref}
          className={cn(
            "w-full bg-[#161F2E] border border-[#232E42] text-slate-100 rounded px-3 py-2 text-xs font-mono transition-colors",
            "focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500",
            "disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer",
            error ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500" : "",
            className
          )}
          {...props}
        >
          {children}
        </select>
        {error && <p className="text-[11px] font-mono text-rose-400">{error}</p>}
      </div>
    );
  }
);

Select.displayName = 'Select';
