import React, { useState } from 'react';
import { RollingCorrelationPoint } from '../../types';
import { formatDate } from '../../utils/formatters';

interface RollingCorrelationProps {
  series: RollingCorrelationPoint[];
  assetA?: string;
  assetB?: string;
  window?: number;
  height?: number;
}

export const RollingCorrelation: React.FC<RollingCorrelationProps> = ({
  series,
  assetA = 'BTC-USD',
  assetB = 'GC=F',
  window = 30,
  height = 200,
}) => {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const totalWidth = 800;

  if (!series || series.length === 0) {
    return <div className="p-8 text-center text-slate-500 font-mono">No rolling correlation data.</div>;
  }

  // Correlation bounds: -1.0 to +1.0
  const getY = (corr: number) => {
    // Top is +1.0, Middle is 0.0, Bottom is -1.0
    const normalized = (1.0 - corr) / 2.0; // 0 for +1.0, 0.5 for 0, 1.0 for -1.0
    return normalized * height;
  };

  const linePath = series.reduce((acc, pt, idx) => {
    const x = (idx / (series.length - 1 || 1)) * totalWidth;
    const y = getY(pt.correlation);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const activePt = hoverIdx !== null ? series[hoverIdx] : series[series.length - 1];

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80 mb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-200">
            {window}-Day Rolling Correlation: <span className="text-cyan-400 font-mono">{assetA}</span> vs{' '}
            <span className="text-emerald-400 font-mono">{assetB}</span>
          </h3>
          {activePt && (
            <div className="text-xs font-mono text-slate-400 mt-0.5">
              <span>Date: <strong className="text-slate-200">{formatDate(activePt.date)}</strong></span> |{' '}
              <span>Correlation: <strong className="text-cyan-400">{activePt.correlation.toFixed(3)}</strong></span>
            </div>
          )}
        </div>
        <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
          Decoupling Indicator
        </span>
      </div>

      <div className="relative w-full">
        <svg
          viewBox={`0 0 ${totalWidth} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseLeave={() => setHoverIdx(null)}
        >
          {/* Upper bound +1.0 */}
          <line x1="0" y1={getY(1.0)} x2={totalWidth} y2={getY(1.0)} stroke="rgba(0, 245, 160, 0.2)" strokeDasharray="3 3" />
          <text x={totalWidth - 5} y={getY(1.0) + 10} textAnchor="end" fill="#00f5a0" fontSize="9" fontFamily="JetBrains Mono">
            +1.0 Perfect Sync
          </text>

          {/* Zero baseline */}
          <line x1="0" y1={getY(0.0)} x2={totalWidth} y2={getY(0.0)} stroke="rgba(255, 255, 255, 0.2)" />
          <text x={totalWidth - 5} y={getY(0.0) - 3} textAnchor="end" fill="#94a3b8" fontSize="9" fontFamily="JetBrains Mono">
            0.0 Uncorrelated
          </text>

          {/* Lower bound -1.0 */}
          <line x1="0" y1={getY(-1.0)} x2={totalWidth} y2={getY(-1.0)} stroke="rgba(255, 51, 102, 0.2)" strokeDasharray="3 3" />
          <text x={totalWidth - 5} y={getY(-1.0) - 4} textAnchor="end" fill="#ff3366" fontSize="9" fontFamily="JetBrains Mono">
            -1.0 Inverse
          </text>

          {/* Rolling Correlation Path */}
          <path d={linePath} fill="none" stroke="#00d8ff" strokeWidth="2.5" />

          {/* Hover interaction rects */}
          {series.map((_, idx) => {
            const x = (idx / (series.length - 1 || 1)) * totalWidth;
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
                const hx = (hoverIdx / (series.length - 1 || 1)) * totalWidth;
                const hy = getY(series[hoverIdx].correlation);
                return (
                  <>
                    <line x1={hx} y1="0" x2={hx} y2={height} stroke="#00d8ff" strokeWidth="1" strokeDasharray="2 2" />
                    <circle cx={hx} cy={hy} r="4" fill="#00d8ff" stroke="#080c14" strokeWidth="2" />
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
