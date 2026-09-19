import React, { useEffect, useState } from 'react';
import { Cpu, Activity, RotateCcw, Filter } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { StrategySignalChart } from '../components/charts/StrategySignalChart';
import { DataTable, Column } from '../components/ui/DataTable';
import { strategyApi } from '../api';
import { StrategyResponse, StrategySignalPoint } from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const StrategyBuilderPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [strategy, setStrategy] = useState<string>('sma_crossover');
  const [fastPeriod, setFastPeriod] = useState<number>(20);
  const [slowPeriod, setSlowPeriod] = useState<number>(50);
  const [shortPeriod, setShortPeriod] = useState<number>(20);
  const [longPeriod, setLongPeriod] = useState<number>(50);
  const [lookback, setLookback] = useState<number>(20);
  const [mrWindow, setMrWindow] = useState<number>(20);
  const [mrThreshold, setMrThreshold] = useState<number>(0.02);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [signalFilter, setSignalFilter] = useState<'ALL' | 'BUY' | 'SELL' | 'HOLD'>('ALL');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [strategyData, setStrategyData] = useState<StrategyResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      if (strategy === 'sma_crossover') {
        params.fast_period = fastPeriod;
        params.slow_period = slowPeriod;
      } else if (strategy === 'ema_trend') {
        params.short_period = shortPeriod;
        params.long_period = longPeriod;
      } else if (strategy === 'momentum') {
        params.lookback = lookback;
      } else if (strategy === 'mean_reversion') {
        params.window = mrWindow;
        params.threshold = mrThreshold;
      }

      const res = await strategyApi.getStrategySignals(canonicalAsset, strategy, params);
      setStrategyData(res);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [selectedAsset, strategy]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    fetchSignals();
  };

  const handleReset = () => {
    setFastPeriod(20);
    setSlowPeriod(50);
    setShortPeriod(20);
    setLongPeriod(50);
    setLookback(20);
    setMrWindow(20);
    setMrThreshold(0.02);
    setStartDate('');
    setEndDate('');
  };

  const filteredSignals = React.useMemo(() => {
    if (!strategyData) return [];
    if (signalFilter === 'BUY') return strategyData.data.filter((d) => d.signal === 1);
    if (signalFilter === 'SELL') return strategyData.data.filter((d) => d.signal === -1);
    if (signalFilter === 'HOLD') return strategyData.data.filter((d) => d.signal === 0);
    return strategyData.data;
  }, [strategyData, signalFilter]);

  const signalColumns: Column<StrategySignalPoint>[] = [
    {
      header: 'Date',
      accessor: 'date',
      className: 'font-mono text-slate-300',
      sortable: true,
      sortKey: 'date',
    },
    {
      header: 'Close Price',
      accessor: (row) => `$${row.close.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      sortable: true,
      sortKey: 'close',
    },
    {
      header: 'Signal Action',
      accessor: (row) => {
        if (row.signal === 1) {
          return <Badge variant="emerald" size="xs">BUY</Badge>;
        }
        if (row.signal === -1) {
          return <Badge variant="rose" size="xs">SELL</Badge>;
        }
        return <Badge variant="muted" size="xs">HOLD</Badge>;
      },
    },
    {
      header: 'Active Position',
      accessor: (row) => (
        <span className={row.position === 1 ? 'text-emerald-400 font-bold' : 'text-slate-500'}>
          {row.position === 1 ? 'LONG (1.0)' : 'FLAT (0.0)'}
        </span>
      ),
    },
    {
      header: 'Indicator Values',
      accessor: (row) => {
        const ind = row.indicators || {};
        return (
          <div className="flex gap-2 text-[10px] text-slate-400">
            {Object.entries(ind).map(([k, v]) => (
              <span key={k}>
                {k}: <span className="text-slate-200">{v !== null ? v.toFixed(2) : '—'}</span>
              </span>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      {/* Configuration Controls Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <CardTitle>Strategy Rule Engine & Hyperparameters</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Defaults</span>
          </Button>
        </CardHeader>
        <CardContent className="p-4">
          <form onSubmit={handleApply} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
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
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Strategy Model</label>
              <Select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                <option value="sma_crossover">SMA Crossover</option>
                <option value="ema_trend">EMA Trend</option>
                <option value="momentum">Momentum</option>
                <option value="mean_reversion">Mean Reversion</option>
              </Select>
            </div>

            {/* Dynamic Strategy-Specific Parameters */}
            {strategy === 'sma_crossover' && (
              <>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Fast Period</label>
                  <Input
                    type="number"
                    min={2}
                    max={200}
                    value={fastPeriod}
                    onChange={(e) => setFastPeriod(parseInt(e.target.value) || 20)}
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Slow Period</label>
                  <Input
                    type="number"
                    min={3}
                    max={500}
                    value={slowPeriod}
                    onChange={(e) => setSlowPeriod(parseInt(e.target.value) || 50)}
                  />
                </div>
              </>
            )}

            {strategy === 'ema_trend' && (
              <>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Short Span</label>
                  <Input
                    type="number"
                    min={2}
                    max={200}
                    value={shortPeriod}
                    onChange={(e) => setShortPeriod(parseInt(e.target.value) || 20)}
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Long Span</label>
                  <Input
                    type="number"
                    min={3}
                    max={500}
                    value={longPeriod}
                    onChange={(e) => setLongPeriod(parseInt(e.target.value) || 50)}
                  />
                </div>
              </>
            )}

            {strategy === 'momentum' && (
              <div>
                <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Lookback (Days)</label>
                <Input
                  type="number"
                  min={1}
                  max={252}
                  value={lookback}
                  onChange={(e) => setLookback(parseInt(e.target.value) || 20)}
                />
              </div>
            )}

            {strategy === 'mean_reversion' && (
              <>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Baseline Window</label>
                  <Input
                    type="number"
                    min={2}
                    max={200}
                    value={mrWindow}
                    onChange={(e) => setMrWindow(parseInt(e.target.value) || 20)}
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Deviation Trigger</label>
                  <Input
                    type="number"
                    step={0.005}
                    min={0.001}
                    max={0.2}
                    value={mrThreshold}
                    onChange={(e) => setMrThreshold(parseFloat(e.target.value) || 0.02)}
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Start Date</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                placeholder="YYYY-MM-DD"
              />
            </div>

            <div className="flex items-end">
              <Button variant="primary" size="md" type="submit" className="w-full">
                Generate Signals
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading && <LoadingState message={`Simulating ${strategy} deterministic state machine...`} />}

      {error && <ErrorState message={error} onRetry={fetchSignals} />}

      {!loading && !error && strategyData && (
        <>
          {/* Signal Breakdown Scorecard */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="BUY Signals Generated"
              value={strategyData.signal_counts.buy}
              subtitle="Long entry triggers"
              icon={<Badge variant="emerald" size="xs">BUY</Badge>}
            />
            <MetricCard
              title="SELL Signals Generated"
              value={strategyData.signal_counts.sell}
              subtitle="Exit triggers"
              icon={<Badge variant="rose" size="xs">SELL</Badge>}
            />
            <MetricCard
              title="HOLD Days"
              value={strategyData.signal_counts.hold.toLocaleString()}
              subtitle="No state transition"
              icon={<Badge variant="muted" size="xs">HOLD</Badge>}
            />
            <MetricCard
              title="Total Evaluated Sessions"
              value={strategyData.count.toLocaleString()}
              subtitle={`${canonicalAsset} • ${strategy}`}
              icon={<Activity className="w-4 h-4 text-cyan-400" />}
            />
          </div>

          {/* Interactive Strategy Signal Chart */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Historical Price & Deterministic Trading Signals</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Point-in-time BUY and SELL signals generated by the {strategyData.strategy} strategy engine
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <StrategySignalChart
                data={strategyData.data}
                assetName={canonicalAsset}
                strategyName={strategyData.strategy}
                height={420}
              />
            </CardContent>
          </Card>

          {/* Filterable Signal Events Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Signal Event Log</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Chronological record of indicator calculations and triggered signal states
                </p>
              </div>

              {/* Filter by signal */}
              <div className="flex items-center space-x-1.5 bg-[#121824] p-1 rounded border border-[#1E293B]">
                <Filter className="w-3 h-3 text-slate-400 ml-1" />
                {(['ALL', 'BUY', 'SELL', 'HOLD'] as const).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setSignalFilter(mode)}
                    className={`px-2 py-0.5 text-xs font-mono rounded transition-colors ${
                      signalFilter === mode
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
                data={filteredSignals}
                columns={signalColumns}
                pageSize={15}
                emptyMessage={`No ${signalFilter} signal events found in this historical sample.`}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
