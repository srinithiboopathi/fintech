import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  TrendingUp,
  GitMerge,
  Cpu,
  PlayCircle,
  ShieldCheck,
  ArrowRight,
  Database,
  BarChart2,
  Lock,
  ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/Button';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#06090E] text-slate-100 flex flex-col font-sans relative overflow-x-hidden selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Abstract Institutional Quant Grid & Glow Background */}
      <div className="fixed inset-0 quant-grid-bg pointer-events-none opacity-60" />
      <div className="fixed inset-0 quant-glow pointer-events-none" />

      {/* Top Navigation Bar */}
      <header className="border-b border-[#1E293B]/70 bg-[#06090E]/80 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <NavLink to="/" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-sm group-hover:border-cyan-400 transition-colors">
              QL
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-sm tracking-wider text-white font-mono">QUANTLAB</span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono tracking-widest uppercase block -mt-0.5">
                Multi-Asset Intelligence
              </span>
            </div>
          </NavLink>

          {/* Quick asset pill indicators */}
          <div className="hidden md:flex items-center space-x-2 text-xs font-mono">
            <span className="text-slate-500 text-[11px] uppercase mr-1">Coverage:</span>
            <span className="px-2 py-0.5 rounded bg-[#0D111A] border border-amber-800/40 text-amber-300">GOLD</span>
            <span className="px-2 py-0.5 rounded bg-[#0D111A] border border-orange-800/40 text-orange-400">BTC</span>
            <span className="px-2 py-0.5 rounded bg-[#0D111A] border border-lime-800/40 text-lime-400">NVDA</span>
          </div>

          <div className="flex items-center space-x-3">
            <NavLink to="/login">
              <Button variant="ghost" size="sm" className="font-mono text-xs text-slate-300 hover:text-white">
                MAID Login
              </Button>
            </NavLink>
            <NavLink to="/login">
              <Button variant="primary" size="sm" className="space-x-1.5 font-mono">
                <span>Enter QuantLab</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </NavLink>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-12 lg:py-20 flex flex-col items-center justify-center relative z-10">
        {/* Terminal Status Pill */}
        <div className="inline-flex items-center space-x-2.5 bg-[#0D111A] border border-[#1E293B] px-3.5 py-1.5 rounded-full mb-8 text-xs font-mono text-cyan-400 shadow-lg">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="tracking-wide">Institutional Quantitative Research & Backtesting Platform</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">v0.1.0</span>
        </div>

        {/* Hero Title */}
        <div className="text-center max-w-4xl space-y-3 mb-6">
          <div className="text-xs md:text-sm font-mono uppercase tracking-[0.25em] text-cyan-400 font-semibold">
            QUANTLAB
          </div>
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Quantitative Multi-Asset <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-slate-100 via-cyan-200 to-teal-400">
              Financial Intelligence & Backtesting
            </span>
          </h1>
        </div>

        {/* Hero Subtitle */}
        <p className="text-sm md:text-base text-slate-400 max-w-2xl text-center leading-relaxed font-sans mb-10">
          A dedicated institutional platform to analyze multiple assets, study quantitative market behavior,
          explore cross-asset correlations, test systematic strategies, simulate portfolio performance with
          realistic transaction costs, and evaluate statistical risk regimes.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full max-w-md mb-16">
          <NavLink to="/login" className="w-full sm:w-auto">
            <Button variant="primary" size="lg" className="w-full px-8 space-x-2 font-mono text-sm tracking-wide">
              <span>ENTER QUANTLAB</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </NavLink>
          <NavLink to="/dashboard" className="w-full sm:w-auto">
            <Button variant="secondary" size="lg" className="w-full px-7 space-x-2 font-mono text-sm">
              <span>EXPLORE PLATFORM</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </Button>
          </NavLink>
        </div>

        {/* Abstract Quantitative Graphic Visual Container */}
        <div className="w-full max-w-5xl bg-[#0D111A]/90 border border-[#1E293B] rounded-xl p-6 lg:p-8 shadow-2xl relative overflow-hidden mb-16 quant-glass">
          {/* Subtle Top Telemetry Header */}
          <div className="flex items-center justify-between border-b border-[#1E293B] pb-4 mb-6 text-xs font-mono text-slate-400">
            <div className="flex items-center space-x-3">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 inline-block"></span>
              <span className="text-slate-200 font-semibold">MULTI-ASSET CROSS-CORRELATION & EQUITY SIMULATION</span>
            </div>
            <div className="hidden sm:flex items-center space-x-4 text-[11px] text-slate-500">
              <span>MODEL: DETERMINISTIC</span>
              <span>SLIPPAGE: INCLUDED</span>
              <span>LOOK-AHEAD: 0.00%</span>
            </div>
          </div>

          {/* Abstract SVG Financial Time-Series Visual */}
          <div className="w-full h-48 sm:h-64 relative flex items-center justify-center">
            <svg
              className="w-full h-full text-cyan-500"
              viewBox="0 0 800 240"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#06B6D4" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="goldGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="btcGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#F7931A" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#F7931A" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="0" y1="40" x2="800" y2="40" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="0" y1="100" x2="800" y2="100" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="0" y1="160" x2="800" y2="160" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="0" y1="220" x2="800" y2="220" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />

              <line x1="200" y1="0" x2="200" y2="240" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="400" y1="0" x2="400" y2="240" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />
              <line x1="600" y1="0" x2="600" y2="240" stroke="#1E293B" strokeWidth="1" strokeDasharray="3 3" />

              {/* Abstract Curve 1: NVIDIA Momentum (Teal/Lime) */}
              <path
                d="M0,190 C120,175 220,120 340,135 C460,150 560,70 680,60 C730,55 770,30 800,20"
                stroke="#10B981"
                strokeWidth="2.5"
                strokeLinecap="round"
              />

              {/* Abstract Curve 2: Gold Safe-Haven (Gold) */}
              <path
                d="M0,150 C140,145 280,160 420,130 C560,105 700,95 800,75"
                stroke="#F59E0B"
                strokeWidth="2"
                strokeDasharray="4 2"
                strokeLinecap="round"
              />

              {/* Abstract Curve 3: Backtest Strategy Portfolio (Cyan with Gradient Fill) */}
              <path
                d="M0,210 C100,200 200,160 300,140 C400,120 500,80 600,65 C700,50 750,35 800,25 L800,240 L0,240 Z"
                fill="url(#cyanGrad)"
              />
              <path
                d="M0,210 C100,200 200,160 300,140 C400,120 500,80 600,65 C700,50 750,35 800,25"
                stroke="#06B6D4"
                strokeWidth="3"
                strokeLinecap="round"
              />

              {/* Data Nodes on Strategy Curve */}
              <circle cx="300" cy="140" r="4" fill="#06B6D4" stroke="#06090E" strokeWidth="2" />
              <circle cx="600" cy="65" r="4" fill="#06B6D4" stroke="#06090E" strokeWidth="2" />
              <circle cx="800" cy="25" r="4" fill="#10B981" stroke="#06090E" strokeWidth="2" />
            </svg>

            {/* Overlay Telemetry Legend */}
            <div className="absolute bottom-3 left-3 bg-[#06090E]/90 border border-[#1E293B] px-3 py-1.5 rounded flex items-center space-x-3 text-[10px] font-mono">
              <span className="flex items-center space-x-1 text-cyan-400">
                <span className="w-2.5 h-0.5 bg-cyan-400 inline-block"></span>
                <span>Strategy Backtest</span>
              </span>
              <span className="flex items-center space-x-1 text-amber-400">
                <span className="w-2.5 h-0.5 bg-amber-400 inline-block"></span>
                <span>Gold Baseline</span>
              </span>
              <span className="flex items-center space-x-1 text-emerald-400">
                <span className="w-2.5 h-0.5 bg-emerald-400 inline-block"></span>
                <span>NVIDIA Momentum</span>
              </span>
            </div>
          </div>
        </div>

        {/* 6 Core Quantitative Capabilities */}
        <div className="w-full max-w-5xl mb-16">
          <div className="text-center mb-8">
            <h2 className="text-xs font-mono uppercase tracking-widest text-slate-500 font-semibold">
              Systematic Workflow
            </h2>
            <p className="text-lg font-bold text-white font-mono mt-1">
              End-to-End Quantitative Pipeline
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-left">
            {/* 1 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <TrendingUp className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">1. Multi-Asset Analysis</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Analyze historical OHLCV data across Gold, Bitcoin, and NVIDIA with institutional candle metrics.
              </p>
            </div>

            {/* 2 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <BarChart2 className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">2. Quantitative Indicators</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Compute moving averages (SMA/EMA), compounding daily returns, annualized volatility, Sharpe, and drawdowns.
              </p>
            </div>

            {/* 3 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <GitMerge className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">3. Cross-Asset Correlation</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Evaluate pairwise Pearson correlation matrices, covariance dynamics, and rolling window co-movements.
              </p>
            </div>

            {/* 4 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <Cpu className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">4. Systematic Strategies</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Configure SMA Crossover, EMA Trend, Momentum, and Mean Reversion rules with zero look-ahead bias.
              </p>
            </div>

            {/* 5 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <PlayCircle className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">5. Portfolio Backtesting</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Simulate portfolio equity growth against Buy-and-Hold benchmark with realistic trading fees and slippage.
              </p>
            </div>

            {/* 6 */}
            <div className="bg-[#0D111A] border border-[#1E293B] p-5 rounded-lg hover:border-cyan-500/40 transition-colors">
              <div className="w-8 h-8 rounded bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 mb-3">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-semibold text-slate-100 font-mono mb-1">6. Risk & Regime Evaluation</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Stress-test parameters with Monte Carlo simulation and classify performance across macroeconomic regimes.
              </p>
            </div>
          </div>
        </div>

        {/* Institutional Integrity Guarantee Bar */}
        <div className="w-full max-w-5xl bg-[#0D111A]/60 border border-[#1E293B] p-4 rounded-lg flex items-center justify-between flex-wrap gap-4 text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-cyan-400" />
            <span>Mathematical Integrity: Python SciPy Engine • Zero Synthetic Market Data</span>
          </div>
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-emerald-400" />
            <span>Target Datasets: Kaggle Gold • Bitcoin • NVIDIA</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#1E293B] bg-[#06090E] px-6 py-6 text-center text-xs text-slate-500 font-mono">
        QUANTLAB • Quantitative Multi-Asset Financial Intelligence & Backtesting Platform
      </footer>
    </div>
  );
};
