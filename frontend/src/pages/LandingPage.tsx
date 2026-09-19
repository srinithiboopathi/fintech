import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  TrendingUp,
  Cpu,
  GitMerge,
  ShieldCheck,
  PlayCircle,
  ArrowRight,
  Database
} from 'lucide-react';
import { Button } from '../components/ui/Button';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Background Decorative Matrix Grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#161F2E15_1px,transparent_1px),linear-gradient(to_bottom,#161F2E15_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Top Navigation */}
      <header className="border-b border-[#232E42]/80 bg-[#111722]/80 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-base">
              QL
            </div>
            <div>
              <span className="font-bold text-base tracking-wider text-slate-100 font-mono">QUANTLAB</span>
              <span className="text-[10px] text-slate-500 font-mono ml-2 uppercase">v0.1.0</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <NavLink to="/login">
              <Button variant="ghost" size="sm">
                MAID Login
              </Button>
            </NavLink>
            <NavLink to="/dashboard">
              <Button variant="primary" size="sm" className="space-x-1.5">
                <span>Enter Terminal</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16 lg:py-24 relative z-10 max-w-6xl mx-auto text-center">
        <div className="inline-flex items-center space-x-2 bg-[#161F2E] border border-[#232E42] px-3.5 py-1.5 rounded-full mb-6 text-xs font-mono text-cyan-400">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          <span>Institutional Multi-Asset Quantitative Engine</span>
        </div>

        <h1 className="text-3xl md:text-5xl lg:text-6xl font-extrabold tracking-tight text-white max-w-4xl leading-tight md:leading-tight">
          Quantitative Multi-Asset <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400">
            Financial Intelligence & Backtesting
          </span>
        </h1>

        <p className="mt-6 text-sm md:text-base text-slate-400 max-w-2xl leading-relaxed font-sans">
          A full-stack quantitative research terminal designed for rigorous analysis across 
          <span className="text-amber-300 font-mono mx-1">Gold</span>, 
          <span className="text-orange-400 font-mono mx-1">Bitcoin</span>, and 
          <span className="text-lime-400 font-mono mx-1">NVIDIA</span>.
          Featuring mathematical indicator engines, cross-asset correlation matrices, and portfolio backtesting with realistic execution frictions.
        </p>

        {/* CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center gap-4">
          <NavLink to="/dashboard">
            <Button variant="primary" size="lg" className="w-full sm:w-auto px-8 space-x-2 font-mono">
              <span>Launch QuantLab Terminal</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </NavLink>
          <NavLink to="/login">
            <Button variant="secondary" size="lg" className="w-full sm:w-auto px-6 space-x-2 font-mono">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>MAID Authentication</span>
            </Button>
          </NavLink>
        </div>

        {/* Multi-Asset Pill Badges */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-3">
          <div className="bg-[#111722] border border-[#232E42] px-4 py-2 rounded-lg flex items-center space-x-2.5">
            <div className="w-2 h-2 rounded-full bg-amber-400"></div>
            <span className="text-xs font-mono font-medium text-amber-300">Gold (Safe Haven)</span>
          </div>
          <div className="bg-[#111722] border border-[#232E42] px-4 py-2 rounded-lg flex items-center space-x-2.5">
            <div className="w-2 h-2 rounded-full bg-orange-400"></div>
            <span className="text-xs font-mono font-medium text-orange-400">Bitcoin (Digital Asset)</span>
          </div>
          <div className="bg-[#111722] border border-[#232E42] px-4 py-2 rounded-lg flex items-center space-x-2.5">
            <div className="w-2 h-2 rounded-full bg-lime-400"></div>
            <span className="text-xs font-mono font-medium text-lime-400">NVIDIA (Equities Tech)</span>
          </div>
        </div>

        {/* 4 Core Pillars */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 w-full text-left">
          <div className="bg-[#111722] border border-[#232E42] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
            <div className="w-9 h-9 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100 font-mono mb-1">Multi-Asset Intelligence</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Historical OHLCV normalization, SMA, EMA, returns, volatility, Sharpe ratio, and max drawdown.
            </p>
          </div>

          <div className="bg-[#111722] border border-[#232E42] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
            <div className="w-9 h-9 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
              <GitMerge className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100 font-mono mb-1">Correlation Lab</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Pearson correlation matrices, dynamic covariance, and rolling window co-movement analysis.
            </p>
          </div>

          <div className="bg-[#111722] border border-[#232E42] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
            <div className="w-9 h-9 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100 font-mono mb-1">Strategy Formulation</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              SMA Crossover, EMA Trend, Momentum, and Mean Reversion algorithmic rule configurations.
            </p>
          </div>

          <div className="bg-[#111722] border border-[#232E42] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
            <div className="w-9 h-9 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
              <PlayCircle className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100 font-mono mb-1">Portfolio Backtesting</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Simulated equity curve tracking, transaction cost frictions, slippage, and Buy & Hold benchmarking.
            </p>
          </div>
        </div>

        {/* Institutional Integrity Guarantee */}
        <div className="mt-12 bg-[#161F2E]/60 border border-[#232E42] p-4 rounded-lg flex items-center justify-between flex-wrap gap-3 w-full text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Mathematical Rigor: Zero Synthetic Datasets • Look-Ahead Bias Prevention</span>
          </div>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>FastAPI REST Engine • PostgreSQL Tier</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#232E42] bg-[#0E131C] px-6 py-6 text-center text-xs text-slate-500 font-mono">
        QUANTLAB Platform • Quantitative Multi-Asset Financial Intelligence & Backtesting
      </footer>
    </div>
  );
};
