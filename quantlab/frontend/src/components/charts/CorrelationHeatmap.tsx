import React, { useState } from 'react';
import { CorrelationMatrixData } from '../../types';
import { getCorrelationColor } from '../../utils/colors';

interface CorrelationHeatmapProps {
  data: CorrelationMatrixData | null;
  onCellClick?: (assetA: string, assetB: string) => void;
}

export const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({ data, onCellClick }) => {
  const [hoverCell, setHoverCell] = useState<{ row: number; col: number } | null>(null);

  if (!data || !data.symbols || data.symbols.length === 0) {
    return <div className="p-8 text-center text-slate-500 font-mono">Loading correlation matrix...</div>;
  }

  const { symbols, raw_symbols, matrix } = data;

  return (
    <div className="w-full glass-card rounded-2xl p-5 border border-slate-800">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-200">Cross-Asset Pearson Correlation Matrix</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time pairwise statistical correlation across Gold, Bitcoin, and NVIDIA
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono">
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500/80 inline-block" /> +1.0
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <span className="w-2.5 h-2.5 rounded-sm bg-slate-700 inline-block" /> 0.0
          </span>
          <span className="flex items-center gap-1 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-sm bg-rose-500/80 inline-block" /> -1.0
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-center border-collapse">
          <thead>
            <tr>
              <th className="p-3 text-xs font-mono text-slate-400 font-medium text-left"></th>
              {symbols.map((sym, idx) => (
                <th key={idx} className="p-3 text-xs font-mono font-bold text-slate-200 whitespace-nowrap">
                  {sym}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {symbols.map((rowSym, rIdx) => (
              <tr key={rIdx}>
                <td className="p-3 text-xs font-mono font-bold text-slate-200 text-left whitespace-nowrap border-r border-slate-800/80">
                  {rowSym}
                </td>
                {symbols.map((colSym, cIdx) => {
                  const val = matrix[rIdx]?.[cIdx] ?? (rIdx === cIdx ? 1.0 : 0.0);
                  const isHovered = hoverCell?.row === rIdx && hoverCell?.col === cIdx;
                  return (
                    <td
                      key={cIdx}
                      onMouseEnter={() => setHoverCell({ row: rIdx, col: cIdx })}
                      onMouseLeave={() => setHoverCell(null)}
                      onClick={() => onCellClick && onCellClick(raw_symbols[rIdx], raw_symbols[cIdx])}
                      className="p-3 transition-all duration-150 cursor-pointer"
                    >
                      <div
                        className={`py-3 px-2 rounded-xl font-mono text-sm font-bold transition-transform ${
                          isHovered ? 'scale-105 shadow-lg ring-1 ring-cyan-400' : ''
                        }`}
                        style={{ backgroundColor: getCorrelationColor(val) }}
                      >
                        <span className="text-white drop-shadow-sm">{val.toFixed(2)}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
