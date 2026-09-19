import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  TrendingUp,
  Activity,
  ShieldCheck,
  Cpu,
  PlayCircle,
  BarChart3,
  ArrowUpRight,
  Layers
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
      {/* Top Asset & Terminal Status Banner */}
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 shadow-xl quant-glass">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono font-bold">
            QL
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white tracking-wide">
                Terminal Dashboard Overview
              </h1>
              <Badge variant="cyan" size="xs">Phase 1 Active</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Quantitative Multi-Asset Financial Intelligence & Backtesting System
            </p>
          </div>
        </div>

        {/* Active Asset Selector */}
        <div className="flex items-center space-x-2 bg-[#121824] p-1.5 rounded-lg border border-[#1E293B]">
          <span className="text-[11px] font-mono text-slate-400 px-2 uppercase">Active Asset:</span>
          <button
            onClick={() => setSelectedAsset('gold')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'gold'
                ? 'bg-amber-950/90 text-amber-300 border border-amber-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            GOLD
          </button>
          <button
            onClick={() => setSelectedAsset('bitcoin')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'bitcoin'
                ? 'bg-orange-950/90 text-orange-400 border border-orange-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            BTC
          </button>
          <button
            onClick={() => setSelectedAsset('nvidia')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'nvidia'
                ? 'bg-lime-950/90 text-lime-400 border border-lime-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NVDA
          </button>
        </div>
      </div>

      {/* 5 Core Dashboard Sections Required */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. Market Overview */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <CardTitle>1. Market Overview</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Multi-Asset</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-amber-300">Gold (Commodity)</span>
                  <span className="text-slate-500 text-[11px]">Awaiting Ingestion</span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-orange-400">Bitcoin (Crypto)</span>
                  <span className="text-slate-500 text-[11px]">Awaiting Ingestion</span>
                </div>
                <div className="flex items-center justify-between p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-lime-400">NVIDIA (Equities)</span>
                  <span className="text-slate-500 text-[11px]">Awaiting Ingestion</span>
                </div>
              </div>
              <div className="p-3 bg-[#121824]/50 rounded border border-[#1E293B]/60 text-center">
                <p className="text-[11px] text-slate-400 font-mono">
                  Normalized daily time-series will link in Phase 2 via Kaggle datasets.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px] text-slate-500">Datasets: datasets/raw/*</span>
            <NavLink to="/market-analysis" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>View Data</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 2. Asset Snapshot */}
        <Card variant="default" className="flex flex-col justify-between">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                <CardTitle>2. Asset Snapshot</CardTitle>
              </div>
              <Badge variant={currentAsset.badge} size="xs">{selectedAsset.toUpperCase()}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="text-xs text-slate-300 font-mono flex items-center justify-between">
                <span className="text-slate-400">Class:</span>
                <span className="text-slate-200">{currentAsset.category}</span>
              </div>
              <div className="p-4 bg-[#121824]/50 rounded border border-[#1E293B]/60 text-center space-y-2">
                <Activity className="w-6 h-6 text-slate-600 mx-auto" />
                <div className="text-xs font-mono text-slate-300 font-medium">Awaiting Historical Data</div>
                <p className="text-[11px] text-slate-400">
                  Open, High, Low, Close, and Traded Volume candles will populate from verified Kaggle records.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px] text-slate-500">Schema: ISO Date, OHLCV</span>
            <NavLink to="/market-analysis" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Price Action</span>
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
                <CardTitle>3. Performance</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 4 Engine</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">CUMULATIVE RETURN</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
                <div className="p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">ANNUALIZED RETURN</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 bg-[#121824]/50 p-3 rounded border border-[#1E293B]/60 leading-relaxed font-mono">
                FastAPI Python engine calculates daily arithmetic and compounded geometric returns.
              </p>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px] text-slate-500">Engine: Python NumPy</span>
            <NavLink to="/market-analysis" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Indicators</span>
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
            <CardContent className="space-y-2.5">
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">ANNUALIZED VOL</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
                <div className="p-2 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">MAX DRAWDOWN</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">SHARPE RATIO</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
                <div className="p-2 bg-[#121824] rounded border border-[#1E293B]">
                  <span className="text-slate-500 text-[10px] block uppercase">CALMAR RATIO</span>
                  <span className="text-slate-400 font-mono text-xs">—</span>
                </div>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px] text-slate-500">Benchmark: Rf = 0.0</span>
            <NavLink to="/robustness" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Risk Diagnostics</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>

        {/* 5. Recent Backtests */}
        <Card variant="default" className="flex flex-col justify-between md:col-span-2 lg:col-span-2">
          <div>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <PlayCircle className="w-4 h-4 text-cyan-400" />
                <CardTitle>5. Recent Backtests & Strategy Hub</CardTitle>
              </div>
              <Badge variant="outline" size="xs">Phase 8 Backtest</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 bg-[#121824]/50 rounded border border-[#1E293B]/60 text-center space-y-2">
                <Cpu className="w-6 h-6 text-slate-600 mx-auto" />
                <div className="text-xs font-mono text-slate-300 font-medium">No Active Backtest Simulations</div>
                <p className="text-[11px] text-slate-400 max-w-md mx-auto">
                  Configure SMA Crossover, EMA Trend, Momentum, or Mean Reversion models with customizable transaction fees in Phase 8.
                </p>
              </div>
            </CardContent>
          </div>
          <CardFooter>
            <span className="font-mono text-[11px] text-slate-500">Simulation: Cash, Holdings, Slippage</span>
            <NavLink to="/strategy-builder" className="text-cyan-400 hover:text-cyan-300 font-mono text-[11px] flex items-center">
              <span>Strategy Builder</span>
              <ArrowUpRight className="w-3 h-3 ml-0.5" />
            </NavLink>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};
