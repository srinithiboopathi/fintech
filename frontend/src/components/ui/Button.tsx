import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'gold' | 'danger' | 'accent';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading = false, children, disabled, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500 disabled:pointer-events-none disabled:opacity-40 rounded select-none cursor-pointer active:scale-[0.98]";

    const variants = {
      primary: "bg-cyan-600 hover:bg-cyan-500 text-white shadow-sm shadow-cyan-950",
      secondary: "bg-[#161F2E] hover:bg-[#1E2A3E] text-slate-200 border border-[#232E42]",
      outline: "bg-transparent hover:bg-[#161F2E] text-slate-300 border border-[#232E42] hover:text-white",
      ghost: "bg-transparent hover:bg-[#161F2E]/80 text-slate-400 hover:text-slate-100",
      gold: "bg-amber-600 hover:bg-amber-500 text-amber-950 font-semibold shadow-sm",
      danger: "bg-rose-600/20 text-rose-300 border border-rose-600/40 hover:bg-rose-600/30",
      accent: "bg-emerald-600 hover:bg-emerald-500 text-white",
    };

    const sizes = {
      xs: "h-7 px-2.5 text-xs font-mono",
      sm: "h-8 px-3 text-xs font-mono",
      md: "h-9 px-4 text-xs font-mono",
      lg: "h-11 px-6 text-sm font-medium",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
