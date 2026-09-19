import React, { useState } from 'react';
import { IndicatorData } from '../../types';

interface IndicatorChartProps {
  indicators?: IndicatorData | null;
  activeIndicator?: 'rsi' | 'macd' | 'bbands';
  height?: number;
}

export const IndicatorChart: React.FC<IndicatorChartProps> = ({
  indicators,
  activeIndicator = 'rsi',
  height = 180,
}) => {
  const [selectedInd, setSelectedInd] = useState<'rsi' | 'macd' | 'bbands'>(activeIndicator);
  const totalWidth = 800;

  // Mock series if data is empty
  const dates = indicators?.dates?.length ? indicators.dates.slice(-60) : Array.from({ length: 60 }, (_, i) => `Day ${i + 1}`);
  const rsiValues = indicators?.rsi?.length
    ? indicators.rsi.slice(-60)
    : Array.from({ length: 60 }, (_, i) => 40 + Math.sin(i / 4) * 25 + Math.random() * 8);

  const macdValues = indicators?.macd?.length
    ? indicators.macd.slice(-60)
    : Array.from({ length: 60 }, (_, i) => Math.sin(i / 5) * 2.5);

  const getRsiY = (val: number | null) => {
    if (val === null) return height / 2;
    return height - (val / 100) * height;
  };

  const getMacdY = (val: number | null) => {
    if (val === null) return height / 2;
    // Map -5 to +5
    const normalized = (val + 5) / 10;
    return height - Math.max(0, Math.min(1, normalized)) * height;
  };

  const rsiPath = rsiValues.reduce((acc, v, idx) => {
    const x = (idx / (rsiValues.length - 1 || 1)) * totalWidth;
    const y = getRsiY(v);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const macdPath = macdValues.reduce((acc, v, idx) => {
    const x = (idx / (macdValues.length - 1 || 1)) * totalWidth;
    const y = getMacdY(v);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
          Technical Indicator Oscillator
        </div>
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setSelectedInd('rsi')}
            className={`px-2.5 py-0.5 rounded ${
              selectedInd === 'rsi' ? 'bg-purple-500/20 text-purple-400 font-bold border border-purple-500/30' : 'text-slate-400'
            }`}
          >
            RSI (14)
          </button>
          <button
            onClick={() => setSelectedInd('macd')}
            className={`px-2.5 py-0.5 rounded ${
              selectedInd === 'macd' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30' : 'text-slate-400'
            }`}
          >
            MACD (12, 26, 9)
          </button>
        </div>
      </div>

      <div className="relative w-full">
        <svg viewBox={`0 0 ${totalWidth} ${height}`} className="w-full h-auto overflow-visible select-none">
          {/* RSI Background Thresholds */}
          {selectedInd === 'rsi' && (
            <>
              {/* Overbought 70 */}
              <line x1="0" y1={getRsiY(70)} x2={totalWidth} y2={getRsiY(70)} stroke="rgba(255, 51, 102, 0.4)" strokeDasharray="3 3" />
              <text x={totalWidth - 5} y={getRsiY(70) - 3} textAnchor="end" fill="#ff3366" fontSize="9" fontFamily="JetBrains Mono">
                Overbought (70)
              </text>

              {/* Midline 50 */}
              <line x1="0" y1={getRsiY(50)} x2={totalWidth} y2={getRsiY(50)} stroke="rgba(255, 255, 255, 0.08)" strokeDasharray="2 2" />

              {/* Oversold 30 */}
              <line x1="0" y1={getRsiY(30)} x2={totalWidth} y2={getRsiY(30)} stroke="rgba(0, 245, 160, 0.4)" strokeDasharray="3 3" />
              <text x={totalWidth - 5} y={getRsiY(30) + 12} textAnchor="end" fill="#00f5a0" fontSize="9" fontFamily="JetBrains Mono">
                Oversold (30)
              </text>

              {/* Shaded zone between 30 and 70 */}
              <rect x="0" y={getRsiY(70)} width={totalWidth} height={getRsiY(30) - getRsiY(70)} fill="rgba(157, 78, 221, 0.05)" />

              {/* RSI Curve */}
              <path d={rsiPath} fill="none" stroke="#a855f7" strokeWidth="2" />
            </>
          )}

          {/* MACD Mode */}
          {selectedInd === 'macd' && (
            <>
              <line x1="0" y1={getMacdY(0)} x2={totalWidth} y2={getMacdY(0)} stroke="rgba(255, 255, 255, 0.2)" />
              <path d={macdPath} fill="none" stroke="#00d8ff" strokeWidth="2" />
            </>
          )}
        </svg>
      </div>
    </div>
  );
};
