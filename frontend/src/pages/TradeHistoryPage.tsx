import React from 'react';
import { History, ListOrdered } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';

export const TradeHistoryPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex items-center justify-between shadow-xl quant-glass">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
            <History className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm md:text-base font-bold font-mono text-white">Execution Trade History</h1>
              <Badge variant="cyan" size="xs">Phase 9 Target</Badge>
            </div>
            <p className="text-xs text-slate-400">
              Audit simulated order executions, trade durations, entry/exit prices, fees, and realized PnL.
            </p>
          </div>
        </div>
      </div>

      <EmptyState
        title="Trade History & Performance Log"
        description="The Trade History module will be implemented in Phase 9. It provides complete transparency into all order fills, commissions paid, and individual trade returns."
        phase={9}
        icon={<ListOrdered className="w-6 h-6 text-cyan-400" />}
        details={[
          'Itemized Execution Table (Timestamp, Side, Size, Entry, Exit, PnL)',
          'Gross Profit, Gross Loss, and Average Trade Duration metrics',
          'Exportable Trade Blotter Log (CSV / JSON format)',
          'Slippage and Commission Impact Breakdown per Trade'
        ]}
      />
    </div>
  );
};
