import React, { useState } from 'react';
import {
  PlayCircle,
  TrendingUp,
  DollarSign,
  Percent,
  Layers,
  RotateCcw,
  AlertTriangle
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { EquityCurveChart } from '../components/charts/EquityCurveChart';
import { DrawdownChart } from '../components/charts/DrawdownChart';
import { DataTable, Column } from '../components/ui/DataTable';
import { backtestingApi } from '../api';
import { BacktestRequest, BacktestResponse, TradeRecord } from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const BacktestingPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset, setLastBacktestResult } = useAppStore();

  const [strategy, setStrategy] = useState<string>('sma_crossover');
  const [startDate, setStartDate] = useState<string>('2020-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [positionSize, setPositionSize] = useState<number>(1.0);
  const [transactionCost, setTransactionCost] = useState<number>(0.001);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.0);

  // Strategy specific parameters
  const [fastPeriod, setFastPeriod] = useState<number>(20);
  const [slowPeriod, setSlowPeriod] = useState<number>(50);
  const [shortPeriod, setShortPeriod] = useState<number>(20);
  const [longPeriod, setLongPeriod] = useState<number>(50);
  const [lookback, setLookback] = useState<number>(20);
  const [mrWindow, setMrWindow] = useState<number>(20);
  const [mrThreshold, setMrThreshold] = useState<number>(0.02);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const handleRunBacktest = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const stratParams: Record<string, any> = {};
      if (strategy === 'sma_crossover') {
        if (fastPeriod >= slowPeriod) {
          throw new Error('Fast period must be strictly less than Slow period.');
        }
        stratParams.fast_period = fastPeriod;
        stratParams.slow_period = slowPeriod;
      } else if (strategy === 'ema_trend') {
        if (shortPeriod >= longPeriod) {
          throw new Error('Short period must be strictly less than Long period.');
        }
        stratParams.short_period = shortPeriod;
        stratParams.long_period = longPeriod;
      } else if (strategy === 'momentum') {
        stratParams.lookback = lookback;
      } else if (strategy === 'mean_reversion') {
        stratParams.window = mrWindow;
        stratParams.threshold = mrThreshold;
      }

      const payload: BacktestRequest = {
        asset: canonicalAsset,
        strategy,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        initial_capital: initialCapital,
        position_size: positionSize,
        transaction_cost: transactionCost,
        risk_free_rate: riskFreeRate,
        strategy_parameters: stratParams,
      };

      const result = await backtestingApi.runBacktest(payload);
      setBacktestResult(result);
      setLastBacktestResult(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStartDate('2020-01-01');
    setEndDate('2024-12-31');
    setInitialCapital(100000);
    setPositionSize(1.0);
    setTransactionCost(0.001);
    setRiskFreeRate(0.0);
    setFastPeriod(20);
    setSlowPeriod(50);
  };

  const tradeColumns: Column<TradeRecord>[] = [
    {
      header: 'ID',
      accessor: (row) => `#${row.trade_id}`,
      className: 'font-mono text-slate-400 w-12',
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
      header: 'Fees Paid',
      accessor: (row) => `$${(row.entry_cost + row.exit_cost).toFixed(2)}`,
    },
    {
      header: 'Net P&L ($)',
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
      header: 'Return (%)',
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
      header: 'Holding (Days)',
      accessor: (row) => `${row.holding_period_days}d`,
      sortable: true,
      sortKey: 'holding_period_days',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Backtest Configuration Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <PlayCircle className="w-4 h-4 text-emerald-400" />
            <CardTitle>Backtest Execution Engine & Portfolio Parameters</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Form</span>
          </Button>
        </CardHeader>
        <CardContent className="p-4">
          <form onSubmit={handleRunBacktest} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Target Asset</label>
                <Select
                  value={selectedAsset}
                  onChange={(e) => setSelectedAsset(e.target.value as any)}
                >
                  <option value="gold">Gold Spot</option>
                  <option value="bitcoin">Bitcoin (2017 Dataset)</option>
                  <option value="nvidia">NVIDIA Corp</option>
                </Select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Strategy</label>
                <Select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                  <option value="sma_crossover">SMA Crossover</option>
                  <option value="ema_trend">EMA Trend</option>
                  <option value="momentum">Momentum</option>
                  <option value="mean_reversion">Mean Reversion</option>
                </Select>
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Start Date</label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="YYYY-MM-DD"
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">End Date</label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="YYYY-MM-DD"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-[#1E293B]">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Initial Capital ($)</label>
                <Input
                  type="number"
                  min={1000}
                  step={1000}
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Position Size (0.1 - 1.0)</label>
                <Input
                  type="number"
                  min={0.05}
                  max={1.0}
                  step={0.05}
                  value={positionSize}
                  onChange={(e) => setPositionSize(parseFloat(e.target.value) || 1.0)}
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Transaction Fee (e.g. 0.001 = 10 bps)</label>
                <Input
                  type="number"
                  min={0}
                  max={0.05}
                  step={0.0005}
                  value={transactionCost}
                  onChange={(e) => setTransactionCost(parseFloat(e.target.value) || 0.001)}
                />
              </div>

              {/* Dynamic Strategy Hyperparameters */}
              {strategy === 'sma_crossover' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Fast SMA</label>
                    <Input
                      type="number"
                      min={2}
                      value={fastPeriod}
                      onChange={(e) => setFastPeriod(parseInt(e.target.value) || 20)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Slow SMA</label>
                    <Input
                      type="number"
                      min={3}
                      value={slowPeriod}
                      onChange={(e) => setSlowPeriod(parseInt(e.target.value) || 50)}
                    />
                  </div>
                </div>
              )}

              {strategy === 'ema_trend' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Short EMA</label>
                    <Input
                      type="number"
                      min={2}
                      value={shortPeriod}
                      onChange={(e) => setShortPeriod(parseInt(e.target.value) || 20)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Long EMA</label>
                    <Input
                      type="number"
                      min={3}
                      value={longPeriod}
                      onChange={(e) => setLongPeriod(parseInt(e.target.value) || 50)}
                    />
                  </div>
                </div>
              )}

              {strategy === 'momentum' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Lookback (Days)</label>
                  <Input
                    type="number"
                    min={1}
                    value={lookback}
                    onChange={(e) => setLookback(parseInt(e.target.value) || 20)}
                  />
                </div>
              )}

              {strategy === 'mean_reversion' && (
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Window</label>
                    <Input
                      type="number"
                      min={2}
                      value={mrWindow}
                      onChange={(e) => setMrWindow(parseInt(e.target.value) || 20)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Threshold</label>
                    <Input
                      type="number"
                      step={0.005}
                      value={mrThreshold}
                      onChange={(e) => setMrThreshold(parseFloat(e.target.value) || 0.02)}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                size="lg"
                type="submit"
                disabled={loading}
                isLoading={loading}
                className="w-full sm:w-auto px-8"
              >
                RUN BACKTEST SIMULATION
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading && <LoadingState message={`Simulating realistic portfolio execution on ${canonicalAsset}...`} />}

      {error && <ErrorState message={error} onRetry={handleRunBacktest} />}

      {!loading && !error && backtestResult && (
        <>
          {/* Performance Scorecard */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              title="Final Portfolio"
              value={`$${backtestResult.performance.final_portfolio_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              subtitle={`Start: $${backtestResult.performance.initial_capital.toLocaleString()}`}
              icon={<DollarSign className="w-3.5 h-3.5 text-cyan-400" />}
            />
            <MetricCard
              title="Total Return"
              value={`${(backtestResult.performance.total_return * 100).toFixed(2)}%`}
              subtitle={`Net: $${backtestResult.performance.net_profit.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
              isPositiveGood={true}
              icon={<Percent className="w-3.5 h-3.5 text-emerald-400" />}
            />
            <MetricCard
              title="CAGR (Ann. Return)"
              value={`${(backtestResult.performance.annualized_return * 100).toFixed(2)}%`}
              subtitle={`Benchmark: ${(backtestResult.benchmark.annualized_return * 100).toFixed(2)}%`}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={backtestResult.performance.sharpe_ratio.toFixed(2)}
              subtitle={`Diff: ${backtestResult.comparison.sharpe_difference >= 0 ? '+' : ''}${backtestResult.comparison.sharpe_difference.toFixed(2)}`}
              icon={<TrendingUp className="w-3.5 h-3.5 text-cyan-400" />}
            />
            <MetricCard
              title="Maximum Drawdown"
              value={`${(backtestResult.performance.maximum_drawdown * 100).toFixed(2)}%`}
              subtitle={`Benchmark: ${(backtestResult.benchmark.maximum_drawdown * 100).toFixed(2)}%`}
              isPositiveGood={false}
              className="text-rose-400"
            />
            <MetricCard
              title="Win Rate (Trades)"
              value={`${(backtestResult.performance.win_rate * 100).toFixed(1)}%`}
              subtitle={`${backtestResult.performance.winning_trades}W / ${backtestResult.performance.losing_trades}L (${backtestResult.performance.number_of_trades} total)`}
            />
          </div>

          {/* Equity Curve Chart */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Strategy vs Benchmark Equity Curves</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Chronological mark-to-market portfolio value progression with executed trade markers
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <EquityCurveChart
                data={backtestResult.equity_curve}
                trades={backtestResult.trades}
                strategyName={backtestResult.strategy.display_name}
                assetName={backtestResult.backtest.asset}
                height={400}
              />
            </CardContent>
          </Card>

          {/* Drawdown Profile */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Portfolio Drawdown Time-Series</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Percentage drawdown from running high-water mark equity
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DrawdownChart
                data={backtestResult.equity_curve.map((d) => ({ date: d.date, drawdown: d.drawdown }))}
                height={260}
              />
            </CardContent>
          </Card>

          {/* Open Position Banner if exists */}
          {backtestResult.open_position && (
            <Card variant="subpanel" className="border-amber-700/60 bg-amber-950/20">
              <CardContent className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                  <div>
                    <div className="text-xs font-bold font-mono text-amber-300">
                      OPEN POSITION AT TERMINATION (NO FABRICATED EXIT)
                    </div>
                    <div className="text-[11px] font-mono text-slate-300 mt-0.5">
                      Entered on {backtestResult.open_position.entry_date} @ ${backtestResult.open_position.entry_price.toFixed(2)} • Qty: {backtestResult.open_position.quantity.toFixed(4)}
                    </div>
                  </div>
                </div>
                <div className="font-mono text-right">
                  <div className="text-xs text-slate-400">Unrealized P&L:</div>
                  <div className={`text-sm font-bold ${backtestResult.open_position.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {backtestResult.open_position.unrealized_pnl >= 0 ? '+' : ''}${backtestResult.open_position.unrealized_pnl.toFixed(2)} ({(backtestResult.open_position.unrealized_return_pct * 100).toFixed(2)}%)
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Completed Trades Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Completed Round-Trip Executions ({backtestResult.trades.length})</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Complete trade ledger with execution notionals, transaction fees, and net holding returns
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                data={backtestResult.trades}
                columns={tradeColumns}
                pageSize={10}
                emptyMessage="No round-trip trades were completed during this backtest window."
                keyExtractor={(r) => r.trade_id}
              />
            </CardContent>
          </Card>
        </>
      )}

      {!loading && !backtestResult && !error && (
        <Card variant="subpanel" className="p-8 text-center">
          <Layers className="w-10 h-10 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold font-mono text-slate-200">
            Backtest Simulator Ready
          </h3>
          <p className="text-xs font-mono text-slate-400 max-w-md mx-auto mt-1">
            Configure simulation parameters above and click "RUN BACKTEST SIMULATION" to execute the quantitative backtesting engine.
          </p>
        </Card>
      )}
    </div>
  );
};
