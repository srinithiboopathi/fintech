import React, { useState } from 'react';
import { Trade } from '../../types';
import { formatCurrency, formatPercent, formatDate } from '../../utils/formatters';
import { exportToCSV } from '../../utils/export';
import { Button } from '../ui/Button';
import { Download, ArrowUpRight, ArrowDownRight, Filter } from 'lucide-react';

interface TradeTableProps {
  trades: Trade[];
}

export const TradeTable: React.FC<TradeTableProps> = ({ trades }) => {
  const [filterSide, setFilterSide] = useState<'ALL' | 'WIN' | 'LOSS'>('ALL');

  const filteredTrades = trades.filter((t) => {
    if (filterSide === 'WIN') return t.pnl_usd > 0;
    if (filterSide === 'LOSS') return t.pnl_usd <= 0;
    return true;
  });

  const handleExport = () => {
    exportToCSV(trades, `quantlab_trades_${new Date().toISOString().split('T')[0]}`);
  };

  if (!trades || trades.length === 0) {
    return (
      <div className="glass-card rounded-2xl p-8 text-center text-slate-500 font-mono">
        No completed trade orders generated in this simulation run.
      </div>
    );
  }

  return (
    <div className="w-full glass-card rounded-2xl border border-slate-800 overflow-hidden">
      {/* Table Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-slate-800/80">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold text-slate-200">Execution Audit Log</h3>
          <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/20 px-2 py-0.5 rounded">
            {trades.length} Orders
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Filter Pills */}
          <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setFilterSide('ALL')}
              className={`px-2 py-0.5 rounded ${
                filterSide === 'ALL' ? 'bg-slate-700 text-white font-bold' : 'text-slate-400'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterSide('WIN')}
              className={`px-2 py-0.5 rounded ${
                filterSide === 'WIN' ? 'bg-emerald-500/20 text-emerald-400 font-bold' : 'text-slate-400'
              }`}
            >
              Winners
            </button>
            <button
              onClick={() => setFilterSide('LOSS')}
              className={`px-2 py-0.5 rounded ${
                filterSide === 'LOSS' ? 'bg-rose-500/20 text-rose-400 font-bold' : 'text-slate-400'
              }`}
            >
              Losses
            </button>
          </div>

          <Button
            size="sm"
            variant="outline"
            onClick={handleExport}
            leftIcon={<Download className="w-3.5 h-3.5" />}
          >
            Export CSV
          </Button>
        </div>
      </div>

      {/* Table Data */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="p-3">Trade ID</th>
              <th className="p-3">Symbol</th>
              <th className="p-3">Side</th>
              <th className="p-3">Entry Date</th>
              <th className="p-3">Entry Price</th>
              <th className="p-3">Exit Date</th>
              <th className="p-3">Exit Price</th>
              <th className="p-3">Net PnL ($)</th>
              <th className="p-3">Return (%)</th>
              <th className="p-3">Friction</th>
              <th className="p-3">Exit Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredTrades.map((t) => {
              const isWin = t.pnl_usd > 0;
              return (
                <tr key={t.trade_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-3 font-bold text-slate-300">{t.trade_id}</td>
                  <td className="p-3 text-cyan-400 font-bold">{t.symbol}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">
                      {t.side}
                    </span>
                  </td>
                  <td className="p-3 text-slate-300">{formatDate(t.entry_date)}</td>
                  <td className="p-3 text-slate-200">{formatCurrency(t.entry_price)}</td>
                  <td className="p-3 text-slate-300">{formatDate(t.exit_date)}</td>
                  <td className="p-3 text-slate-200">{formatCurrency(t.exit_price)}</td>
                  <td className={`p-3 font-bold ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {formatCurrency(t.pnl_usd)}
                  </td>
                  <td className={`p-3 font-bold flex items-center gap-1 ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {isWin ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                    {formatPercent(t.pnl_pct)}
                  </td>
                  <td className="p-3 text-slate-400 text-[11px]">
                    ${t.commission.toFixed(1)} fee
                  </td>
                  <td className="p-3">
                    <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {t.exit_reason}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
