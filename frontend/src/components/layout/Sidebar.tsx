import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  GitMerge,
  Cpu,
  PlayCircle,
  History,
  ShieldAlert,
  Gauge,
  FileText,
  X
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  phase: number;
}

const navItems: NavItem[] = [
  { name: 'Overview', path: '/dashboard', icon: LayoutDashboard, phase: 1 },
  { name: 'Market Analysis', path: '/market-analysis', icon: TrendingUp, phase: 5 },
  { name: 'Correlation Lab', path: '/correlation', icon: GitMerge, phase: 6 },
  { name: 'Strategy Builder', path: '/strategy-builder', icon: Cpu, phase: 7 },
  { name: 'Backtesting', path: '/backtesting', icon: PlayCircle, phase: 8 },
  { name: 'Trade History', path: '/trade-history', icon: History, phase: 9 },
  { name: 'Robustness Lab', path: '/robustness', icon: ShieldAlert, phase: 11 },
  { name: 'Market Regimes', path: '/market-regimes', icon: Gauge, phase: 12 },
  { name: 'Research Report', path: '/research-report', icon: FileText, phase: 13 },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar container */}
      <aside
        className={cn(
          "fixed top-0 left-0 bottom-0 z-50 w-64 bg-[#0A0E17] border-r border-[#1E293B] flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static shrink-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand header */}
        <div className="h-14 px-4 border-b border-[#1E293B] flex items-center justify-between bg-[#0D111A]">
          <NavLink to="/dashboard" className="flex items-center space-x-2.5 group">
            <div className="w-7 h-7 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-xs group-hover:border-cyan-400 transition-colors">
              QL
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-xs tracking-wider text-slate-100 font-mono">QUANTLAB</span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              </div>
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block -mt-0.5">
                Quant Terminal
              </span>
            </div>
          </NavLink>

          <button
            onClick={onClose}
            className="lg:hidden p-1 text-slate-400 hover:text-white rounded hover:bg-[#161F2E]"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Section title */}
        <div className="px-4 py-2.5 text-[9px] font-mono font-semibold tracking-widest text-slate-500 uppercase">
          Terminal Navigation
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth < 1024) onClose();
                }}
                className={({ isActive }) =>
                  cn(
                    "flex items-center justify-between px-3 py-2 rounded text-xs font-mono transition-all group relative",
                    isActive
                      ? "bg-cyan-950/40 text-cyan-300 font-medium border-l-2 border-cyan-400 pl-2.5"
                      : "text-slate-400 hover:text-slate-200 hover:bg-[#121824] border-l-2 border-transparent"
                  )
                }
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="w-3.5 h-3.5 transition-colors group-hover:text-cyan-400 text-slate-400" />
                  <span>{item.name}</span>
                </div>
                {item.phase > 1 && (
                  <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-[#121824] text-slate-500 border border-[#1E293B]">
                    P{item.phase}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Asset Coverage Section */}
        <div className="p-3 border-t border-[#1E293B] bg-[#080B12]">
          <div className="text-[9px] font-mono font-semibold tracking-widest text-slate-500 uppercase mb-2">
            Target Universe
          </div>
          <div className="grid grid-cols-3 gap-1 text-center font-mono text-[10px]">
            <div className="bg-[#121824] border border-amber-800/40 text-amber-300 py-1 rounded">
              GOLD
            </div>
            <div className="bg-[#121824] border border-orange-800/40 text-orange-400 py-1 rounded">
              BTC
            </div>
            <div className="bg-[#121824] border border-lime-800/40 text-lime-400 py-1 rounded">
              NVDA
            </div>
          </div>
        </div>

        {/* Footer status */}
        <div className="px-3.5 py-2.5 border-t border-[#1E293B] bg-[#0A0E17] text-[10px] font-mono text-slate-500 flex items-center justify-between">
          <span>Engine v0.1.0</span>
          <span className="text-emerald-400 flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Online</span>
          </span>
        </div>
      </aside>
    </>
  );
};
