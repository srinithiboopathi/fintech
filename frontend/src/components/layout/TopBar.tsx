import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, Server, Clock, Filter, LogOut } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { checkHealth } from '../../lib/api';
import { authApi } from '../../api';

interface TopBarProps {
  onToggleSidebar: () => void;
}

const pageTitles: Record<string, string> = {
  '/dashboard': 'Portfolio Overview & Multi-Asset Intelligence',
  '/market-analysis': 'Historical Price & Quantitative Indicator Analysis',
  '/correlation': 'Cross-Asset Correlation & Covariance Matrix Lab',
  '/portfolio': 'Multi-Asset Portfolio Analytics & Risk Decomposition',
  '/portfolio/optimization': 'Portfolio Optimization & Efficient Frontier Lab',
  '/strategy-builder': 'Quantitative Strategy Builder & Signal Generation',
  '/backtesting': 'Portfolio Backtest Engine & Transaction Cost Simulation',
  '/trade-history': 'Execution Trade Log & Historical Orders',
  '/robustness': 'Parameter Sensitivity & Monte Carlo Robustness Lab',
  '/market-regimes': 'Market Regime Classification & Volatility Regimes',
  '/research-report': 'Institutional Research Report & Teardown Summary',
};

export const TopBar: React.FC<TopBarProps> = ({ onToggleSidebar }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { selectedAsset, setSelectedAsset, backendHealthy, setBackendHealthy, user, isDemo, logout } = useAppStore();
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

  const handleLogout = async () => {
    try {
      if (!isDemo) {
        await authApi.logout();
      }
    } catch {
      // Ignore logout errors and proceed with client state clearance
    } finally {
      logout();
      navigate('/login');
    }
  };

  const currentTitle = pageTitles[location.pathname] || 'QUANTLAB Platform';
  const displayEmail = user?.email || (isDemo ? 'demo.analyst' : 'analyst');
  const userInitial = (user?.full_name ? user.full_name[0] : user?.email ? user.email[0] : 'Q').toUpperCase();

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

      {/* Right side: Asset selector + Telemetry + User profile + Logout */}
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

        {/* Authenticated User Pill */}
        <div className="flex items-center space-x-2 bg-[#121824] border border-[#1E293B] px-2.5 py-1 rounded text-xs font-mono text-slate-300">
          <div className="w-4 h-4 rounded-full bg-cyan-950 border border-cyan-500/50 flex items-center justify-center text-[9px] text-cyan-300 font-bold">
            {userInitial}
          </div>
          <span className="hidden md:inline text-[11px] text-slate-300 max-w-[120px] truncate" title={displayEmail}>
            {user?.full_name || displayEmail}
          </span>
          {isDemo && (
            <span className="text-[9px] px-1 py-0.2 rounded bg-amber-950 text-amber-400 border border-amber-800/60 font-semibold">
              DEMO
            </span>
          )}
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="flex items-center space-x-1 bg-[#121824] hover:bg-rose-950/40 hover:text-rose-300 hover:border-rose-800/60 border border-[#1E293B] px-2 py-1 rounded text-xs font-mono text-slate-400 transition-colors"
          title="Sign out of QuantLab"
          aria-label="Sign out"
        >
          <LogOut className="w-3 h-3" />
          <span className="hidden sm:inline text-[11px]">Logout</span>
        </button>
      </div>
    </header>
  );
};

