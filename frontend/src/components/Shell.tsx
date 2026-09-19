import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Activity, CheckCircle2, AlertCircle, ShieldCheck, Layers, Server } from 'lucide-react';
import { checkHealth, HealthCheckResponse } from '../lib/api';
import { useAppStore } from '../store/useAppStore';

export const Shell: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const { backendHealthy, setBackendHealthy } = useAppStore();

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const data = await checkHealth();
        setHealthData(data);
        setBackendHealthy(data.status === 'healthy');
        setError(null);
      } catch (err: any) {
        const errorMsg = err.message || 'Unable to connect to backend API';
        setError(errorMsg);
        setBackendHealthy(false);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
  }, [setBackendHealthy]);

  // Minimal diagnostic chart option strictly to verify Apache ECharts installation
  const chartOption = {
    backgroundColor: 'transparent',
    grid: { top: 10, right: 10, bottom: 20, left: 30 },
    xAxis: {
      type: 'category',
      data: ['T1', 'T2', 'T3', 'T4', 'T5'],
      axisLine: { lineStyle: { color: '#232E42' } },
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#161F2E' } },
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    series: [
      {
        data: [10, 25, 18, 30, 22],
        type: 'line',
        smooth: true,
        color: '#06B6D4',
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(6, 182, 212, 0.3)' },
              { offset: 1, color: 'rgba(6, 182, 212, 0.0)' }
            ]
          }
        }
      }
    ]
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="border-b border-[#232E42] bg-[#111722]/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-lg">
            QL
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-semibold tracking-wide text-white">QUANTLAB</h1>
              <span className="text-xs font-mono uppercase bg-cyan-950 text-cyan-400 border border-cyan-800 px-2 py-0.5 rounded">
                Phase 0 Foundation
              </span>
            </div>
            <p className="text-xs text-slate-400">Quantitative Multi-Asset Financial Intelligence & Backtesting Platform</p>
          </div>
        </div>

        {/* Backend Status Indicator */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-[#161F2E] border border-[#232E42] px-3 py-1.5 rounded text-xs font-mono">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Backend:</span>
            {loading ? (
              <span className="text-yellow-400 animate-pulse">Checking...</span>
            ) : backendHealthy ? (
              <span className="text-emerald-400 flex items-center space-x-1" title={healthData?.app_name || 'Healthy'}>
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-ping"></span>
                <span>Healthy ({healthData?.status})</span>
              </span>
            ) : (
              <span className="text-rose-400 flex items-center space-x-1" title={error || 'Connection error'}>
                <AlertCircle className="w-3.5 h-3.5 inline" />
                <span>Offline</span>
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 flex flex-col justify-center">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Phase 0 Architecture Status */}
          <div className="md:col-span-2 bg-[#111722] border border-[#232E42] rounded-lg p-6 shadow-xl">
            <div className="flex items-center space-x-3 mb-4">
              <ShieldCheck className="w-6 h-6 text-cyan-400" />
              <div>
                <h2 className="text-lg font-semibold text-slate-100">Project Foundation Initialized</h2>
                <p className="text-xs text-slate-400">Phase 0 Architecture and Repository Setup Completed</p>
              </div>
            </div>

            <div className="space-y-3 mt-4 text-sm">
              <div className="flex items-center justify-between p-3 bg-[#161F2E] rounded border border-[#232E42]/60">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-200">Git Branch & Safety</span>
                </div>
                <span className="font-mono text-xs text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                  feature/quantlab-platform
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-[#161F2E] rounded border border-[#232E42]/60">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-200">Frontend Technology Stack</span>
                </div>
                <span className="font-mono text-xs text-slate-400">
                  React 18 • TypeScript • Vite • Tailwind • ECharts
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-[#161F2E] rounded border border-[#232E42]/60">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-200">Backend Technology Stack</span>
                </div>
                <span className="font-mono text-xs text-slate-400">
                  FastAPI • Pandas • NumPy • SciPy • SQLAlchemy
                </span>
              </div>

              <div className="flex items-center justify-between p-3 bg-[#161F2E] rounded border border-[#232E42]/60">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-slate-200">Dataset Isolation & Integrity</span>
                </div>
                <span className="font-mono text-xs text-amber-400">
                  Awaiting Phase 2 Real Datasets
                </span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-[#232E42] flex items-center justify-between text-xs text-slate-400">
              <span>FastAPI Endpoint: <code className="text-cyan-400 font-mono">GET /health</code></span>
              <span className="font-mono">Ready for Phase 1 Shell & Routing</span>
            </div>
          </div>

          {/* ECharts & Environment Verification Card */}
          <div className="bg-[#111722] border border-[#232E42] rounded-lg p-6 flex flex-col justify-between shadow-xl">
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <Layers className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-semibold text-slate-200">ECharts Engine Verification</h3>
              </div>
              <p className="text-xs text-slate-400 mb-4">
                Verifying rendering engine capability for institutional time-series analytics.
              </p>
              <div className="h-32 w-full bg-[#161F2E] rounded border border-[#232E42] p-2">
                <ReactECharts option={chartOption} style={{ height: '100%', width: '100%' }} />
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-[#232E42] flex items-center justify-between text-xs">
              <span className="text-slate-400">Engine Status:</span>
              <span className="text-emerald-400 font-mono flex items-center space-x-1">
                <Activity className="w-3 h-3 animate-pulse" />
                <span>Operational</span>
              </span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#232E42] bg-[#111722]/50 px-6 py-3 text-center text-xs text-slate-500 font-mono">
        QUANTLAB v0.1.0 • Multi-Asset Financial Intelligence & Backtesting System
      </footer>
    </div>
  );
};
