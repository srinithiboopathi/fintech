import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { Card } from '../ui/Card';
import { AssetOverview } from '../../types';
import { formatCurrency, formatPercent, formatCompactNumber } from '../../utils/formatters';
import { getRegimeBadgeColor } from '../../utils/colors';

interface AssetCardProps {
  asset: AssetOverview;
  isSelected?: boolean;
  onClick?: () => void;
}

export const AssetCard: React.FC<AssetCardProps> = ({ asset, isSelected, onClick }) => {
  const isPos = asset.change_24h >= 0;
  const regimeBadge = getRegimeBadgeColor(asset.regime);

  return (
    <Card
      onClick={onClick}
      variant="glass"
      className={`cursor-pointer transition-all duration-200 ${
        isSelected
          ? 'border-cyan-400 bg-slate-800/80 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-400/40'
          : 'hover:border-slate-700'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-base text-slate-100 font-mono">{asset.symbol}</span>
            <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${regimeBadge.bg} ${regimeBadge.text} ${regimeBadge.border}`}>
              {asset.regime}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">{asset.name}</p>
        </div>
        <div className="text-right">
          <div className="text-base font-bold text-slate-100 font-mono">
            {formatCurrency(asset.current_price, asset.symbol.includes('NVDA') ? 2 : 1)}
          </div>
          <div className={`flex items-center justify-end gap-1 text-xs font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isPos ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
            {formatPercent(asset.change_24h)}
          </div>
        </div>
      </div>

      {/* Sparkline Visual Simulation */}
      <div className="h-10 w-full flex items-end gap-1 py-1 px-1 bg-slate-950/40 rounded-lg border border-slate-800/50 mb-3">
        {asset.sparkline.map((val, idx) => {
          const min = Math.min(...asset.sparkline);
          const max = Math.max(...asset.sparkline);
          const heightPct = max === min ? 50 : Math.max(15, ((val - min) / (max - min)) * 100);
          return (
            <div
              key={idx}
              className={`flex-1 rounded-t-sm transition-all ${
                isPos ? 'bg-emerald-500/60 hover:bg-emerald-400' : 'bg-rose-500/60 hover:bg-rose-400'
              }`}
              style={{ height: `${heightPct}%` }}
            />
          );
        })}
      </div>

      {/* Footer Metrics */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
        <div>
          <span className="text-slate-400 block text-[10px]">30D VOL</span>
          <span className="text-slate-200 font-semibold">{formatPercent(asset.volatility_30d * 100, 1, false)}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">1Y SHARPE</span>
          <span className="text-cyan-400 font-semibold">{asset.sharpe_1y.toFixed(2)}</span>
        </div>
        <div className="text-right">
          <span className="text-slate-400 block text-[10px]">24H VOL</span>
          <span className="text-slate-200 font-semibold">{formatCompactNumber(asset.volume_24h)}</span>
        </div>
      </div>
    </Card>
  );
};
