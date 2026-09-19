import React, { useEffect, useState } from 'react';
import { Gauge, Info, RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { RegimeTimelineChart } from '../components/charts/RegimeTimelineChart';
import { DataTable, Column } from '../components/ui/DataTable';
import { regimeApi } from '../api';
import { RegimeResponse, TransitionEvent, RegimeMetrics } from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const MarketRegimesPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [trendWindow, setTrendWindow] = useState<number>(50);
  const [volatilityWindow, setVolatilityWindow] = useState<number>(20);
  const [thresholdMode, setThresholdMode] = useState<string>('historical_descriptive');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [regimeData, setRegimeData] = useState<RegimeResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const fetchRegimes = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await regimeApi.getMarketRegimes(canonicalAsset, {
        trend_window: trendWindow,
        volatility_window: volatilityWindow,
        threshold_mode: thresholdMode,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      setRegimeData(res);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegimes();
  }, [selectedAsset, thresholdMode]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRegimes();
  };

  const handleReset = () => {
    setTrendWindow(50);
    setVolatilityWindow(20);
    setThresholdMode('historical_descriptive');
    setStartDate('');
    setEndDate('');
  };

  const transitionColumns: Column<TransitionEvent>[] = [
    {
      header: 'Date',
      accessor: 'date',
      className: 'font-mono text-slate-300 font-bold',
      sortable: true,
      sortKey: 'date',
    },
    {
      header: 'Transition Type',
      accessor: (row) => (
        <span className="uppercase text-[10px] bg-[#161F2E] px-2 py-0.5 rounded border border-[#232E42] text-slate-300">
          {row.transition_type}
        </span>
      ),
    },
    {
      header: 'Prior State',
      accessor: (row) => {
        if (row.from_state === 'BULL') return <Badge variant="emerald" size="xs">BULL</Badge>;
        if (row.from_state === 'BEAR') return <Badge variant="rose" size="xs">BEAR</Badge>;
        if (row.from_state === 'HIGH_VOLATILITY') return <Badge variant="amber" size="xs">HIGH VOL</Badge>;
        return <Badge variant="cyan" size="xs">LOW VOL</Badge>;
      },
    },
    {
      header: 'New State',
      accessor: (row) => {
        if (row.to_state === 'BULL') return <Badge variant="emerald" size="xs">BULL</Badge>;
        if (row.to_state === 'BEAR') return <Badge variant="rose" size="xs">BEAR</Badge>;
        if (row.to_state === 'HIGH_VOLATILITY') return <Badge variant="amber" size="xs">HIGH VOL</Badge>;
        return <Badge variant="cyan" size="xs">LOW VOL</Badge>;
      },
    },
  ];

  interface StateStatRow {
    stateName: string;
    badgeVariant: 'emerald' | 'rose' | 'amber' | 'cyan';
    metrics: RegimeMetrics;
  }

  const statRows: StateStatRow[] = regimeData?.summary_statistics
    ? [
        { stateName: 'BULL REGIME (Trend > SMA)', badgeVariant: 'emerald', metrics: regimeData.summary_statistics.bull },
        { stateName: 'BEAR REGIME (Trend <= SMA)', badgeVariant: 'rose', metrics: regimeData.summary_statistics.bear },
        { stateName: 'HIGH VOLATILITY (Vol > Threshold)', badgeVariant: 'amber', metrics: regimeData.summary_statistics.high_volatility },
        { stateName: 'LOW VOLATILITY (Vol <= Threshold)', badgeVariant: 'cyan', metrics: regimeData.summary_statistics.low_volatility },
      ]
    : [];

  const statColumns: Column<StateStatRow>[] = [
    {
      header: 'State / Regime',
      accessor: (row) => <Badge variant={row.badgeVariant} size="sm">{row.stateName}</Badge>,
    },
    {
      header: 'Sessions',
      accessor: (row) => row.metrics.observation_count.toLocaleString(),
    },
    {
      header: 'Share %',
      accessor: (row) => `${(row.metrics.percentage * 100).toFixed(1)}%`,
    },
    {
      header: 'Avg Daily Return',
      accessor: (row) =>
        row.metrics.average_daily_return !== null
          ? `${(row.metrics.average_daily_return * 100).toFixed(3)}%`
          : '—',
    },
    {
      header: 'Cumulative Return',
      accessor: (row) => {
        const val = row.metrics.cumulative_return;
        if (val === null) return '—';
        return (
          <span className={val >= 0 ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
            {val >= 0 ? '+' : ''}${(val * 100).toFixed(2)}%
          </span>
        );
      },
    },
    {
      header: 'Ann. Volatility',
      accessor: (row) =>
        row.metrics.annualized_volatility !== null
          ? `${(row.metrics.annualized_volatility * 100).toFixed(2)}%`
          : '—',
    },
    {
      header: 'Sharpe Ratio',
      accessor: (row) =>
        row.metrics.sharpe_ratio !== null ? row.metrics.sharpe_ratio.toFixed(2) : '—',
    },
    {
      header: 'Max Drawdown',
      accessor: (row) => (
        <span className="text-rose-400 font-medium">
          {row.metrics.maximum_drawdown !== null
            ? `${(row.metrics.maximum_drawdown * 100).toFixed(2)}%`
            : '—'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Controls Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <Gauge className="w-4 h-4 text-cyan-400" />
            <CardTitle>Historical Market Regime Classification Controls</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Controls</span>
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
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Trend Window</label>
              <Input
                type="number"
                min={2}
                max={200}
                value={trendWindow}
                onChange={(e) => setTrendWindow(parseInt(e.target.value) || 50)}
              />
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Vol Window</label>
              <Input
                type="number"
                min={2}
                max={200}
                value={volatilityWindow}
                onChange={(e) => setVolatilityWindow(parseInt(e.target.value) || 20)}
              />
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Threshold Mode</label>
              <Select
                value={thresholdMode}
                onChange={(e) => setThresholdMode(e.target.value)}
              >
                <option value="historical_descriptive">Historical Descriptive (Median)</option>
                <option value="expanding_threshold">Expanding Point-in-Time</option>
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

            <div className="flex items-end">
              <Button variant="primary" size="md" type="submit" className="w-full">
                Classify Regimes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Methodology Explanation Banner */}
      <div className="bg-[#121824] border border-[#1E293B] rounded-lg p-3.5 flex items-start space-x-3 text-xs font-mono text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-slate-200">
            {thresholdMode === 'historical_descriptive' ? 'Historical Descriptive Mode:' : 'Expanding Threshold Mode:'}
          </span>{' '}
          {thresholdMode === 'historical_descriptive'
            ? 'Uses the full-sample median rolling volatility as a constant threshold. Ideal for retrospective historical review, but not strictly causal.'
            : 'Calculates the median threshold expanding dynamically up to date t. Strictly causal with zero look-ahead bias.'}
        </div>
      </div>

      {loading && <LoadingState message={`Classifying market regimes and volatility states for ${canonicalAsset}...`} />}

      {error && <ErrorState message={error} onRetry={fetchRegimes} />}

      {!loading && !error && regimeData && (
        <>
          {/* Regime Timeline Visualization */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Historical Market Regime Analysis • {canonicalAsset}</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Descriptive classification of historical price trend (BULL/BEAR) and rolling annualized volatility
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <RegimeTimelineChart
                data={regimeData.data}
                assetName={canonicalAsset}
                height={440}
              />
            </CardContent>
          </Card>

          {/* Descriptive Statistics Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Descriptive Regime & Volatility State Statistics</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Empirical performance distributions across identified trend regimes and volatility environments
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable data={statRows} columns={statColumns} pageSize={5} />
            </CardContent>
          </Card>

          {/* Chronological State Transitions Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>State Transition Timeline ({regimeData.transitions.length} Events)</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Chronological record of flips in primary trend regime and volatility states
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                data={regimeData.transitions}
                columns={transitionColumns}
                pageSize={10}
                emptyMessage="No state transitions detected in this sample."
                keyExtractor={(_, i) => i}
              />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
