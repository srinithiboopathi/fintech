import React, { useState } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { formatCurrency, formatPercent } from '../../utils/formatters';
import { FileText, Printer, Download, CheckCircle2, ShieldAlert, Award } from 'lucide-react';

export const ResearchReport: React.FC = () => {
  const [symbol, setSymbol] = useState('NVDA');

  const handlePrint = () => {
    window.print();
  };

  return (
    <PageContainer
      title="Institutional Quantitative Research Tear Sheet"
      subtitle="Comprehensive multi-factor risk attribution and algorithmic backtest report"
      actions={
        <div className="flex items-center gap-3">
          <Select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            options={[
              { value: 'NVDA', label: 'NVIDIA Corporation (NVDA)' },
              { value: 'BTC-USD', label: 'Bitcoin Core (BTC-USD)' },
              { value: 'GC=F', label: 'Gold Continuous (GC=F)' },
            ]}
          />
          <Button
            variant="glow"
            size="sm"
            onClick={handlePrint}
            leftIcon={<Printer className="w-3.5 h-3.5" />}
          >
            Print / Export PDF
          </Button>
        </div>
      }
    >
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Document Header */}
        <Card variant="glass" className="p-6 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
            <div>
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block">
                QuantLab Institutional Teardown
              </span>
              <h2 className="text-xl font-black text-slate-100 mt-0.5">
                Factor & Risk Tear Sheet: {symbol}
              </h2>
            </div>
            <div className="text-right text-xs font-mono text-slate-400">
              <div>Date: {new Date().toLocaleDateString('en-US', { dateStyle: 'long' })}</div>
              <div className="text-emerald-400 font-semibold">Tier: ENTERPRISE PRO</div>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase text-slate-300 font-mono">
              Executive Research Summary
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              Quantitative evaluation of {symbol} indicates significant momentum factor loading coupled with favorable risk-adjusted Sharpe ratios under trend-following systematic regimes. Tail risk is bounded with 95% 1-day Value at Risk estimated at 3.6% and expected recovery duration within 22 trading sessions.
            </p>
          </div>

          {/* Key Quantitative Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800 font-mono text-xs">
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">CAGR</span>
              <span className="text-emerald-400 font-bold text-sm">+58.4%</span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Annualized Sharpe</span>
              <span className="text-cyan-400 font-bold text-sm">2.34</span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Max Drawdown</span>
              <span className="text-rose-400 font-bold text-sm">-14.2%</span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Profit Factor</span>
              <span className="text-purple-400 font-bold text-sm">2.35</span>
            </div>
          </div>
        </Card>

        {/* Multi-Factor Loadings */}
        <Card variant="glass" className="p-6 border border-slate-800 space-y-3">
          <h4 className="text-xs font-bold uppercase text-slate-300 font-mono">
            Multi-Factor Decomposition (Fama-French + Momentum)
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Market Beta (β)</span>
                <span className="text-slate-200 font-bold">1.18</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div className="bg-cyan-400 h-full w-[70%]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Momentum Factor (MOM)</span>
                <span className="text-emerald-400 font-bold">+0.84</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-400 h-full w-[84%]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Volatility Risk (VOL)</span>
                <span className="text-rose-400 font-bold">0.62</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div className="bg-rose-500 h-full w-[62%]" />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Quality / Cash Flow (Q)</span>
                <span className="text-purple-400 font-bold">0.78</span>
              </div>
              <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                <div className="bg-purple-400 h-full w-[78%]" />
              </div>
            </div>
          </div>
        </Card>

        {/* Investment Committee Verdict */}
        <Card variant="glow" className="p-6 border-emerald-500/30">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-slate-100 font-mono">
                Systematic Recommendation: OVERWEIGHT DIVERSIFICATION
              </h4>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                Strategy exhibits strong alpha generation across 2021-2024 historical cycles with high resilience to volatility shocks.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};
