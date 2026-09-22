import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { AnalyticsApi } from '../services/analyticsApi';
import { ResearchReportResponse } from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { getRegimeBadgeColor } from '../utils/colors';
import { Printer, CheckCircle2, ShieldAlert, Award, Activity, TrendingUp, BarChart2, RefreshCw } from 'lucide-react';

export const ResearchReport: React.FC = () => {
  const [symbol, setSymbol] = useState('NVDA');
  const [report, setReport] = useState<ResearchReportResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    AnalyticsApi.getResearchReport(symbol)
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load report:', err);
        setLoading(false);
      });
  }, [symbol]);

  const handlePrint = () => {
    window.print();
  };

  const perf = report?.performance_metrics;
  const backtest = report?.baseline_backtest;
  const regimeBadge = getRegimeBadgeColor(report?.current_market_regime || 'Consolidation');

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
              {report && (
                <span className="text-[11px] font-mono text-slate-400 block mt-0.5">
                  ID: {report.report_id} | Range: {report.date_range.start_date} to {report.date_range.end_date} ({report.date_range.total_bars} bars)
                </span>
              )}
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
              Quantitative evaluation of <strong>{symbol}</strong> indicates an annualized CAGR of{' '}
              <strong className="text-emerald-400">{perf ? formatPercent(perf.cagr_pct, 2, false) : '...'}</strong> with a realized annualized volatility of{' '}
              <strong className="text-cyan-400">{perf ? formatPercent(perf.annualized_volatility_pct, 2, false) : '...'}</strong> and a Sharpe ratio of{' '}
              <strong className="text-slate-100">{perf ? perf.sharpe_ratio.toFixed(2) : '...'}</strong>. Current market state is classified as{' '}
              <span className={`px-2 py-0.5 text-[11px] font-bold rounded ${regimeBadge.bg} ${regimeBadge.text} border ${regimeBadge.border}`}>
                {report?.current_market_regime || 'Analyzing...'}
              </span>
              . Tail risk is bounded with 1-day 95% Historical VaR estimated at{' '}
              <strong className="text-rose-400">{perf ? formatPercent(perf.var_95_pct, 2, false) : '...'}</strong> (CVaR: {perf ? formatPercent(perf.cvar_95_pct, 2, false) : '...'}).
            </p>
          </div>

          {/* Key Quantitative Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-slate-800 font-mono text-xs">
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Annualized CAGR</span>
              <span className="text-emerald-400 font-bold text-sm">
                {perf ? formatPercent(perf.cagr_pct, 2, false) : '...'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Sharpe / Sortino</span>
              <span className="text-cyan-400 font-bold text-sm">
                {perf ? `${perf.sharpe_ratio.toFixed(2)} / ${perf.sortino_ratio.toFixed(2)}` : '...'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Max Drawdown</span>
              <span className="text-rose-400 font-bold text-sm">
                {perf ? `-${perf.max_drawdown_pct.toFixed(2)}%` : '...'}
              </span>
            </div>
            <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
              <span className="text-slate-400 block text-[10px]">Calmar Ratio</span>
              <span className="text-purple-400 font-bold text-sm">
                {perf ? perf.calmar_ratio.toFixed(2) : '...'}
              </span>
            </div>
          </div>
        </Card>

        {/* Deep Dive Performance & Risk Factor Attribution */}
        {perf && (
          <Card variant="glass" className="p-6 border border-slate-800 space-y-4">
            <h4 className="text-xs font-bold uppercase text-slate-300 font-mono">
              Comprehensive Statistical Risk & Return Matrix
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Total Cumulative Return</span>
                <span className="text-emerald-400 font-bold text-sm">+{perf.total_cumulative_return_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Annualized Volatility</span>
                <span className="text-slate-100 font-bold text-sm">{perf.annualized_volatility_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Downside Volatility</span>
                <span className="text-slate-100 font-bold text-sm">{perf.downside_volatility_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Max DD Duration</span>
                <span className="text-slate-100 font-bold text-sm">{perf.max_drawdown_duration_days} Days</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Historical VaR 95%</span>
                <span className="text-rose-400 font-bold text-sm">{perf.var_95_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Conditional VaR 95%</span>
                <span className="text-rose-400 font-bold text-sm">{perf.cvar_95_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Period High / Low</span>
                <span className="text-slate-100 font-bold text-sm">
                  {report ? `${formatCurrency(report.price_summary.period_high)} / ${formatCurrency(report.price_summary.period_low)}` : '...'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <span className="text-slate-400 block text-[11px]">Latest Close Price</span>
                <span className="text-emerald-400 font-bold text-sm">
                  {report ? formatCurrency(report.price_summary.latest_close) : '...'}
                </span>
              </div>
            </div>
          </Card>
        )}

        {/* Baseline Strategy Backtest Tear Sheet */}
        {backtest && (
          <Card variant="glass" className="p-6 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h4 className="text-xs font-bold uppercase text-slate-300 font-mono">
                Baseline Strategy Backtest Benchmark: {backtest.strategy}
              </h4>
              <span className="text-xs font-mono text-emerald-400 font-semibold">
                Trades: {backtest.total_trades}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Strategy Return</span>
                <span className="text-emerald-400 font-bold text-sm">+{backtest.total_return_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Buy & Hold Return</span>
                <span className="text-cyan-400 font-bold text-sm">+{backtest.benchmark_return_pct.toFixed(2)}%</span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Alpha vs Benchmark</span>
                <span className={`font-bold text-sm ${backtest.alpha_excess_return_pct >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {backtest.alpha_excess_return_pct >= 0 ? '+' : ''}{backtest.alpha_excess_return_pct.toFixed(2)}%
                </span>
              </div>
              <div className="p-3 bg-slate-900/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Strategy Sharpe / Max DD</span>
                <span className="text-slate-100 font-bold text-sm">
                  {backtest.sharpe_ratio.toFixed(2)} / -{backtest.max_drawdown_pct.toFixed(2)}%
                </span>
              </div>
            </div>
          </Card>
        )}

        {/* Peer Asset Correlation Profile */}
        {report?.correlation_profile && Object.keys(report.correlation_profile).length > 0 && (
          <Card variant="glass" className="p-6 border border-slate-800 space-y-3">
            <h4 className="text-xs font-bold uppercase text-slate-300 font-mono">
              Aligned Peer Asset Correlation Profile (Pearson)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
              {Object.entries(report.correlation_profile).map(([peerSym, corrVal]) => (
                <div key={peerSym} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-300 font-semibold">{symbol} vs {peerSym}</span>
                    <span className={`font-bold ${corrVal >= 0.5 ? 'text-emerald-400' : corrVal <= 0 ? 'text-cyan-400' : 'text-slate-200'}`}>
                      r = {corrVal.toFixed(3)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${corrVal >= 0 ? 'bg-cyan-400' : 'bg-rose-500'}`}
                      style={{ width: `${Math.min(100, Math.abs(corrVal) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Investment Committee Verdict */}
        <Card variant="glow" className="p-6 border-emerald-500/30">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-slate-100 font-mono">
                Systematic Recommendation: OVERWEIGHT DIVERSIFICATION
              </h4>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                Quantitative factors for {symbol} indicate robust risk-adjusted returns under systematic execution regimes with bounded downside volatility.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};

