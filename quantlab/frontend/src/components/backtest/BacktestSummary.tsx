import React from 'react';
import { BacktestResult } from '../../types';
import { MetricCard } from '../market/MetricCard';
import { formatCurrency, formatPercent } from '../../utils/formatters';
import { TrendingUp, ShieldAlert, Award, Percent, Hash, Activity } from 'lucide-react';

interface BacktestSummaryProps {
  result: BacktestResult;
}

export const BacktestSummary: React.FC<BacktestSummaryProps> = ({ result }) => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Total Net PnL"
          value={formatPercent(result.total_return_pct)}
          subValue={formatCurrency(result.final_equity)}
          change={result.total_return_pct - result.benchmark_return_pct}
          icon={<TrendingUp className="w-4 h-4" />}
          tooltip="Cumulative net return after all transaction costs"
        />
        <MetricCard
          label="CAGR"
          value={formatPercent(result.cagr, 2, false)}
          subValue="Annualized Growth"
          icon={<Activity className="w-4 h-4" />}
        />
        <MetricCard
          label="Sharpe Ratio"
          value={result.sharpe_ratio.toFixed(2)}
          subValue={`Sortino: ${result.sortino_ratio.toFixed(2)}`}
          icon={<Award className="w-4 h-4" />}
        />
        <MetricCard
          label="Max Drawdown"
          value={formatPercent(result.max_drawdown_pct, 2, false)}
          subValue={`Calmar: ${result.calmar_ratio.toFixed(2)}`}
          icon={<ShieldAlert className="w-4 h-4" />}
        />
        <MetricCard
          label="Win Rate"
          value={formatPercent(result.win_rate_pct, 1, false)}
          subValue={`${result.winning_trades}W / ${result.losing_trades}L`}
          icon={<Percent className="w-4 h-4" />}
        />
        <MetricCard
          label="Profit Factor"
          value={result.profit_factor.toFixed(2)}
          subValue={`${result.total_trades} Total Trades`}
          icon={<Hash className="w-4 h-4" />}
        />
      </div>
    </div>
  );
};
