import React from 'react';
import { AssetOverview } from '../../types';

interface AssetSelectorProps {
  assets: AssetOverview[];
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}

export const AssetSelector: React.FC<AssetSelectorProps> = ({
  assets,
  selectedSymbol,
  onSelect,
}) => {
  return (
    <div className="flex items-center gap-2 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
      {assets.map((asset) => {
        const isSelected = asset.symbol === selectedSymbol;
        return (
          <button
            key={asset.symbol}
            onClick={() => onSelect(asset.symbol)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all duration-150 flex items-center gap-1.5 ${
              isSelected
                ? 'bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
            }`}
          >
            <span>{asset.symbol}</span>
            <span className="text-[10px] opacity-70 hidden sm:inline">({asset.category})</span>
          </button>
        );
      })}
    </div>
  );
};
