import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  TrendingUp,
  Activity,
  Layers,
  ShieldCheck,
  GitMerge,
  Cpu,
  PlayCircle,
  BarChart3,
  ArrowUpRight,
  Database
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { useAppStore } from '../store/useAppStore';

export const DashboardPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const assetDetails = {
    gold: { name: 'Gold (Physical/Futures)', ticker: 'GOLD', category: 'Safe-Haven Commodity', badge: 'gold' as const },
    bitcoin: { name: 'Bitcoin (BTC-USD)', ticker: 'BTC', category: 'Digital Asset', badge: 'btc' as const },
    nvidia: { name: 'NVIDIA Corporation', ticker: 'NVDA', category: 'Equities Tech Semiconductor', badge: 'nvda' as const },
  };

  const currentAsset = assetDetails[selectedAsset];

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Selector */}
      <div className="bg-[#111722] border border-[#232E42] rounded-lg p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono font-bold">
            QL
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white tracking-wide">
                Terminal Dashboard Overview
              </h1>
              <Badge variant="cyan" size="xs">Phase 1 Shell</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-Asset Financial Intelligence & Quantitative Execution Terminal
            </p>
          </div>
        </div>

        {/* Asset Quick Switcher */}
        <div className="flex items-center space-x-2 bg-[#161F2E] p-1.5 rounded-lg border border-[#232E42]">
          <span className="text-[11px] font-mono text-slate-400 px-2 uppercase">Active Asset:</span>
          <button
            onClick={() => setSelectedAsset('gold')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'gold'
                ? 'bg-amber-950/80 text-amber-300 border border-amber-700/60 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            GOLD
          </button>
          <button
            onClick={() => setSelectedAsset('bitcoin')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'bitcoin'
                ? 'bg-orange-950/80 text-orange-400 border border-orange-700/60 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            BTC
          </button>
          <button
            onClick={() => setSelectedAsset('nvidia')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'nvidia'
                ? 'bg-lime-950/80 text-lime-400 border border-lime-700/60 font-semibold shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NVDA
          </button>
        </div>
      </div>

      {/* 6 Structural Sections Required for Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 1. Portfolio Overview */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <CardTitle>1. Portfolio Overview</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Structural</Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-[#161F2E] rounded border border-[#232E42]">
                <span className="text-xs text-slate-400 font-mono">Current Focus Asset</span>
                <Badge variant={currentAsset.badge} size="sm">{currentAsset.ticker}</Badge>
              </div>
              <div className="p-4 bg-[#161F2E]/50 rounded border border-[#232E42]/60 text-center space-y-2">
                <Database className="w-6 h-6 text-slate-500 mx-auto" />
                <p className="text-xs text-slate-400">
                  Portfolio capital allocation, total simulated equity, and cash balance metrics will activate with Phase 8 Backtesting.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Engine Status: Ready for Ingestion</span>
            <NavLink to="/backtesting" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Configure</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 2. Market Snapshot */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <CardTitle>2. Market Snapshot</CardTitle>
              </div>
              <Badge variant={currentAsset.badge} size="xs">{selectedAsset.toUpperCase()}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-xs text-slate-300 font-mono flex items-center justify-between">
                <span className="text-slate-400">Asset Class:</span>
                <span>{currentAsset.category}</span>
              </div>
              <div className="p-4 bg-[#161F2E]/50 rounded border border-[#232E42]/60 text-center space-y-2">
                <Activity className="w-6 h-6 text-slate-500 mx-auto" />
                <p className="text-xs text-slate-400">
                  Real historical OHLCV settlement candles, session volume, and daily percentage change will load from Kaggle dataset in Phase 2.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Data Source: Kaggle Raw Files</span>
            <NavLink to="/market-analysis" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Deep Dive</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 3. Performance Metrics */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-cyan-400" />
                <CardTitle>3. Performance Metrics</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 4 Engine</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">CUMULATIVE RETURN</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">ANNUALIZED RETURN</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
              </div>
              <p className="text-xs text-slate-400 bg-[#161F2E]/50 p-3 rounded border border-[#232E42]/60">
                Mathematical indicator engine (Pandas/NumPy) calculates exact compounding returns without look-ahead bias.
              </p>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Backend: Python SciPy</span>
            <NavLink to="/market-analysis" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>View Indicators</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 4. Risk Metrics */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <CardTitle>4. Risk Metrics</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 4 Engine</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">ANNUALIZED VOL</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">MAX DRAWDOWN</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">SHARPE RATIO</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
                <div className="p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-slate-500 text-[10px] block">CALMAR RATIO</span>
                  <span className="text-slate-400 text-xs">—</span>
                </div>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Risk Free Rate: Rf = 0.0</span>
            <NavLink to="/robustness" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Risk Lab</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 5. Asset Comparison */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <GitMerge className="w-4 h-4 text-cyan-400" />
                <CardTitle>5. Asset Comparison</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 6 Lab</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex items-center justify-between p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-amber-300">Gold vs Bitcoin</span>
                  <span className="text-slate-500">Pending Phase 6</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-amber-300">Gold vs NVIDIA</span>
                  <span className="text-slate-500">Pending Phase 6</span>
                </div>
                <div className="flex items-center justify-between p-2 bg-[#161F2E] rounded border border-[#232E42]">
                  <span className="text-orange-400">Bitcoin vs NVIDIA</span>
                  <span className="text-slate-500">Pending Phase 6</span>
                </div>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Pearson Matrix Analysis</span>
            <NavLink to="/correlation" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Correlation Lab</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 6. Recent Backtests */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <PlayCircle className="w-4 h-4 text-cyan-400" />
                <CardTitle>6. Recent Backtests</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 8 Backtest</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 bg-[#161F2E]/50 rounded border border-[#232E42]/60 text-center space-y-2">
                <Cpu className="w-6 h-6 text-slate-500 mx-auto" />
                <p className="text-xs text-slate-400">
                  Execute SMA Crossover, EMA Trend, Momentum, or Mean Reversion simulations to populate historical backtest runs.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px]">Strategy Simulation Hub</span>
            <NavLink to="/strategy-builder" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Build Strategy</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};
