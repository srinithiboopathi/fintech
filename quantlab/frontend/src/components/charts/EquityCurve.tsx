import React, { useState } from 'react';
import { EquityPoint } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface EquityCurveProps {
  data: EquityPoint[];
  title?: string;
  height?: number;
}

export const EquityCurve: React.FC<EquityCurveProps> = ({
  data,
  title = 'Portfolio Equity vs Benchmark',
  height = 280,
}) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const totalWidth = 800;

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-slate-500 font-mono">No simulation data available.</div>;
  }

  const equities = data.map((d) => d.equity);
  const benchmarks = data.map((d) => d.benchmark_equity);
  const allValues = [...equities, ...benchmarks];

  const minVal = Math.min(...allValues) * 0.95;
  const maxVal = Math.max(...allValues) * 1.05;

  const getY = (val: number) => {
    if (maxVal === minVal) return height / 2;
    return height - ((val - minVal) / (maxVal - minVal)) * height;
  };

  const equityPath = data.reduce((acc, pt, idx) => {
    const x = (idx / (data.length - 1 || 1)) * totalWidth;
    const y = getY(pt.equity);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaPath = `${equityPath} L ${totalWidth} ${height} L 0 ${height} Z`;

  const benchPath = data.reduce((acc, pt, idx) => {
    const x = (idx / (data.length - 1 || 1)) * totalWidth;
    const y = getY(pt.benchmark_equity);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const activePt = hoverIdx !== null ? data[hoverIdx] : data[data.length - 1];

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80 mb-3">
        <div>
          <div className="text-sm font-bold text-slate-200">{title}</div>
          {activePt && (
            <div className="flex items-center gap-4 text-xs font-mono mt-1 text-slate-400">
              <span>Date: <strong className="text-slate-200">{formatDate(activePt.date)}</strong></span>
              <span>Strategy: <strong className="text-emerald-400">{formatCurrency(activePt.equity)}</strong></span>
              <span>Benchmark: <strong className="text-cyan-400">{formatCurrency(activePt.benchmark_equity)}</strong></span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2.5 h-0.5 bg-emerald-400" /> Strategy
          </div>
          <div className="flex items-center gap-1.5 text-cyan-400">
            <span className="w-2.5 h-0.5 bg-cyan-400" /> Benchmark
          </div>
        </div>
      </div>

      <div className="relative w-full">
        <svg
          viewBox={`0 0 ${totalWidth} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseLeave={() => setHoverIdx(null)}
        >
          <defs>
            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00f5a0" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#00f5a0" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((p, idx) => {
            const y = p * height;
            const val = maxVal - p * (maxVal - minVal);
            return (
              <g key={idx}>
                <line x1="0" y1={y} x2={totalWidth} y2={y} stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                <text x={totalWidth - 5} y={y - 4} textAnchor="end" fill="#64748b" fontSize="10" fontFamily="JetBrains Mono">
                  {formatCurrency(val, 0)}
                </text>
              </g>
            );
          })}

          {/* Strategy Area & Line */}
          <path d={areaPath} fill="url(#equityGrad)" />
          <path d={equityPath} fill="none" stroke="#00f5a0" strokeWidth="2.5" />

          {/* Benchmark Line */}
          <path d={benchPath} fill="none" stroke="#00d8ff" strokeWidth="1.5" strokeDasharray="4 4" />

          {/* Hover trigger points */}
          {data.map((_, idx) => {
            const x = (idx / (data.length - 1 || 1)) * totalWidth;
            return (
              <rect
                key={idx}
                x={x - 4}
                y="0"
                width="8"
                height={height}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoverIdx(idx)}
              />
            );
          })}

          {hoverIdx !== null && (
            <g>
              {(() => {
                const hx = (hoverIdx / (data.length - 1 || 1)) * totalWidth;
                const hy = getY(data[hoverIdx].equity);
                return (
                  <>
                    <line x1={hx} y1="0" x2={hx} y2={height} stroke="#00f5a0" strokeWidth="1" strokeDasharray="2 2" />
                    <circle cx={hx} cy={hy} r="4" fill="#00f5a0" stroke="#080c14" strokeWidth="2" />
                  </>
                );
              })()}
            </g>
          )}
        </svg>
      </div>
    </div>
  );
};
