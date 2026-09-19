import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, PlayCircle, Filter, DollarSign, Percent, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { DataTable, Column } from '../components/ui/DataTable';
import { EmptyState } from '../components/ui/EmptyState';
import { TradeRecord } from '../types';
import { useAppStore } from '../store/useAppStore';

export const TradeHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { lastBacktestResult } = useAppStore();
  const [tradeFilter, setTradeFilter] = useState<'ALL' | 'WINS' | 'LOSSES'>('ALL');

  if (!lastBacktestResult || lastBacktestResult.trades.length === 0) {
    return (
      <EmptyState
        title="No Session Trade History Available"
        description="Trade executions are generated dynamically when running portfolio backtests. Launch the backtesting engine to simulate strategy execution and generate real trade logs."
        actionText="Launch Backtest Simulator"
        actionPath="/backtesting"
        icon={<History className="w-6 h-6 text-cyan-400" />}
      />
    );
  }

  const { performance, backtest, strategy, trades, open_position } = lastBacktestResult;

  const filteredTrades = trades.filter((t) => {
    if (tradeFilter === 'WINS') return t.net_pnl >= 0;
    if (tradeFilter === 'LOSSES') return t.net_pnl < 0;
    return true;
  });

  const tradeColumns: Column<TradeRecord>[] = [
    {
      header: 'Trade ID',
      accessor: (row) => `#${row.trade_id}`,
      className: 'font-mono text-slate-400 w-16',
      sortable: true,
      sortKey: 'trade_id',
    },
    {
      header: 'Entry Date',
      accessor: 'entry_date',
      sortable: true,
      sortKey: 'entry_date',
    },
    {
      header: 'Exit Date',
      accessor: 'exit_date',
      sortable: true,
      sortKey: 'exit_date',
    },
    {
      header: 'Entry Price',
      accessor: (row) => `$${row.entry_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
    },
    {
      header: 'Exit Price',
      accessor: (row) => `$${row.exit_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
    },
    {
      header: 'Quantity',
      accessor: (row) => row.quantity.toFixed(4),
    },
    {
      header: 'Entry Notional',
      accessor: (row) => `$${row.entry_notional.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
    },
    {
      header: 'Exit Notional',
      accessor: (row) => `$${row.exit_notional.toLocaleString('en-US', { maximumFractionDigits: 2 })}`,
    },
    {
      header: 'Total Fees',
      accessor: (row) => `$${(row.entry_cost + row.exit_cost).toFixed(2)}`,
    },
    {
      header: 'Net P&L',
      accessor: (row) => {
        const isWin = row.net_pnl >= 0;
        return (
          <span className={isWin ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
            {isWin ? '+' : ''}${row.net_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        );
      },
      sortable: true,
      sortKey: 'net_pnl',
    },
    {
      header: 'Return %',
      accessor: (row) => {
        const isWin = row.return_pct >= 0;
        return (
          <span className={isWin ? 'text-emerald-400' : 'text-rose-400'}>
            {isWin ? '+' : ''}${(row.return_pct * 100).toFixed(2)}%
          </span>
        );
      },
      sortable: true,
      sortKey: 'return_pct',
    },
    {
      header: 'Holding Period',
      accessor: (row) => `${row.holding_period_days} days`,
      sortable: true,
      sortKey: 'holding_period_days',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Session Metadata Banner */}
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono font-bold">
            <History className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white tracking-wide">
                Session Trade Execution Ledger
              </h1>
              <Badge variant="cyan" size="xs">{backtest.asset}</Badge>
              <Badge variant="default" size="xs">{strategy.display_name}</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Backtest timeline: {backtest.start_date} to {backtest.end_date} • {backtest.trading_days} sessions
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate('/backtesting')}
          className="font-mono text-xs"
        >
          <PlayCircle className="w-3.5 h-3.5 mr-1 text-emerald-400" />
          <span>New Backtest</span>
        </Button>
      </div>

      {/* Trade Performance Summary Scorecard */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          title="Completed Trades"
          value={performance.number_of_trades}
          subtitle={`${performance.winning_trades} Win / ${performance.losing_trades} Loss`}
        />
        <MetricCard
          title="Win Rate"
          value={`${(performance.win_rate * 100).toFixed(1)}%`}
          subtitle="Profitable trade ratio"
          isPositiveGood={true}
          icon={<Percent className="w-3.5 h-3.5 text-emerald-400" />}
        />
        <MetricCard
          title="Gross Profit"
          value={`$${performance.gross_profit.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
          subtitle="Winning trade sum"
          className="text-emerald-400"
        />
        <MetricCard
          title="Gross Loss"
          value={`$${performance.gross_loss.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
          subtitle="Losing trade sum"
          isPositiveGood={false}
          className="text-rose-400"
        />
        <MetricCard
          title="Total Friction Fees"
          value={`$${performance.total_fees_paid.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
          subtitle={`Rate: ${(backtest.transaction_cost * 100).toFixed(2)}%`}
        />
        <MetricCard
          title="Cumulative Net P&L"
          value={`$${performance.net_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subtitle={`Total return: ${(performance.total_return * 100).toFixed(2)}%`}
          icon={<DollarSign className="w-3.5 h-3.5 text-cyan-400" />}
        />
      </div>

      {/* Open Position Warning if active */}
      {open_position && (
        <Card variant="subpanel" className="border-amber-700/60 bg-amber-950/20">
          <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
              <div>
                <div className="text-xs font-bold font-mono text-amber-300">
                  OPEN ACTIVE POSITION AT BACKTEST CLOSE
                </div>
                <div className="text-[11px] font-mono text-slate-300 mt-0.5">
                  Opened {open_position.entry_date} @ ${open_position.entry_price.toFixed(2)} • Position Qty: {open_position.quantity.toFixed(4)} • Current Mark: ${open_position.current_price.toFixed(2)}
                </div>
              </div>
            </div>
            <div className="font-mono text-right">
              <div className="text-xs text-slate-400">Unrealized P&L:</div>
              <div className={`text-sm font-bold ${open_position.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {open_position.unrealized_pnl >= 0 ? '+' : ''}${open_position.unrealized_pnl.toFixed(2)} ({(open_position.unrealized_return_pct * 100).toFixed(2)}%)
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filterable Trades Ledger */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Trade Execution Records ({filteredTrades.length})</CardTitle>
            <p className="text-[11px] font-mono text-slate-400 mt-0.5">
              Verified order executions, fill prices, transaction fees, and net return statistics
            </p>
          </div>

          <div className="flex items-center space-x-1.5 bg-[#121824] p-1 rounded border border-[#1E293B]">
            <Filter className="w-3 h-3 text-slate-400 ml-1" />
            {(['ALL', 'WINS', 'LOSSES'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setTradeFilter(mode)}
                className={`px-2 py-0.5 text-xs font-mono rounded transition-colors ${
                  tradeFilter === mode
                    ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent className="p-4">
          <DataTable
            data={filteredTrades}
            columns={tradeColumns}
            pageSize={15}
            emptyMessage={`No ${tradeFilter} trades found in this execution sample.`}
            keyExtractor={(r) => r.trade_id}
          />
        </CardContent>
      </Card>
    </div>
  );
};
