import React, { useState } from 'react';
import {
  ShieldAlert,
  Layers,
  RotateCcw,
  Percent,
  Info
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { RobustnessHeatmap } from '../components/charts/RobustnessHeatmap';
import { DataTable, Column } from '../components/ui/DataTable';
import { robustnessApi } from '../api';
import { RobustnessRequest, RobustnessResponse, RobustnessConfigResult } from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const RobustnessLabPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [strategy, setStrategy] = useState<string>('sma_crossover');
  const [startDate, setStartDate] = useState<string>('2022-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [positionSize, setPositionSize] = useState<number>(1.0);
  const [costSteps, setCostSteps] = useState<string>('0.0, 0.001, 0.002');
  const [maxConfigs, setMaxConfigs] = useState<number>(100);

  // Strategy Grid Inputs (Comma-separated strings)
  const [smaFastGrid, setSmaFastGrid] = useState<string>('10, 20, 30');
  const [smaSlowGrid, setSmaSlowGrid] = useState<string>('40, 50, 100');
  const [emaShortGrid, setEmaShortGrid] = useState<string>('10, 20');
  const [emaLongGrid, setEmaLongGrid] = useState<string>('40, 50, 100');
  const [momLookbackGrid, setMomLookbackGrid] = useState<string>('10, 20, 30, 60');
  const [mrWindowGrid, setMrWindowGrid] = useState<string>('10, 20, 50');
  const [mrThresholdGrid, setMrThresholdGrid] = useState<string>('0.01, 0.02, 0.03');

  // Heatmap metric selector
  const [heatmapMetric, setHeatmapMetric] = useState<'total_return' | 'sharpe_ratio' | 'maximum_drawdown'>('total_return');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [robustnessResult, setRobustnessResult] = useState<RobustnessResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const parseNumberList = (str: string): number[] => {
    return str
      .split(',')
      .map((s) => parseFloat(s.trim()))
      .filter((n) => !isNaN(n));
  };

  const parseIntList = (str: string): number[] => {
    return str
      .split(',')
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n));
  };

  const handleRunSweep = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const costs = parseNumberList(costSteps);
      if (costs.length === 0) {
        throw new Error('Please supply at least one valid transaction cost rate.');
      }

      const grid: Record<string, any[]> = {};
      if (strategy === 'sma_crossover') {
        const fastList = parseIntList(smaFastGrid);
        const slowList = parseIntList(smaSlowGrid);
        if (fastList.length === 0 || slowList.length === 0) {
          throw new Error('Please specify at least one Fast SMA and Slow SMA value.');
        }
        grid.fast_period = fastList;
        grid.slow_period = slowList;
      } else if (strategy === 'ema_trend') {
        const shortList = parseIntList(emaShortGrid);
        const longList = parseIntList(emaLongGrid);
        if (shortList.length === 0 || longList.length === 0) {
          throw new Error('Please specify at least one Short EMA and Long EMA value.');
        }
        grid.short_period = shortList;
        grid.long_period = longList;
      } else if (strategy === 'momentum') {
        const lookbacks = parseIntList(momLookbackGrid);
        if (lookbacks.length === 0) {
          throw new Error('Please specify at least one momentum lookback value.');
        }
        grid.lookback = lookbacks;
      } else if (strategy === 'mean_reversion') {
        const windows = parseIntList(mrWindowGrid);
        const thresholds = parseNumberList(mrThresholdGrid);
        if (windows.length === 0 || thresholds.length === 0) {
          throw new Error('Please specify at least one window and threshold value.');
        }
        grid.window = windows;
        grid.threshold = thresholds;
      }

      const payload: RobustnessRequest = {
        asset: canonicalAsset,
        strategy,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        initial_capital: initialCapital,
        position_size: positionSize,
        transaction_costs: costs,
        strategy_parameter_grid: grid,
        max_configurations: maxConfigs,
      };

      const result = await robustnessApi.runRobustnessSweep(payload);
      setRobustnessResult(result);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStartDate('2022-01-01');
    setEndDate('2024-12-31');
    setCostSteps('0.0, 0.001, 0.002');
    setSmaFastGrid('10, 20, 30');
    setSmaSlowGrid('40, 50, 100');
    setMaxConfigs(100);
  };

  const resultColumns: Column<RobustnessConfigResult>[] = [
    {
      header: 'Parameters',
      accessor: (row) => (
        <div className="flex gap-1.5 flex-wrap font-bold text-slate-200">
          {Object.entries(row.parameters).map(([k, v]) => (
            <span key={k} className="bg-[#161F2E] px-1.5 py-0.5 rounded border border-[#232E42]">
              {k}: {v}
            </span>
          ))}
        </div>
      ),
    },
    {
      header: 'Fee Rate',
      accessor: (row) => `${(row.transaction_cost * 100).toFixed(2)}%`,
      sortable: true,
      sortKey: 'transaction_cost',
    },
    {
      header: 'Total Return',
      accessor: (row) => {
        const isWin = row.total_return >= 0;
        return (
          <span className={isWin ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
            {isWin ? '+' : ''}${(row.total_return * 100).toFixed(2)}%
          </span>
        );
      },
      sortable: true,
      sortKey: 'total_return',
    },
    {
      header: 'CAGR',
      accessor: (row) => `${(row.annualized_return * 100).toFixed(2)}%`,
      sortable: true,
      sortKey: 'annualized_return',
    },
    {
      header: 'Ann. Vol',
      accessor: (row) => `${(row.annualized_volatility * 100).toFixed(2)}%`,
      sortable: true,
      sortKey: 'annualized_volatility',
    },
    {
      header: 'Sharpe',
      accessor: (row) => (
        <span className={row.sharpe_ratio >= 1.0 ? 'text-cyan-300 font-bold' : 'text-slate-300'}>
          {row.sharpe_ratio.toFixed(2)}
        </span>
      ),
      sortable: true,
      sortKey: 'sharpe_ratio',
    },
    {
      header: 'Max DD',
      accessor: (row) => (
        <span className="text-rose-400 font-medium">
          {(row.maximum_drawdown * 100).toFixed(2)}%
        </span>
      ),
      sortable: true,
      sortKey: 'maximum_drawdown',
    },
    {
      header: 'Trades',
      accessor: 'number_of_trades',
      sortable: true,
      sortKey: 'number_of_trades',
    },
    {
      header: 'Win Rate',
      accessor: (row) => `${(row.win_rate * 100).toFixed(1)}%`,
      sortable: true,
      sortKey: 'win_rate',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Parameter Grid Form Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <CardTitle>Parameter Grid Sensitivity & Robustness Sweeps</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Form</span>
          </Button>
        </CardHeader>
        <CardContent className="p-4">
          <form onSubmit={handleRunSweep} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Target Asset</label>
                <Select
                  value={selectedAsset}
                  onChange={(e) => setSelectedAsset(e.target.value as any)}
                >
                  <option value="gold">Gold Spot</option>
                  <option value="bitcoin">Bitcoin (2017)</option>
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

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Initial Capital ($)</label>
                <Input
                  type="number"
                  min={1000}
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
                />
              </div>

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Position Size (0-1)</label>
                <Input
                  type="number"
                  min={0.1}
                  max={1.0}
                  step={0.1}
                  value={positionSize}
                  onChange={(e) => setPositionSize(parseFloat(e.target.value) || 1.0)}
                />
              </div>
            </div>

            {/* Grid Definition Inputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2 border-t border-[#1E293B]">
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Transaction Costs (List)
                </label>
                <Input
                  type="text"
                  value={costSteps}
                  onChange={(e) => setCostSteps(e.target.value)}
                  placeholder="0.0, 0.001, 0.002"
                />
              </div>

              {strategy === 'sma_crossover' && (
                <>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Fast SMA List (e.g. 10, 20, 30)
                    </label>
                    <Input
                      type="text"
                      value={smaFastGrid}
                      onChange={(e) => setSmaFastGrid(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Slow SMA List (e.g. 40, 50, 100)
                    </label>
                    <Input
                      type="text"
                      value={smaSlowGrid}
                      onChange={(e) => setSmaSlowGrid(e.target.value)}
                    />
                  </div>
                </>
              )}

              {strategy === 'ema_trend' && (
                <>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Short EMA List (e.g. 10, 20)
                    </label>
                    <Input
                      type="text"
                      value={emaShortGrid}
                      onChange={(e) => setEmaShortGrid(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Long EMA List (e.g. 40, 50, 100)
                    </label>
                    <Input
                      type="text"
                      value={emaLongGrid}
                      onChange={(e) => setEmaLongGrid(e.target.value)}
                    />
                  </div>
                </>
              )}

              {strategy === 'momentum' && (
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                    Lookback List (e.g. 10, 20, 30, 60)
                  </label>
                  <Input
                    type="text"
                    value={momLookbackGrid}
                    onChange={(e) => setMomLookbackGrid(e.target.value)}
                  />
                </div>
              )}

              {strategy === 'mean_reversion' && (
                <>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Window List (e.g. 10, 20, 50)
                    </label>
                    <Input
                      type="text"
                      value={mrWindowGrid}
                      onChange={(e) => setMrWindowGrid(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                      Threshold List (e.g. 0.01, 0.02, 0.03)
                    </label>
                    <Input
                      type="text"
                      value={mrThresholdGrid}
                      onChange={(e) => setMrThresholdGrid(e.target.value)}
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                  Safety Limit Max Configs
                </label>
                <Input
                  type="number"
                  min={1}
                  max={500}
                  value={maxConfigs}
                  onChange={(e) => setMaxConfigs(parseInt(e.target.value) || 100)}
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="gold"
                size="lg"
                type="submit"
                disabled={loading}
                isLoading={loading}
                className="w-full sm:w-auto px-8"
              >
                EXECUTE ROBUSTNESS SWEEP
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Methodology Disclaimer Callout */}
      <div className="bg-[#121824] border border-[#1E293B] rounded-lg p-3.5 flex items-start space-x-3 text-xs font-mono text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-200 uppercase">Non-Optimization Principle:</span> The Robustness Lab does not select a "best" configuration or rank parameters. It reveals sensitivity surfaces and parameter cliff risks across historical regimes.
        </div>
      </div>

      {loading && <LoadingState message="Executing multi-parameter Cartesian backtest grid..." />}

      {error && <ErrorState message={error} onRetry={handleRunSweep} />}

      {!loading && !error && robustnessResult && (
        <>
          {/* Summary Metric Ranges Scorecard */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <MetricCard
              title="Configurations"
              value={robustnessResult.summary.total_configurations}
              subtitle="Total backtests run"
              icon={<Layers className="w-4 h-4 text-cyan-400" />}
            />
            <MetricCard
              title="Return Range"
              value={`${(robustnessResult.summary.metrics_ranges.return_range.min * 100).toFixed(1)}% → ${(robustnessResult.summary.metrics_ranges.return_range.max * 100).toFixed(1)}%`}
              subtitle="Min / Max cumulative"
              icon={<Percent className="w-4 h-4 text-emerald-400" />}
            />
            <MetricCard
              title="Sharpe Range"
              value={`${robustnessResult.summary.metrics_ranges.sharpe_range.min.toFixed(2)} → ${robustnessResult.summary.metrics_ranges.sharpe_range.max.toFixed(2)}`}
              subtitle="Observed range"
            />
            <MetricCard
              title="Drawdown Range"
              value={`${(robustnessResult.summary.metrics_ranges.drawdown_range.min * 100).toFixed(1)}% → ${(robustnessResult.summary.metrics_ranges.drawdown_range.max * 100).toFixed(1)}%`}
              subtitle="Peak drop bounds"
              isPositiveGood={false}
              className="text-rose-400"
            />
            <MetricCard
              title="Trades Range"
              value={`${robustnessResult.summary.metrics_ranges.trades_range.min} → ${robustnessResult.summary.metrics_ranges.trades_range.max}`}
              subtitle="Completed trades"
            />
            <MetricCard
              title="Win Rate Range"
              value={`${(robustnessResult.summary.metrics_ranges.win_rate_range.min * 100).toFixed(0)}% → ${(robustnessResult.summary.metrics_ranges.win_rate_range.max * 100).toFixed(0)}%`}
              subtitle="Win proportion range"
            />
          </div>

          {/* 2D Sensitivity Heatmap */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Hyperparameter Sensitivity Surface</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Multi-parameter landscape heatmap (reveals parameter stability vs cliff vulnerability)
                </p>
              </div>

              <div className="flex items-center space-x-1.5 bg-[#121824] p-1 rounded border border-[#1E293B]">
                <button
                  onClick={() => setHeatmapMetric('total_return')}
                  className={`px-2 py-0.5 text-xs font-mono rounded ${
                    heatmapMetric === 'total_return'
                      ? 'bg-cyan-950 text-cyan-300 font-semibold'
                      : 'text-slate-400'
                  }`}
                >
                  Total Return
                </button>
                <button
                  onClick={() => setHeatmapMetric('sharpe_ratio')}
                  className={`px-2 py-0.5 text-xs font-mono rounded ${
                    heatmapMetric === 'sharpe_ratio'
                      ? 'bg-cyan-950 text-cyan-300 font-semibold'
                      : 'text-slate-400'
                  }`}
                >
                  Sharpe Ratio
                </button>
                <button
                  onClick={() => setHeatmapMetric('maximum_drawdown')}
                  className={`px-2 py-0.5 text-xs font-mono rounded ${
                    heatmapMetric === 'maximum_drawdown'
                      ? 'bg-cyan-950 text-cyan-300 font-semibold'
                      : 'text-slate-400'
                  }`}
                >
                  Max Drawdown
                </button>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <RobustnessHeatmap
                results={robustnessResult.results}
                metric={heatmapMetric}
                height={340}
              />
            </CardContent>
          </Card>

          {/* Unranked Configuration Outcomes Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>All Tested Grid Configurations ({robustnessResult.results.length})</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Objective quantitative performance outputs across all parameter and cost combinations
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                data={robustnessResult.results}
                columns={resultColumns}
                pageSize={15}
                keyExtractor={(_, i) => i}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
