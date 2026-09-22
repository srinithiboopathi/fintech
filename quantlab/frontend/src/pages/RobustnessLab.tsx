import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { AnalyticsApi } from '../services/analyticsApi';
import { MonteCarloResult, SensitivityResponse } from '../types';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { ShieldAlert, Play, RefreshCw, BarChart2, Award, Sliders } from 'lucide-react';

export const RobustnessLab: React.FC = () => {
  const [symbol, setSymbol] = useState('NVDA');
  const [strategyId, setStrategyId] = useState('sma_crossover');
  const [simulations, setSimulations] = useState(300);
  const [horizon, setHorizon] = useState(252);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MonteCarloResult | null>(null);
  const [sensitivity, setSensitivity] = useState<SensitivityResponse | null>(null);

  const runSimulation = () => {
    setLoading(true);
    Promise.all([
      AnalyticsApi.getMonteCarlo(symbol, simulations, horizon),
      AnalyticsApi.getParameterSensitivity(symbol, strategyId),
    ])
      .then(([mcRes, sensRes]) => {
        setResult(mcRes);
        setSensitivity(sensRes);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to run robustness tests:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    runSimulation();
  }, [symbol, strategyId]);

  const totalWidth = 800;
  const height = 300;

  // Compute scale
  let minVal = 50000;
  let maxVal = 250000;
  if (result?.p95_equity_curve?.length) {
    maxVal = Math.max(...result.p95_equity_curve) * 1.05;
    minVal = Math.min(...result.p5_equity_curve) * 0.95;
  }

  const getY = (v: number) => {
    if (maxVal === minVal) return height / 2;
    return height - ((v - minVal) / (maxVal - minVal)) * height;
  };

  const getPath = (curve: number[]) => {
    return curve.reduce((acc, v, idx) => {
      const x = (idx / (curve.length - 1 || 1)) * totalWidth;
      const y = getY(v);
      return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, '');
  };

  return (
    <PageContainer
      title="Monte Carlo & Robustness Lab"
      subtitle="Statistical stress-testing, bootstrap resampling, and parameter sensitivity stability"
      actions={
        <div className="flex flex-wrap items-center gap-3">
          <Select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            options={[
              { value: 'NVDA', label: 'NVIDIA (NVDA)' },
              { value: 'BTC-USD', label: 'Bitcoin (BTC)' },
              { value: 'GC=F', label: 'Gold (GC=F)' },
            ]}
          />
          <Select
            value={strategyId}
            onChange={(e) => setStrategyId(e.target.value)}
            options={[
              { value: 'sma_crossover', label: 'Dual SMA Golden Cross' },
              { value: 'ema_trend', label: 'Triple EMA Trend Ribbon' },
              { value: 'momentum', label: 'Momentum Breakout' },
              { value: 'mean_reversion', label: 'Bollinger Mean Reversion' },
            ]}
          />
          <Button
            variant="glow"
            size="sm"
            onClick={runSimulation}
            isLoading={loading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Run Resampling
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Metric Confidence Cards */}
        {result?.metrics && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
            <Card variant="glass" className="p-5 border-emerald-500/20 space-y-1">
              <span className="text-xs text-slate-400">95th Percentile (Optimistic)</span>
              <div className="text-2xl font-black text-emerald-400">
                {formatCurrency(result.metrics.terminal_wealth_p95)}
              </div>
              <div className="text-xs text-slate-300">
                Sharpe: {result.metrics.sharpe_p95.toFixed(2)} | Max DD: {result.metrics.max_drawdown_p95}%
              </div>
            </Card>

            <Card variant="glass" className="p-5 border-cyan-500/20 space-y-1">
              <span className="text-xs text-slate-400">50th Percentile (Median Expected)</span>
              <div className="text-2xl font-black text-cyan-400">
                {formatCurrency(result.metrics.terminal_wealth_p50)}
              </div>
              <div className="text-xs text-slate-300">
                Sharpe: {result.metrics.sharpe_p50.toFixed(2)} | Max DD: {result.metrics.max_drawdown_p50}%
              </div>
            </Card>

            <Card variant="glass" className="p-5 border-rose-500/20 space-y-1">
              <span className="text-xs text-slate-400">5th Percentile (Stress / Tail Risk)</span>
              <div className="text-2xl font-black text-rose-400">
                {formatCurrency(result.metrics.terminal_wealth_p5)}
              </div>
              <div className="text-xs text-slate-300">
                Sharpe: {result.metrics.sharpe_p5.toFixed(2)} | Max DD: {result.metrics.max_drawdown_p5}%
              </div>
            </Card>
          </div>
        )}

        {/* Monte Carlo Fan Chart */}
        <Card variant="glass" className="p-5 border border-slate-800">
          <div className="flex flex-wrap items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Resampled Equity Growth Paths (N = {simulations} Simulations, 252 Days)
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Synthetic bootstrap paths demonstrating probability distribution of terminal capital
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2.5 h-0.5 bg-emerald-400" /> 95th Percentile
              </span>
              <span className="flex items-center gap-1 text-cyan-400">
                <span className="w-2.5 h-0.5 bg-cyan-400" /> Median (50th)
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="w-2.5 h-0.5 bg-rose-400" /> 5th Percentile
              </span>
            </div>
          </div>

          <div className="relative w-full">
            <svg viewBox={`0 0 ${totalWidth} ${height}`} className="w-full h-auto overflow-visible select-none">
              {/* Sample Random Paths (Faint Lines) */}
              {result?.sample_trajectories?.map((traj, idx) => (
                <path
                  key={idx}
                  d={getPath(traj)}
                  fill="none"
                  stroke="rgba(56, 189, 248, 0.12)"
                  strokeWidth="1"
                />
              ))}

              {/* 5th Percentile */}
              {result?.p5_equity_curve?.length && (
                <path d={getPath(result.p5_equity_curve)} fill="none" stroke="#ff3366" strokeWidth="2.5" />
              )}

              {/* Median 50th Percentile */}
              {result?.p50_equity_curve?.length && (
                <path d={getPath(result.p50_equity_curve)} fill="none" stroke="#00d8ff" strokeWidth="3" />
              )}

              {/* 95th Percentile */}
              {result?.p95_equity_curve?.length && (
                <path d={getPath(result.p95_equity_curve)} fill="none" stroke="#00f5a0" strokeWidth="2.5" />
              )}
            </svg>
          </div>
        </Card>

        {/* Parameter Sensitivity Grid */}
        {sensitivity?.results && sensitivity.results.length > 0 && (
          <Card variant="glass" className="p-5 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100 font-mono">
                  Parameter Sensitivity & Friction Stability Grid ({sensitivity.total_permutations} Permutations)
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Strategy: {strategyId} | Asset: {symbol}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono">
                <thead className="bg-slate-900 text-slate-400">
                  <tr>
                    <th className="p-2.5 text-left">Parameters</th>
                    <th className="p-2.5 text-right">Commission (bps)</th>
                    <th className="p-2.5 text-right">Return</th>
                    <th className="p-2.5 text-right">Sharpe</th>
                    <th className="p-2.5 text-right">Max DD</th>
                    <th className="p-2.5 text-right">Trades</th>
                    <th className="p-2.5 text-right">Profit Factor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {sensitivity.results.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30">
                      <td className="p-2.5 text-slate-300">
                        {Object.entries(item.parameters)
                          .map(([k, v]) => `${k}=${v}`)
                          .join(', ')}
                      </td>
                      <td className="p-2.5 text-right text-slate-400">{item.commission_bps} bps</td>
                      <td className={`p-2.5 text-right font-bold ${item.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {item.total_return_pct >= 0 ? '+' : ''}{item.total_return_pct.toFixed(2)}%
                      </td>
                      <td className="p-2.5 text-right text-cyan-400 font-semibold">{item.sharpe_ratio.toFixed(2)}</td>
                      <td className="p-2.5 text-right text-rose-400">-{item.max_drawdown_pct.toFixed(2)}%</td>
                      <td className="p-2.5 text-right text-slate-300">{item.total_trades}</td>
                      <td className="p-2.5 text-right text-slate-200">{item.profit_factor.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </PageContainer>
  );
};

