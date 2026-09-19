import React, { useEffect, useState } from 'react';
import { GitMerge, Sliders, Calendar, RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { CorrelationHeatmap } from '../components/charts/CorrelationHeatmap';
import { RollingCorrelationChart } from '../components/charts/RollingCorrelationChart';
import { DataTable, Column } from '../components/ui/DataTable';
import { correlationApi } from '../api';
import {
  CorrelationMatrixResponse,
  PairCorrelationResponse,
  RollingCorrelationResponse,
  AssetComparisonMetrics,
} from '../types';
import { extractErrorMessage } from '../lib/api';

export const CorrelationLabPage: React.FC = () => {
  const [assetA, setAssetA] = useState<string>('Gold');
  const [assetB, setAssetB] = useState<string>('NVIDIA');
  const [rollingWindow, setRollingWindow] = useState<number>(60);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [matrixData, setMatrixData] = useState<CorrelationMatrixResponse | null>(null);
  const [pairData, setPairData] = useState<PairCorrelationResponse | null>(null);
  const [rollingData, setRollingData] = useState<RollingCorrelationResponse | null>(null);
  const [comparisonList, setComparisonList] = useState<AssetComparisonMetrics[]>([]);

  const fetchCorrelationData = async () => {
    setLoading(true);
    setError(null);
    try {
      const baseParams = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const [matRes, pairRes, rollRes, compRes] = await Promise.all([
        correlationApi.getCorrelationMatrix(baseParams),
        correlationApi.getPairCorrelation({
          asset_a: assetA,
          asset_b: assetB,
          ...baseParams,
        }),
        correlationApi.getRollingCorrelation({
          asset_a: assetA,
          asset_b: assetB,
          window: rollingWindow,
          ...baseParams,
        }),
        correlationApi.getAssetComparison(baseParams),
      ]);

      setMatrixData(matRes);
      setPairData(pairRes);
      setRollingData(rollRes);
      setComparisonList(compRes.assets);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCorrelationData();
  }, [assetA, assetB, rollingWindow]);

  const handleApply = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCorrelationData();
  };

  const handleReset = () => {
    setAssetA('Gold');
    setAssetB('NVIDIA');
    setRollingWindow(60);
    setStartDate('');
    setEndDate('');
  };

  const comparisonColumns: Column<AssetComparisonMetrics>[] = [
    {
      header: 'Asset Name',
      accessor: 'asset',
      className: 'font-bold text-slate-100',
    },
    {
      header: 'Total Return',
      accessor: (row) =>
        row.total_return !== null
          ? `${(row.total_return * 100).toFixed(2)}%`
          : '—',
      sortable: true,
      sortKey: 'total_return',
    },
    {
      header: 'CAGR (Ann. Return)',
      accessor: (row) =>
        row.annualized_return !== null
          ? `${(row.annualized_return * 100).toFixed(2)}%`
          : '—',
      sortable: true,
      sortKey: 'annualized_return',
    },
    {
      header: 'Ann. Volatility',
      accessor: (row) =>
        row.annualized_volatility !== null
          ? `${(row.annualized_volatility * 100).toFixed(2)}%`
          : '—',
      sortable: true,
      sortKey: 'annualized_volatility',
    },
    {
      header: 'Sharpe Ratio',
      accessor: (row) =>
        row.sharpe_ratio !== null ? row.sharpe_ratio.toFixed(2) : '—',
      sortable: true,
      sortKey: 'sharpe_ratio',
    },
    {
      header: 'Max Drawdown',
      accessor: (row) => (
        <span className="text-rose-400">
          {row.maximum_drawdown !== null
            ? `${(row.maximum_drawdown * 100).toFixed(2)}%`
            : '—'}
        </span>
      ),
      sortable: true,
      sortKey: 'maximum_drawdown',
    },
    {
      header: 'Observations',
      accessor: (row) => row.observations.toLocaleString(),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Controls Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <CardTitle>Cross-Asset Correlation Controls</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Controls</span>
          </Button>
        </CardHeader>
        <CardContent className="p-4">
          <form onSubmit={handleApply} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Asset A</label>
              <Select value={assetA} onChange={(e) => setAssetA(e.target.value)}>
                <option value="Gold">Gold Spot</option>
                <option value="Bitcoin">Bitcoin (BTC)</option>
                <option value="NVIDIA">NVIDIA (NVDA)</option>
              </Select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Asset B</label>
              <Select value={assetB} onChange={(e) => setAssetB(e.target.value)}>
                <option value="Gold">Gold Spot</option>
                <option value="Bitcoin">Bitcoin (BTC)</option>
                <option value="NVIDIA">NVIDIA (NVDA)</option>
              </Select>
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Rolling Window (Days)</label>
              <Input
                type="number"
                min={5}
                max={252}
                value={rollingWindow}
                onChange={(e) => setRollingWindow(parseInt(e.target.value) || 60)}
              />
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

            <div className="flex items-end">
              <Button variant="primary" size="md" type="submit" className="w-full">
                Recalculate
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading && <LoadingState message="Computing Pearson correlation and covariance matrices..." />}

      {error && <ErrorState message={error} onRetry={fetchCorrelationData} />}

      {!loading && !error && (
        <>
          {/* Pairwise Metric Scorecard */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title={`Pairwise Correlation (${assetA} × ${assetB})`}
              value={pairData?.correlation !== null && pairData?.correlation !== undefined ? `${pairData.correlation >= 0 ? '+' : ''}${pairData.correlation.toFixed(4)}` : '—'}
              subtitle="Full sample Pearson coefficient"
              icon={<GitMerge className="w-4 h-4 text-cyan-400" />}
            />
            <MetricCard
              title="Daily Covariance"
              value={pairData?.covariance !== null && pairData?.covariance !== undefined ? pairData.covariance.toFixed(6) : '—'}
              subtitle="Co-movement magnitude"
            />
            <MetricCard
              title="Aligned Observations"
              value={pairData?.observations?.toLocaleString()}
              subtitle="Overlapping trading days"
              icon={<Calendar className="w-4 h-4 text-slate-400" />}
            />
            <MetricCard
              title="Time Horizon"
              value={pairData?.start_date ? `${pairData.start_date.slice(0, 4)} - ${pairData.end_date.slice(0, 4)}` : '—'}
              subtitle={`${pairData?.start_date} to ${pairData?.end_date}`}
            />
          </div>

          {/* Matrix and Rolling Correlation Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Correlation Matrix Heatmap */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Cross-Asset Correlation Matrix</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Pairwise Pearson correlation across aligned trading sessions
                  </p>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {matrixData && (
                  <CorrelationHeatmap
                    assets={matrixData.assets}
                    matrix={matrixData.matrix}
                    observations={matrixData.observations}
                    height={320}
                  />
                )}
              </CardContent>
            </Card>

            {/* Rolling Correlation Time-Series */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>{rollingWindow}-Day Rolling Correlation</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Dynamic time-varying correlation between {assetA} and {assetB}
                  </p>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {rollingData && (
                  <RollingCorrelationChart
                    data={rollingData.data}
                    assetA={assetA}
                    assetB={assetB}
                    window={rollingWindow}
                    height={320}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          {/* Asset Comparison Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Multi-Asset Comparative Performance Profile</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Objective statistical comparison across verified historical datasets (no rankings or subjective scoring)
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable data={comparisonList} columns={comparisonColumns} pageSize={10} />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
