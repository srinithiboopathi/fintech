import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  LineChart,
  GitCompare,
  Sliders,
  PlaySquare,
  History,
  ShieldAlert,
  Gauge,
  FileText,
  Sparkles,
} from 'lucide-react';
import { clsx } from 'clsx';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Market Analysis', path: '/market-analysis', icon: LineChart },
  { name: 'Correlation Lab', path: '/correlation-lab', icon: GitCompare },
  { name: 'Strategy Builder', path: '/strategy-builder', icon: Sliders },
  { name: 'Backtesting', path: '/backtesting', icon: PlaySquare },
  { name: 'Trade History', path: '/trade-history', icon: History },
  { name: 'Robustness Lab', path: '/robustness-lab', icon: ShieldAlert },
  { name: 'Market Regimes', path: '/market-regimes', icon: Gauge },
  { name: 'Research Report', path: '/research-report', icon: FileText },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 shrink-0 hidden md:flex flex-col glass-panel border-r border-slate-800/80 min-h-[calc(100vh-53px)] p-3">
      {/* Navigation section */}
      <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 px-3 py-2">
        Core Quantitative Modules
      </div>
      <nav className="space-y-1 mt-1 flex-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
                  isActive
                    ? 'bg-gradient-to-r from-emerald-500/15 to-cyan-500/10 text-emerald-400 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={clsx(
                      'w-4 h-4 transition-colors',
                      isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-cyan-400'
                    )}
                  />
                  <span>{item.name}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Pro Quant Status Banner */}
      <div className="p-3 mt-auto rounded-xl bg-gradient-to-b from-slate-900/80 to-indigo-950/40 border border-indigo-500/20">
        <div className="flex items-center gap-2 mb-1.5">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-200">QuantLab Engine</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed mb-2.5">
          Vectorized Python engine & event simulation active with 100% test coverage.
        </p>
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800">
          <span>v1.0.0 Institutional</span>
          <span className="text-emerald-400 font-semibold">252 Day Matrix</span>
        </div>
      </div>
    </aside>
  );
};
