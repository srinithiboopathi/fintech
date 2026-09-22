import React, { useState } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { TradeTable } from '../components/backtest/TradeTable';
import { MetricCard } from '../components/market/MetricCard';
import { useBacktest } from '../hooks/useBacktest';
import { formatCurrency, formatPercent } from '../utils/formatters';
import { Award, TrendingDown, Clock, Hash } from 'lucide-react';

export const TradeHistory: React.FC = () => {
  const { activeResult } = useBacktest();
  const trades = activeResult?.trades || [];

  const winningTrades = trades.filter((t) => t.pnl_usd > 0);
  const losingTrades = trades.filter((t) => t.pnl_usd <= 0);

  const grossGains = winningTrades.reduce((acc, t) => acc + t.pnl_usd, 0);
  const grossLosses = Math.abs(losingTrades.reduce((acc, t) => acc + t.pnl_usd, 0));

  return (
    <PageContainer
      title="Trade Execution History & Audit Log"
      subtitle="Complete chronological record of all simulated entries, exits, slippage, and fee deductions"
    >
      <div className="space-y-6">
        {/* Trade Metrics Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Total Executions"
            value={trades.length.toString()}
            subValue={`${winningTrades.length} Win / ${losingTrades.length} Loss`}
            icon={<Hash className="w-4 h-4" />}
          />
          <MetricCard
            label="Gross Wins"
            value={formatCurrency(grossGains)}
            subValue={`Avg Win: +${activeResult?.max_win_pct || 0}%`}
            icon={<Award className="w-4 h-4 text-emerald-400" />}
          />
          <MetricCard
            label="Gross Losses"
            value={formatCurrency(grossLosses)}
            subValue={`Max Loss: ${activeResult?.max_loss_pct || 0}%`}
            icon={<TrendingDown className="w-4 h-4 text-rose-400" />}
          />
          <MetricCard
            label="Avg Trade Return"
            value={formatPercent(activeResult?.avg_trade_pnl_pct || 0)}
            subValue="Per Position Cycle"
            icon={<Clock className="w-4 h-4 text-cyan-400" />}
          />
        </div>

        {/* Trade Table */}
        <TradeTable trades={trades} />
      </div>
    </PageContainer>
  );
};
