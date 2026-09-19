import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, Bell, Search, User as UserIcon, Shield, ChevronRight } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useMarketStore } from '../../store/marketStore';
import { formatCurrency, formatPercent } from '../../utils/formatters';

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const { assets } = useMarketStore();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-4 lg:px-6 py-2.5">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Brand & Breadcrumb */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center p-0.5 shadow-md shadow-cyan-500/20 group-hover:scale-105 transition-transform">
              <div className="w-full h-full bg-[#080c14] rounded-[7px] flex items-center justify-center">
                <Activity className="w-4 h-4 text-emerald-400" />
              </div>
            </div>
            <div className="hidden sm:block">
              <span className="text-base font-extrabold tracking-tight text-white">
                QUANT<span className="text-emerald-400">LAB</span>
              </span>
              <span className="ml-1.5 px-1.5 py-0.5 text-[9px] font-mono uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded">
                Institutional
              </span>
            </div>
          </Link>
        </div>

        {/* Center: Live Real-Time Ticker Ribbon */}
        <div className="hidden md:flex items-center gap-5 px-3 py-1 rounded-full bg-slate-900/60 border border-slate-800/80 font-mono text-xs">
          {assets.slice(0, 3).map((asset) => {
            const isPos = asset.change_24h >= 0;
            return (
              <div
                key={asset.symbol}
                onClick={() => navigate('/market-analysis')}
                className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
              >
                <span className="font-semibold text-slate-300">{asset.symbol}</span>
                <span className="text-slate-100">{formatCurrency(asset.current_price, asset.symbol.includes('NVDA') ? 2 : 1)}</span>
                <span className={`text-[11px] font-medium ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {formatPercent(asset.change_24h)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Right: User Profile & Actions */}
        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Engine Online (Low Latency)
          </div>

          {isAuthenticated && user ? (
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-xs font-bold text-white border border-cyan-400/30">
                {user.name.split(' ').map((n) => n[0]).join('')}
              </div>
              <div className="hidden xl:block text-left text-xs">
                <div className="font-semibold text-slate-200">{user.name}</div>
                <div className="text-[10px] text-slate-400">{user.role}</div>
              </div>
            </div>
          ) : (
            <Link
              to="/login"
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};
