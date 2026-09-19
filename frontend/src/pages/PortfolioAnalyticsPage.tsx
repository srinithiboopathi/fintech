import React, { useEffect, useState } from 'react';
import {
  PieChart,
  DollarSign,
  TrendingUp,
  Activity,
  Shield,
  Sparkles,
  Info,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { DataTable, Column } from '../components/ui/DataTable';
import {
  PortfolioEquityChart,
  PortfolioComparisonChart,
  PortfolioDrawdownChart,
} from '../components/charts';
import { portfolioApi } from '../api';
import {
  PortfolioAnalysisRequest,
  PortfolioAnalysisResponse,
  AssetPerformanceContribution,
  AssetRiskContribution,
} from '../types';
import { extractErrorMessage } from '../lib/api';

const ASSET_META: Record<string, { name: string; color: string; bg: string; border: string }> = {
  Gold: { name: 'Gold Spot', color: '#F59E0B', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  Bitcoin: { name: 'Bitcoin (BTC)', color: '#F97316', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  NVIDIA: { name: 'NVIDIA (NVDA)', color: '#10B981', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
};

export const PortfolioAnalyticsPage: React.FC = () => {
  // Asset weight state in percentage (0 - 100)
  const [goldWeight, setGoldWeight] = useState<number>(40);
  const [btcWeight, setBtcWeight] = useState<number>(30);
  const [nvdaWeight, setNvdaWeight] = useState<number>(30);

  // Parameter state
  const [startDate, setStartDate] = useState<string>('2017-01-01');
  const [endDate, setEndDate] = useState<string>('2017-12-31');
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(2.0); // in percent

  // Tab & API state
  const [activeTab, setActiveTab] = useState<'equity' | 'comparison' | 'drawdown'>('equity');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PortfolioAnalysisResponse | null>(null);

  const totalWeight = Number((goldWeight + btcWeight + nvdaWeight).toFixed(2));
  const isWeightValid = Math.abs(totalWeight - 100.0) < 0.01;

  const runAnalysis = async () => {
    if (!isWeightValid) {
      setError(`Portfolio weights must total 100%. Current sum: ${totalWeight}%.`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const weightsObj: Record<string, number> = {};
      if (goldWeight > 0) weightsObj['Gold'] = Number((goldWeight / 100).toFixed(4));
      if (btcWeight > 0) weightsObj['Bitcoin'] = Number((btcWeight / 100).toFixed(4));
      if (nvdaWeight > 0) weightsObj['NVIDIA'] = Number((nvdaWeight / 100).toFixed(4));

      const payload: PortfolioAnalysisRequest = {
        weights: weightsObj,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        initial_capital: initialCapital,
        risk_free_rate: riskFreeRate / 100,
      };

      const res = await portfolioApi.analyzePortfolio(payload);
      setData(res);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAnalysis();
  }, []);

  // Presets
  const applyPreset = (gold: number, btc: number, nvda: number, start?: string, end?: string) => {
    setGoldWeight(gold);
    setBtcWeight(btc);
    setNvdaWeight(nvda);
    if (start) setStartDate(start);
    if (end) setEndDate(end);
  };

  const handleReset = () => {
    applyPreset(40, 30, 30, '2017-01-01', '2017-12-31');
    setInitialCapital(100000);
    setRiskFreeRate(2.0);
  };

  // Performance contribution columns
  const perfColumns: Column<AssetPerformanceContribution>[] = [
    {
      header: 'Asset',
      accessor: (row) => (
        <div className="flex items-center space-x-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: ASSET_META[row.asset]?.color || '#94A3B8' }}
          />
          <span className="font-semibold text-slate-100">{row.asset}</span>
          <span className="text-[10px] text-slate-500 font-mono">({ASSET_META[row.asset]?.name})</span>
        </div>
      ),
    },
    {
      header: 'Allocation Weight',
      accessor: (row) => `${(row.weight * 100).toFixed(1)}%`,
      sortable: true,
      sortKey: 'weight',
    },
    {
      header: 'Asset Standalone Return',
      accessor: (row) => {
        const isPos = row.total_return >= 0;
        return (
          <span className={isPos ? 'text-emerald-400 font-mono' : 'text-rose-400 font-mono'}>
            {isPos ? '+' : ''}{(row.total_return * 100).toFixed(2)}%
          </span>
        );
      },
      sortable: true,
      sortKey: 'total_return',
    },
    {
      header: 'Weighted Return Contribution',
      accessor: (row) => {
        const isPos = row.weighted_contribution >= 0;
        return (
          <span className={isPos ? 'text-emerald-400 font-mono font-bold' : 'text-rose-400 font-mono font-bold'}>
            {isPos ? '+' : ''}{(row.weighted_contribution * 100).toFixed(2)}%
          </span>
        );
      },
      sortable: true,
      sortKey: 'weighted_contribution',
    },
    {
      header: '% of Portfolio Return',
      accessor: (row) => {
        if (row.contribution_percentage === null || row.contribution_percentage === undefined) return '—';
        return (
          <div className="flex items-center space-x-2">
            <span className="font-mono text-slate-200">
              {(row.contribution_percentage * 100).toFixed(1)}%
            </span>
            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-400 rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, row.contribution_percentage * 100))}%` }}
              />
            </div>
          </div>
        );
      },
    },
  ];

  // Risk contribution columns
  const riskColumns: Column<AssetRiskContribution>[] = [
    {
      header: 'Asset',
      accessor: (row) => (
        <div className="flex items-center space-x-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: ASSET_META[row.asset]?.color || '#94A3B8' }}
          />
          <span className="font-semibold text-slate-100">{row.asset}</span>
        </div>
      ),
    },
    {
      header: 'Weight',
      accessor: (row) => `${(row.weight * 100).toFixed(1)}%`,
    },
    {
      header: 'Standalone Volatility (Ann.)',
      accessor: (row) => `${(row.annualized_volatility * 100).toFixed(2)}%`,
    },
    {
      header: 'Marginal Risk Contribution (MCR)',
      accessor: (row) => (
        <span className="font-mono text-slate-300">
          {(row.marginal_risk_contribution * 100).toFixed(2)}%
        </span>
      ),
    },
    {
      header: 'Component Risk (CCR)',
      accessor: (row) => (
        <span className="font-mono font-bold text-cyan-300">
          {(row.component_risk_contribution * 100).toFixed(2)}%
        </span>
      ),
      sortable: true,
      sortKey: 'component_risk_contribution',
    },
    {
      header: '% Total Portfolio Risk',
      accessor: (row) => (
        <div className="flex items-center space-x-2">
          <span className="font-mono font-bold text-amber-300">
            {(row.percentage_risk_contribution * 100).toFixed(1)}%
          </span>
          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-400 rounded-full"
              style={{ width: `${Math.min(100, Math.max(0, row.percentage_risk_contribution * 100))}%` }}
            />
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Configuration Header Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center space-x-2">
              <PieChart className="w-4 h-4 text-cyan-400" />
              <CardTitle>Multi-Asset Portfolio Construction</CardTitle>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
                <RotateCcw className="w-3 h-3 mr-1" />
                <span>Reset Defaults</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-4 space-y-4">
          {/* Preset buttons */}
          <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-[#1E293B]">
            <span className="text-[10px] font-mono uppercase text-slate-400 mr-1 flex items-center">
              <Sparkles className="w-3 h-3 text-cyan-400 mr-1" /> Allocation Presets:
            </span>
            <button
              onClick={() => applyPreset(40, 30, 30, '2017-01-01', '2017-12-31')}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              Balanced 40/30/30 (2017)
            </button>
            <button
              onClick={() => applyPreset(33.33, 33.33, 33.34, '2017-01-01', '2017-12-31')}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              Equal Weight (1/3 Each)
            </button>
            <button
              onClick={() => applyPreset(40, 0, 60, '2020-01-01', '2023-12-31')}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              60/40 Equity-Gold (2020–2023)
            </button>
            <button
              onClick={() => applyPreset(100, 0, 0, '2015-01-01', '2024-12-31')}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              100% Gold Spot
            </button>
            <button
              onClick={() => applyPreset(0, 0, 100, '2015-01-01', '2024-12-31')}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              100% NVIDIA Alpha
            </button>
          </div>

          {/* Asset Weight Allocators */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Gold Weight */}
            <div className="bg-[#0A0E17] border border-[#1E293B] p-3.5 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                  <span className="text-xs font-semibold text-slate-100 font-mono">Gold Spot (XAU)</span>
                </div>
                <span className="text-xs font-mono font-bold text-amber-400">{goldWeight}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={goldWeight}
                onChange={(e) => setGoldWeight(parseFloat(e.target.value) || 0)}
                className="w-full accent-amber-400 cursor-pointer"
              />
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>0%</span>
                <div className="flex items-center space-x-1">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={goldWeight}
                    onChange={(e) => setGoldWeight(parseFloat(e.target.value) || 0)}
                    className="w-16 h-6 text-xs text-right py-0"
                  />
                  <span>%</span>
                </div>
                <span>100%</span>
              </div>
            </div>

            {/* Bitcoin Weight */}
            <div className="bg-[#0A0E17] border border-[#1E293B] p-3.5 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-orange-400" />
                  <span className="text-xs font-semibold text-slate-100 font-mono">Bitcoin (BTC)</span>
                </div>
                <span className="text-xs font-mono font-bold text-orange-400">{btcWeight}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={btcWeight}
                onChange={(e) => setBtcWeight(parseFloat(e.target.value) || 0)}
                className="w-full accent-orange-400 cursor-pointer"
              />
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>0%</span>
                <div className="flex items-center space-x-1">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={btcWeight}
                    onChange={(e) => setBtcWeight(parseFloat(e.target.value) || 0)}
                    className="w-16 h-6 text-xs text-right py-0"
                  />
                  <span>%</span>
                </div>
                <span>100%</span>
              </div>
            </div>

            {/* NVIDIA Weight */}
            <div className="bg-[#0A0E17] border border-[#1E293B] p-3.5 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span className="text-xs font-semibold text-slate-100 font-mono">NVIDIA (NVDA)</span>
                </div>
                <span className="text-xs font-mono font-bold text-emerald-400">{nvdaWeight}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={nvdaWeight}
                onChange={(e) => setNvdaWeight(parseFloat(e.target.value) || 0)}
                className="w-full accent-emerald-400 cursor-pointer"
              />
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                <span>0%</span>
                <div className="flex items-center space-x-1">
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={nvdaWeight}
                    onChange={(e) => setNvdaWeight(parseFloat(e.target.value) || 0)}
                    className="w-16 h-6 text-xs text-right py-0"
                  />
                  <span>%</span>
                </div>
                <span>100%</span>
              </div>
            </div>
          </div>

          {/* Allocation Validation & Secondary Parameters */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-2">
            {/* Weight Status */}
            <div className="flex flex-col justify-center bg-[#0A0E17] border border-[#1E293B] p-2.5 rounded">
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1 flex items-center justify-between">
                <span>Total Allocation</span>
                {isWeightValid ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                )}
              </div>
              <div className="flex items-baseline space-x-2">
                <span
                  className={`text-lg font-mono font-bold ${
                    isWeightValid ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {totalWeight}%
                </span>
                <span className="text-[10px] font-mono text-slate-500">/ 100.0%</span>
              </div>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Start Date
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                End Date
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>

            {/* Initial Capital */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Capital ($)
              </label>
              <Input
                type="number"
                min="1000"
                step="1000"
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 100000)}
              />
            </div>

            {/* Risk-Free Rate */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Risk-Free Rate (%)
              </label>
              <Input
                type="number"
                min="0"
                max="20"
                step="0.25"
                value={riskFreeRate}
                onChange={(e) => setRiskFreeRate(parseFloat(e.target.value) || 0)}
              />
            </div>
          </div>

          {/* Weight Warning or Run Button */}
          <div className="flex items-center justify-between pt-1">
            <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
              <Info className="w-3.5 h-3.5 text-cyan-400" />
              <span>
                {btcWeight > 0
                  ? 'Bitcoin data is active: Evaluation synchronized on calendar year 2017 common trading dates.'
                  : 'Gold & NVIDIA active: Multi-year full horizon evaluation available.'}
              </span>
            </div>

            <Button
              variant="primary"
              size="md"
              disabled={!isWeightValid || loading}
              onClick={runAnalysis}
              className="px-6"
            >
              {loading ? 'Computing Portfolio...' : 'Analyze Portfolio'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading & Error States */}
      {loading && <LoadingState message="Synchronizing multi-asset returns and decomposing Euler risk..." />}
      {error && <ErrorState message={error} onRetry={runAnalysis} />}

      {!loading && !error && data && (
        <>
          {/* Key Portfolio Summary Scorecards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Portfolio Ending Value"
              value={`$${data.summary.final_value.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}`}
              subtitle={`From $${data.summary.initial_capital.toLocaleString()} initial capital`}
              icon={<DollarSign className="w-4 h-4 text-cyan-400" />}
            />

            <MetricCard
              title="Cumulative Total Return"
              value={`${data.summary.total_return >= 0 ? '+' : ''}${(
                data.summary.total_return * 100
              ).toFixed(2)}%`}
              subtitle={`CAGR: ${(data.summary.annualized_return * 100).toFixed(2)}%`}
              icon={<TrendingUp className="w-4 h-4 text-emerald-400" />}
            />

            <MetricCard
              title="Annualized Volatility"
              value={`${(data.summary.annualized_volatility * 100).toFixed(2)}%`}
              subtitle={`Sharpe Ratio: ${data.summary.sharpe_ratio.toFixed(2)} (Rf=${riskFreeRate}%)`}
              icon={<Activity className="w-4 h-4 text-amber-400" />}
            />

            <MetricCard
              title="Maximum Drawdown"
              value={`${(data.summary.maximum_drawdown * 100).toFixed(2)}%`}
              subtitle={`${data.summary.observations} aligned days (${data.summary.start_date} to ${data.summary.end_date})`}
              icon={<Shield className="w-4 h-4 text-rose-400" />}
            />
          </div>

          {/* Interactive Chart Section */}
          <Card>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between w-full">
                <div>
                  <CardTitle>
                    {activeTab === 'equity' && 'Portfolio Equity Growth ($USD)'}
                    {activeTab === 'comparison' && 'Normalized Asset Performance (Base = 100)'}
                    {activeTab === 'drawdown' && 'Portfolio Underwater Drawdown Profile'}
                  </CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {activeTab === 'equity' && 'Dollar equity curve calculated from daily aligned weighted returns'}
                    {activeTab === 'comparison' && 'Objective comparative growth against standalone constituent assets'}
                    {activeTab === 'drawdown' && 'Peak-to-trough historical drawdown series'}
                  </p>
                </div>

                {/* Tab switcher */}
                <div className="flex items-center bg-[#121824] border border-[#1E293B] rounded p-0.5 text-xs font-mono">
                  <button
                    onClick={() => setActiveTab('equity')}
                    className={`px-3 py-1 rounded transition-colors ${
                      activeTab === 'equity'
                        ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/50'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Equity Curve
                  </button>
                  <button
                    onClick={() => setActiveTab('comparison')}
                    className={`px-3 py-1 rounded transition-colors ${
                      activeTab === 'comparison'
                        ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/50'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Asset Comparison (Base 100)
                  </button>
                  <button
                    onClick={() => setActiveTab('drawdown')}
                    className={`px-3 py-1 rounded transition-colors ${
                      activeTab === 'drawdown'
                        ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/50'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Drawdown
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              {activeTab === 'equity' && (
                <PortfolioEquityChart
                  data={data.data}
                  initialCapital={data.summary.initial_capital}
                  height={420}
                />
              )}
              {activeTab === 'comparison' && (
                <PortfolioComparisonChart data={data.comparison} height={420} />
              )}
              {activeTab === 'drawdown' && (
                <PortfolioDrawdownChart data={data.data} height={420} />
              )}
            </CardContent>
          </Card>

          {/* Asset Return Contribution Analysis */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Asset Performance Contribution Decomposition</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Decomposition of portfolio return into asset standalone return and weighted return contribution (w_i × R_i)
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <DataTable
                data={data.performance_contributions}
                columns={perfColumns}
                pageSize={5}
              />
            </CardContent>
          </Card>

          {/* Euler Risk Contribution Analysis */}
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center md:justify-between w-full gap-2">
                <div>
                  <CardTitle>Portfolio Risk Contribution & Euler Volatility Decomposition</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Marginal and Component Risk Contributions derived from annualized covariance matrix (Σ = 252 × Σ_daily)
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="default" className="font-mono text-[10px]">
                    Euler Identity: Σ CCR_i = σ_p ({(data.summary.annualized_volatility * 100).toFixed(2)}%)
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <DataTable
                data={data.risk_contributions}
                columns={riskColumns}
                pageSize={5}
              />

              {/* Informational distinction note */}
              <div className="bg-[#0A0E17] border border-[#1E293B] p-3 rounded-lg text-xs font-mono text-slate-400 flex items-start space-x-2.5">
                <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-200">Institutional Methodology Note: </span>
                  Performance contribution describes asset contribution to portfolio compound return (w_i × R_i).
                  Risk contribution describes component contribution to total portfolio annualized volatility (CCR_i = w_i · (Σw)_i / σ_p).
                  Due to asset correlation and covariance interaction, an asset's risk contribution may differ significantly from its nominal capital weight.
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Annualized Covariance Matrix Snapshot */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Annualized Covariance Matrix (252-Day Factor)</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Pairwise annualized variance and covariance used in Euler risk decomposition
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-[#1E293B] text-slate-400">
                      <th className="py-2 px-3">Asset</th>
                      {Object.keys(data.covariance_matrix).map((asset) => (
                        <th key={asset} className="py-2 px-3 text-right">
                          {asset}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(data.covariance_matrix).map(([rowAsset, colVals]) => (
                      <tr key={rowAsset} className="border-b border-[#1E293B]/50 hover:bg-[#121824]">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">{rowAsset}</td>
                        {Object.entries(colVals).map(([colAsset, val]) => (
                          <td
                            key={colAsset}
                            className={`py-2.5 px-3 text-right ${
                              rowAsset === colAsset ? 'text-cyan-400 font-bold' : 'text-slate-300'
                            }`}
                          >
                            {(val * 10000).toFixed(2)} <span className="text-[9px] text-slate-500">×10⁻⁴</span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
