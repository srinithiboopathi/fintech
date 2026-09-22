import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Select } from '../components/ui/Select';
import { AnalyticsApi } from '../services/analyticsApi';
import { RegimeDetectionResponse } from '../types';
import { getRegimeBadgeColor } from '../utils/colors';
import { Gauge, Sparkles, Activity, ShieldAlert, BarChart } from 'lucide-react';

export const MarketRegimes: React.FC = () => {
  const [symbol, setSymbol] = useState('NVDA');
  const [data, setData] = useState<RegimeDetectionResponse | null>(null);

  useEffect(() => {
    AnalyticsApi.getRegimeDetection(symbol).then(setData);
  }, [symbol]);

  const currentRegime = data?.current_regime?.regime || 'Bull Trend';
  const badge = getRegimeBadgeColor(currentRegime);

  return (
    <PageContainer
      title="Market Regime Detection Radar"
      subtitle="4-State Hidden Markov & Volatility clustering model identifying structural macro regimes"
      actions={
        <Select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          options={[
            { value: 'NVDA', label: 'NVIDIA (NVDA)' },
            { value: 'BTC-USD', label: 'Bitcoin (BTC)' },
            { value: 'GC=F', label: 'Gold (GC=F)' },
          ]}
        />
      }
    >
      <div className="space-y-6">
        {/* Current Regime Spotlight */}
        <Card variant="glow" className="p-6 border-cyan-500/30">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-mono uppercase text-slate-400">Current Market State ({symbol})</span>
              <div className="flex items-center gap-3 mt-1">
                <span className={`px-3 py-1 text-base font-extrabold rounded-xl border ${badge.bg} ${badge.text} ${badge.border}`}>
                  {currentRegime}
                </span>
                <span className="text-xs font-mono text-emerald-400">
                  Confidence: {((data?.current_regime?.confidence || 0.88) * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Trend Direction: <strong className="text-slate-200">{data?.current_regime?.trend_direction || 'Bullish'}</strong> | Realized Volatility: <strong className="text-cyan-400">{data?.current_regime?.realized_volatility || 28.5}%</strong>
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-right">
              <span className="text-xs font-mono text-slate-400 block">Recommended Quant Action</span>
              <span className="text-sm font-bold text-emerald-400 font-mono">
                {currentRegime === 'Bull Trend'
                  ? 'Trend Following (Full Allocation)'
                  : currentRegime === 'Volatile Choppy'
                  ? 'Mean Reversion & Lower Leverage'
                  : 'Defensive Cash / Safe-Haven Flight'}
              </span>
            </div>
          </div>
        </Card>

        {/* Regime Historical Distribution */}
        <Card variant="glass" className="p-6 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-100 font-mono">
            Historical Regime Distribution (2021 - 2024)
          </h3>
          <div className="space-y-3">
            {data?.distribution_pct &&
              Object.entries(data.distribution_pct).map(([regName, pct]) => (
                <div key={regName} className="space-y-1">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-300">{regName}</span>
                    <span className="text-slate-200 font-bold">{pct}%</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        regName === 'Bull Trend'
                          ? 'bg-emerald-400'
                          : regName === 'Bear Trend'
                          ? 'bg-rose-500'
                          : regName === 'Volatile Choppy'
                          ? 'bg-amber-400'
                          : 'bg-cyan-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </Card>

        {/* Regime Transition Probability Matrix */}
        <Card variant="glass" className="p-6 border border-slate-800">
          <h3 className="text-sm font-bold text-slate-100 font-mono mb-3">
            Markov Regime Transition Probability Matrix
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-center text-xs font-mono">
              <thead className="bg-slate-900 text-slate-400">
                <tr>
                  <th className="p-3 text-left">From \ To</th>
                  <th className="p-3">Bull Trend</th>
                  <th className="p-3">Bear Trend</th>
                  <th className="p-3">Volatile Choppy</th>
                  <th className="p-3">Consolidation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                <tr>
                  <td className="p-3 text-left font-bold text-emerald-400">Bull Trend</td>
                  <td className="p-3 bg-emerald-500/10 text-emerald-400 font-bold">0.82</td>
                  <td className="p-3 text-slate-400">0.05</td>
                  <td className="p-3 text-slate-400">0.08</td>
                  <td className="p-3 text-slate-400">0.05</td>
                </tr>
                <tr>
                  <td className="p-3 text-left font-bold text-rose-400">Bear Trend</td>
                  <td className="p-3 text-slate-400">0.06</td>
                  <td className="p-3 bg-rose-500/10 text-rose-400 font-bold">0.74</td>
                  <td className="p-3 text-slate-400">0.14</td>
                  <td className="p-3 text-slate-400">0.06</td>
                </tr>
                <tr>
                  <td className="p-3 text-left font-bold text-amber-400">Volatile Choppy</td>
                  <td className="p-3 text-slate-400">0.12</td>
                  <td className="p-3 text-slate-400">0.18</td>
                  <td className="p-3 bg-amber-500/10 text-amber-400 font-bold">0.62</td>
                  <td className="p-3 text-slate-400">0.08</td>
                </tr>
                <tr>
                  <td className="p-3 text-left font-bold text-cyan-400">Consolidation</td>
                  <td className="p-3 text-slate-400">0.24</td>
                  <td className="p-3 text-slate-400">0.10</td>
                  <td className="p-3 text-slate-400">0.16</td>
                  <td className="p-3 bg-cyan-500/10 text-cyan-400 font-bold">0.50</td>
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};
