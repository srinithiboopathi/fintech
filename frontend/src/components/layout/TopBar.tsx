import React, { useEffect, useState } from 'react';
import { useLocation, NavLink } from 'react-router-dom';
import { Menu, Server, ShieldCheck, Clock, Filter } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { checkHealth } from '../../lib/api';

interface TopBarProps {
  onToggleSidebar: () => void;
}

const pageTitles: Record<string, string> = {
  '/dashboard': 'Portfolio Overview & Multi-Asset Intelligence',
  '/market-analysis': 'Historical Price & Quantitative Indicator Analysis',
  '/correlation': 'Cross-Asset Correlation & Covariance Matrix Lab',
  '/strategy-builder': 'Quantitative Strategy Builder & Signal Generation',
  '/backtesting': 'Portfolio Backtest Engine & Transaction Cost Simulation',
  '/trade-history': 'Execution Trade Log & Historical Orders',
  '/robustness': 'Parameter Sensitivity & Monte Carlo Robustness Lab',
  '/market-regimes': 'Market Regime Classification & Volatility Regimes',
  '/research-report': 'Institutional Research Report & Teardown Summary',
};

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar }) => {
  const location = useLocation();
  const { selectedAsset, setSelectedAsset, backendHealthy, setBackendHealthy } = useAppStore();
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC');
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const testHealth = async () => {
      try {
        const res = await checkHealth();
        setBackendHealthy(res.status === 'healthy');
      } catch {
        setBackendHealthy(false);
      }
    };
    testHealth();
  }, [setBackendHealthy]);

  const currentTitle = pageTitles[location.pathname] || 'QUANTLAB Platform';

  return (
    <header className="h-14 bg-[#0D111A] border-b border-[#1E293B] px-4 lg:px-6 flex items-center justify-between sticky top-0 z-30 shrink-0">
      {/* Left side: Hamburger + Page Title */}
      <div className="flex items-center space-x-3 min-w-0">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded hover:bg-[#161F2E]"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-mono text-cyan-400 tracking-wider uppercase font-semibold">
              QUANTLAB
            </span>
            <span className="text-slate-600 hidden sm:inline">•</span>
            <h2 className="text-xs sm:text-sm font-semibold text-slate-100 font-mono truncate">
              {currentTitle}
            </h2>
          </div>
        </div>
      </div>

      {/* Right side: Asset selector + Date/Filter placeholder + Telemetry + MAID Profile */}
      <div className="flex items-center space-x-2 md:space-x-3 shrink-0">
        {/* Asset Quick Switcher */}
        <div className="flex items-center bg-[#121824] border border-[#1E293B] rounded p-0.5 text-xs font-mono">
          <button
            onClick={() => setSelectedAsset('gold')}
            className={`px-2 py-0.5 rounded transition-colors ${
              selectedAsset === 'gold'
                ? 'bg-amber-950/90 text-amber-300 border border-amber-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            GOLD
          </button>
          <button
            onClick={() => setSelectedAsset('bitcoin')}
            className={`px-2 py-0.5 rounded transition-colors ${
              selectedAsset === 'bitcoin'
                ? 'bg-orange-950/90 text-orange-400 border border-orange-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            BTC
          </button>
          <button
            onClick={() => setSelectedAsset('nvidia')}
            className={`px-2 py-0.5 rounded transition-colors ${
              selectedAsset === 'nvidia'
                ? 'bg-lime-950/90 text-lime-400 border border-lime-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NVDA
          </button>
        </div>

        {/* Date / Filter Placeholder Area */}
        <div className="hidden lg:flex items-center space-x-1.5 bg-[#121824] border border-[#1E293B] px-2.5 py-1 rounded text-xs font-mono text-slate-400">
          <Filter className="w-3 h-3 text-cyan-400" />
          <span className="text-[11px]">ALL DATES</span>
        </div>

        {/* UTC Clock */}
        <div className="hidden xl:flex items-center space-x-1.5 bg-[#121824] border border-[#1E293B] px-2.5 py-1 rounded text-xs font-mono text-slate-400">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span className="text-[11px]">{utcTime || 'UTC'}</span>
        </div>

        {/* Backend Status Indicator */}
        <div
          className="flex items-center space-x-1.5 bg-[#121824] border border-[#1E293B] px-2 py-1 rounded text-xs font-mono"
          title={backendHealthy ? "FastAPI Backend Online" : "FastAPI Backend Offline"}
        >
          <Server className="w-3 h-3 text-slate-400" />
          {backendHealthy === null ? (
            <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
          ) : backendHealthy ? (
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#10B981]"></span>
          ) : (
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
          )}
        </div>

        {/* MAID Profile Placeholder */}
        <NavLink
          to="/login"
          className="flex items-center space-x-1.5 bg-[#121824] hover:bg-[#182030] border border-[#1E293B] px-2 py-1 rounded text-xs font-mono text-slate-300 transition-colors"
        >
          <div className="w-4 h-4 rounded-full bg-cyan-900/60 border border-cyan-500/50 flex items-center justify-center text-[9px] text-cyan-300">
            M
          </div>
          <span className="hidden md:inline text-[11px] text-slate-300">MAID Auth</span>
          <ShieldCheck className="w-3 h-3 text-cyan-400" />
        </NavLink>
      </div>
    </header>
  );
};
