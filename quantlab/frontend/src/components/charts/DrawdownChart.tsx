import React from 'react';
import { EquityPoint } from '../../types';
import { formatPercent, formatDate } from '../../utils/formatters';

interface DrawdownChartProps {
  data: EquityPoint[];
  title?: string;
  height?: number;
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({
  data,
  title = 'Underwater Drawdown Risk Profile',
  height = 160,
}) => {
  const totalWidth = 800;

  if (!data || data.length === 0) return null;

  const dds = data.map((d) => d.drawdown_pct);
  const minDD = Math.min(...dds, -0.01); // e.g. -0.25 (-25%)

  const getY = (val: number) => {
    // Top is 0.0, Bottom is minDD
    if (minDD === 0) return 0;
    return (val / minDD) * height;
  };

  const linePath = data.reduce((acc, pt, idx) => {
    const x = (idx / (data.length - 1 || 1)) * totalWidth;
    const y = getY(pt.drawdown_pct);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaPath = `${linePath} L ${totalWidth} 0 L 0 0 Z`;

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
          {title}
        </div>
        <div className="text-xs font-mono text-rose-400 font-semibold">
          Max DD: {formatPercent(minDD * 100, 2, false)}
        </div>
      </div>

      <div className="relative w-full">
        <svg viewBox={`0 0 ${totalWidth} ${height}`} className="w-full h-auto overflow-visible select-none">
          <defs>
            <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff3366" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#ff3366" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Zero Line */}
          <line x1="0" y1="0" x2={totalWidth} y2="0" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />

          {/* Underwater Fill & Line */}
          <path d={areaPath} fill="url(#ddGrad)" />
          <path d={linePath} fill="none" stroke="#ff3366" strokeWidth="2" />
        </svg>
      </div>
    </div>
  );
};
