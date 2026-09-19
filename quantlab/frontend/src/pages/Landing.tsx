import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  TrendingUp,
  GitCompare,
  Sliders,
  ShieldCheck,
  Zap,
  BarChart3,
  Layers,
  Cpu,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

export const Landing: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col relative overflow-hidden bg-grid-pattern">
      {/* Glow Orbs */}
      <div className="absolute top-10 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-500/15 via-emerald-500/10 to-transparent blur-3xl pointer-events-none rounded-full" />
      <div className="absolute top-[40%] right-[-100px] w-[400px] h-[400px] bg-purple-500/10 blur-3xl pointer-events-none rounded-full" />

      {/* Top Bar */}
      <header className="w-full glass-panel border-b border-slate-800/80 px-6 py-4 flex items-center justify-between z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-400 to-cyan-400 p-0.5 shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#080c14] rounded-[10px] flex items-center justify-center">
              <Activity className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <span className="text-lg font-black tracking-tight text-white">
            QUANT<span className="text-emerald-400">LAB</span>
          </span>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">
              Sign In
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="glow" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Launch Terminal
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 py-16 lg:py-24 z-10 max-w-5xl mx-auto space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          QuantLab Institutional v1.0 Released
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-100 max-w-4xl leading-[1.1]">
          Institutional <span className="text-gradient-cyan-emerald">Quantitative Research</span> & Systematic Backtesting
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-2xl leading-relaxed">
          Engineered for algorithmic traders and portfolio managers. Run high-speed multi-asset simulations, cross-asset correlation analysis, market regime detection, and Monte Carlo stress testing.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <Link to="/dashboard">
            <Button variant="glow" size="lg" rightIcon={<ArrowRight className="w-5 h-5" />}>
              Open Quant Dashboard
            </Button>
          </Link>
          <Link to="/backtesting">
            <Button variant="secondary" size="lg" leftIcon={<Zap className="w-5 h-5 text-cyan-400" />}>
              Run Strategy Simulator
            </Button>
          </Link>
        </div>

        {/* Live Interactive Terminal Teaser */}
        <div className="w-full pt-8">
          <Card variant="glow" className="text-left border-cyan-500/30 bg-slate-950/80 p-6 rounded-2xl shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="text-xs font-mono text-slate-400 ml-2">quantlab_terminal_session.py</span>
              </div>
              <span className="text-[11px] font-mono text-emerald-400">STATUS: VECTORIZED_OPTIMAL</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 font-mono text-xs">
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 mb-1">Active Model</div>
                <div className="text-emerald-400 font-bold text-sm">Dual SMA Golden Cross</div>
                <div className="text-[11px] text-slate-500 mt-1">NVIDIA / BTC Dynamic Parity</div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 mb-1">Simulated 1Y Sharpe</div>
                <div className="text-cyan-400 font-bold text-sm">2.48 (Sortino: 3.25)</div>
                <div className="text-[11px] text-slate-500 mt-1">Max DD: -12.4% vs Bench -38.6%</div>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <div className="text-slate-400 mb-1">Regime State</div>
                <div className="text-purple-400 font-bold text-sm">Bull Trend (Moderate Vol)</div>
                <div className="text-[11px] text-slate-500 mt-1">Confidence Score: 88.4%</div>
              </div>
            </div>
          </Card>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12 text-left w-full">
          <Card variant="glass" className="p-6 space-y-3 hover:border-emerald-500/40">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Multi-Asset Candlestick Engine</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Real-time interactive candlestick rendering with moving average ribbons, RSI, MACD, Bollinger Bands, and volume metrics.
            </p>
          </Card>

          <Card variant="glass" className="p-6 space-y-3 hover:border-cyan-500/40">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Correlation & Decoupling Lab</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              NxN Pearson and Spearman correlation heatmaps and rolling correlation time series across traditional commodities, crypto, and equities.
            </p>
          </Card>

          <Card variant="glass" className="p-6 space-y-3 hover:border-purple-500/40">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-base text-slate-100">Monte Carlo Robustness</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Stress-test quantitative alpha across 1,000 synthetic return trajectories to ensure real statistical robustness before live deployment.
            </p>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="glass-panel border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 font-mono z-10">
        QuantLab Platform © 2026. Built with FastAPI, React, TypeScript, and Vectorized NumPy Engines.
      </footer>
    </div>
  );
};
