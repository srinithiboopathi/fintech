import React, { useState, useMemo } from 'react';
import { OHLCVBar } from '../../types';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface PriceChartProps {
  bars: OHLCVBar[];
  title?: string;
  height?: number;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  bars,
  title = 'Price Action & Volume Matrix',
  height = 340,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [chartType, setChartType] = useState<'candle' | 'line'>('candle');

  // Compute scale boundaries
  const { minPrice, maxPrice, maxVolume, points } = useMemo(() => {
    if (!bars || bars.length === 0) {
      return { minPrice: 0, maxPrice: 100, maxVolume: 100, points: [] };
    }
    const recentBars = bars.slice(-60); // show last 60 trading bars
    const lows = recentBars.map((b) => b.low);
    const highs = recentBars.map((b) => b.high);
    const volumes = recentBars.map((b) => b.volume);

    const minP = Math.min(...lows) * 0.98;
    const maxP = Math.max(...highs) * 1.02;
    const maxV = Math.max(...volumes, 1);

    return {
      minPrice: minP,
      maxPrice: maxP,
      maxVolume: maxV,
      points: recentBars,
    };
  }, [bars]);

  const activeBar = hoverIndex !== null && points[hoverIndex] ? points[hoverIndex] : points[points.length - 1];

  // Dimensions
  const chartHeight = height - 80;
  const volumeHeight = 60;
  const totalWidth = 800; // viewBox width

  const getY = (price: number) => {
    if (maxPrice === minPrice) return chartHeight / 2;
    return chartHeight - ((price - minPrice) / (maxPrice - minPrice)) * chartHeight;
  };

  const getVolY = (vol: number) => {
    return volumeHeight - (vol / maxVolume) * volumeHeight;
  };

  // Build SVG path for line chart mode
  const linePath = points.length > 0
    ? points.reduce((acc, bar, idx) => {
        const x = (idx / (points.length - 1 || 1)) * totalWidth;
        const y = getY(bar.close);
        return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
      }, '')
    : '';

  const areaPath = linePath ? `${linePath} L ${totalWidth} ${chartHeight} L 0 ${chartHeight} Z` : '';

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      {/* Chart Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800/80 mb-4">
        <div>
          <div className="text-sm font-bold text-slate-200">{title}</div>
          {activeBar && (
            <div className="flex items-center gap-3 text-xs font-mono mt-1 text-slate-400">
              <span>Date: <strong className="text-slate-200">{formatDate(activeBar.date)}</strong></span>
              <span>O: <strong className="text-slate-200">{formatCurrency(activeBar.open)}</strong></span>
              <span>H: <strong className="text-emerald-400">{formatCurrency(activeBar.high)}</strong></span>
              <span>L: <strong className="text-rose-400">{formatCurrency(activeBar.low)}</strong></span>
              <span>C: <strong className="text-cyan-400">{formatCurrency(activeBar.close)}</strong></span>
            </div>
          )}
        </div>

        {/* Toggle Candle vs Line */}
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setChartType('candle')}
            className={`px-2.5 py-1 rounded ${
              chartType === 'candle' ? 'bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30' : 'text-slate-400'
            }`}
          >
            Candlestick
          </button>
          <button
            onClick={() => setChartType('line')}
            className={`px-2.5 py-1 rounded ${
              chartType === 'line' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30' : 'text-slate-400'
            }`}
          >
            Line (Close)
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full">
        <svg
          viewBox={`0 0 ${totalWidth} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#00d8ff" stop-opacity="0.3" />
              <stop offset="100%" stop-color="#00d8ff" stop-opacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((p, idx) => {
            const y = p * chartHeight;
            const priceLevel = maxPrice - p * (maxPrice - minPrice);
            return (
              <g key={idx}>
                <line x1="0" y1={y} x2={totalWidth} y2={y} stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                <text x={totalWidth - 5} y={y - 4} textAnchor="end" fill="#64748b" fontSize="10" fontFamily="JetBrains Mono">
                  {formatCurrency(priceLevel, 1)}
                </text>
              </g>
            );
          })}

          {/* Volume Section Separator */}
          <line x1="0" y1={chartHeight + 15} x2={totalWidth} y2={chartHeight + 15} stroke="rgba(255,255,255,0.1)" />

          {/* Render Area & Line Mode */}
          {chartType === 'line' && (
            <>
              <path d={areaPath} fill="url(#areaGradient)" />
              <path d={linePath} fill="none" stroke="#00d8ff" strokeWidth="2.5" />
            </>
          )}

          {/* Render Candlesticks & Volume Bars */}
          {points.map((bar, idx) => {
            const barWidth = Math.max(3, (totalWidth / points.length) * 0.7);
            const x = (idx / (points.length - 1 || 1)) * (totalWidth - barWidth) + barWidth / 2;
            const isUp = bar.close >= bar.open;
            const candleColor = isUp ? '#00f5a0' : '#ff3366';

            const yOpen = getY(bar.open);
            const yClose = getY(bar.close);
            const yHigh = getY(bar.high);
            const yLow = getY(bar.low);

            const rectY = Math.min(yOpen, yClose);
            const rectHeight = Math.max(2, Math.abs(yClose - yOpen));

            // Volume
            const volY = chartHeight + 20 + getVolY(bar.volume);
            const volH = height - volY;

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoverIndex(idx)}
                className="cursor-crosshair transition-opacity duration-100 hover:opacity-80"
              >
                {/* Candlestick Wick & Body */}
                {chartType === 'candle' && (
                  <>
                    <line x1={x} y1={yHigh} x2={x} y2={yLow} stroke={candleColor} strokeWidth="1.2" />
                    <rect
                      x={x - barWidth / 2}
                      y={rectY}
                      width={barWidth}
                      height={rectHeight}
                      fill={candleColor}
                      rx="1"
                    />
                  </>
                )}

                {/* Volume Bar */}
                <rect
                  x={x - barWidth / 2}
                  y={volY}
                  width={barWidth}
                  height={Math.max(2, volH)}
                  fill={isUp ? 'rgba(0, 245, 160, 0.3)' : 'rgba(255, 51, 102, 0.3)'}
                />
              </g>
            );
          })}

          {/* Hover Crosshair */}
          {hoverIndex !== null && points[hoverIndex] && (
            <g>
              {(() => {
                const barWidth = Math.max(3, (totalWidth / points.length) * 0.7);
                const hx = (hoverIndex / (points.length - 1 || 1)) * (totalWidth - barWidth) + barWidth / 2;
                const hy = getY(points[hoverIndex].close);
                return (
                  <>
                    <line x1={hx} y1="0" x2={hx} y2={height} stroke="#00d8ff" strokeWidth="1" strokeDasharray="2 2" />
                    <line x1="0" y1={hy} x2={totalWidth} y2={hy} stroke="#00d8ff" strokeWidth="1" strokeDasharray="2 2" />
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
