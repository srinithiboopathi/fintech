import React, { useEffect, useState } from 'react';
import {
  Target,
  TrendingUp,
  Activity,
  Sparkles,
  Info,
  RotateCcw,
  CheckCircle2,
  Layers,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { EfficientFrontierChart } from '../components/charts';
import { portfolioApi } from '../api';
import {
  PortfolioOptimizationRequest,
  PortfolioOptimizationResponse,
} from '../types';
import { extractErrorMessage } from '../lib/api';

const ASSET_META: Record<string, { name: string; color: string; bg: string; border: string }> = {
  Gold: { name: 'Gold Spot', color: '#F59E0B', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  Bitcoin: { name: 'Bitcoin (BTC)', color: '#F97316', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  NVIDIA: { name: 'NVIDIA (NVDA)', color: '#10B981', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
};

export const PortfolioOptimizationPage: React.FC = () => {
  // Asset Universe selection
  const [selectedAssets, setSelectedAssets] = useState<string[]>(['Gold', 'Bitcoin', 'NVIDIA']);

  // Date and constraint parameters
  const [startDate, setStartDate] = useState<string>('2017-01-01');
  const [endDate, setEndDate] = useState<string>('2017-12-31');
  const [riskFreeRate, setRiskFreeRate] = useState<number>(2.0); // %
  const [minWeight, setMinWeight] = useState<number>(0); // %
  const [maxWeight, setMaxWeight] = useState<number>(100); // %
  const [randomPortfolios, setRandomPortfolios] = useState<number>(5000);
  const [frontierPoints, setFrontierPoints] = useState<number>(50);

  // Optional User Portfolio weights (in %)
  const [includeUserPortfolio, setIncludeUserPortfolio] = useState<boolean>(false);
  const [userWeights, setUserWeights] = useState<Record<string, number>>({
    Gold: 40,
    Bitcoin: 30,
    NVIDIA: 30,
  });

  // API State
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PortfolioOptimizationResponse | null>(null);

  // Validation logic
  const nAssets = selectedAssets.length;
  const isAssetCountValid = nAssets >= 2;
  const isSimplexMinFeasible = (nAssets * (minWeight / 100)) <= 1.0 + 1e-4;
  const isSimplexMaxFeasible = (nAssets * (maxWeight / 100)) >= 1.0 - 1e-4;
  const areBoundsValid = minWeight <= maxWeight && isSimplexMinFeasible && isSimplexMaxFeasible;

  const totalUserWeight = Number(
    selectedAssets.reduce((sum, asset) => sum + (userWeights[asset] || 0), 0).toFixed(2)
  );
  const isUserWeightValid = !includeUserPortfolio || Math.abs(totalUserWeight - 100.0) < 0.01;

  const canRun = isAssetCountValid && areBoundsValid && isUserWeightValid && !loading;

  const toggleAsset = (asset: string) => {
    if (selectedAssets.includes(asset)) {
      if (selectedAssets.length <= 2) return; // Keep at least 2
      setSelectedAssets(selectedAssets.filter((a) => a !== asset));
    } else {
      setSelectedAssets([...selectedAssets, asset]);
    }
  };

  const handleUserWeightChange = (asset: string, val: number) => {
    setUserWeights((prev) => ({
      ...prev,
      [asset]: val,
    }));
  };

  const runOptimization = async () => {
    if (!isAssetCountValid) {
      setError('Please select at least 2 distinct assets for portfolio optimization.');
      return;
    }
    if (!areBoundsValid) {
      setError('Constraint bounds are infeasible on the simplex.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let formattedUserWeights: Record<string, number> | undefined = undefined;
      if (includeUserPortfolio) {
        formattedUserWeights = {};
        selectedAssets.forEach((a) => {
          const w = userWeights[a] || 0;
          if (w > 0) formattedUserWeights![a] = Number((w / 100).toFixed(4));
        });
      }

      const payload: PortfolioOptimizationRequest = {
        assets: selectedAssets,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        risk_free_rate: riskFreeRate / 100,
        min_weight: minWeight / 100,
        max_weight: maxWeight / 100,
        random_portfolios: randomPortfolios,
        frontier_points: frontierPoints,
        random_seed: 42,
        user_weights: formattedUserWeights,
      };

      const res = await portfolioApi.optimizePortfolio(payload);
      setData(res);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runOptimization();
  }, []);

  // Presets
  const applyPreset = (
    assets: string[],
    start: string,
    end: string,
    minW: number,
    maxW: number
  ) => {
    setSelectedAssets(assets);
    setStartDate(start);
    setEndDate(end);
    setMinWeight(minW);
    setMaxWeight(maxW);
  };

  const handleReset = () => {
    applyPreset(['Gold', 'Bitcoin', 'NVIDIA'], '2017-01-01', '2017-12-31', 0, 100);
    setRiskFreeRate(2.0);
    setRandomPortfolios(5000);
    setFrontierPoints(50);
    setIncludeUserPortfolio(false);
  };

  return (
    <div className="space-y-6">
      {/* Parameter Control Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-cyan-400" />
              <CardTitle>Portfolio Optimization & Markowitz Frontier Controls</CardTitle>
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
          {/* Preset Buttons */}
          <div className="flex flex-wrap items-center gap-2 pb-3 border-b border-[#1E293B]">
            <span className="text-[10px] font-mono uppercase text-slate-400 mr-1 flex items-center">
              <Sparkles className="w-3 h-3 text-cyan-400 mr-1" /> Presets:
            </span>
            <button
              onClick={() => applyPreset(['Gold', 'Bitcoin', 'NVIDIA'], '2017-01-01', '2017-12-31', 0, 100)}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              3-Asset Standard (2017)
            </button>
            <button
              onClick={() => applyPreset(['Gold', 'Bitcoin', 'NVIDIA'], '2017-01-01', '2017-12-31', 10, 60)}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              Diversified Floor (10% to 60%)
            </button>
            <button
              onClick={() => applyPreset(['Gold', 'NVIDIA'], '2020-01-01', '2023-12-31', 0, 100)}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              Gold + NVIDIA (2020–2023)
            </button>
            <button
              onClick={() => applyPreset(['Gold', 'Bitcoin', 'NVIDIA'], '2017-01-01', '2017-12-31', 20, 50)}
              className="px-2.5 py-1 rounded text-xs font-mono bg-[#121824] hover:bg-[#1E293B] text-slate-300 border border-[#1E293B] transition-colors"
            >
              Tight Bounds (20% to 50%)
            </button>
          </div>

          {/* Asset Selection Universe */}
          <div className="space-y-1.5">
            <label className="block text-[10px] font-mono uppercase text-slate-400">
              Optimization Universe (Select $\ge$ 2)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {['Gold', 'Bitcoin', 'NVIDIA'].map((asset) => {
                const isSelected = selectedAssets.includes(asset);
                const meta = ASSET_META[asset];
                return (
                  <button
                    key={asset}
                    type="button"
                    onClick={() => toggleAsset(asset)}
                    className={`flex items-center justify-between p-3 rounded-lg border text-left transition-all ${
                      isSelected
                        ? `${meta.bg} ${meta.border} text-slate-100 shadow-[0_0_10px_rgba(0,0,0,0.3)]`
                        : 'bg-[#0A0E17] border-[#1E293B] text-slate-500 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: isSelected ? meta.color : '#475569' }}
                      />
                      <div>
                        <div className="text-xs font-mono font-bold">{asset}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{meta.name}</div>
                      </div>
                    </div>
                    {isSelected ? (
                      <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    ) : (
                      <span className="text-[10px] font-mono text-slate-600">Excluded</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dates & Weight Bounds Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
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

            {/* Min Weight Bound Slider */}
            <div className="bg-[#0A0E17] border border-[#1E293B] p-2.5 rounded space-y-1">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-400 uppercase">Min Weight Bound</span>
                <span className="text-cyan-400 font-bold">{minWeight}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={minWeight}
                onChange={(e) => setMinWeight(parseInt(e.target.value) || 0)}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>

            {/* Max Weight Bound Slider */}
            <div className="bg-[#0A0E17] border border-[#1E293B] p-2.5 rounded space-y-1">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-400 uppercase">Max Weight Bound</span>
                <span className="text-cyan-400 font-bold">{maxWeight}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="100"
                step="5"
                value={maxWeight}
                onChange={(e) => setMaxWeight(parseInt(e.target.value) || 100)}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
          </div>

          {/* Secondary Controls: Risk-Free Rate, Simulation Counts, Optional User Portfolio */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
            {/* Risk-Free Rate */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Risk-Free Rate (Rf %)
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

            {/* Random Portfolios Count */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Feasible Random Portfolios
              </label>
              <Input
                type="number"
                min="500"
                max="10000"
                step="500"
                value={randomPortfolios}
                onChange={(e) => setRandomPortfolios(parseInt(e.target.value) || 5000)}
              />
            </div>

            {/* Frontier Points Count */}
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Frontier Resolution (Points)
              </label>
              <Input
                type="number"
                min="10"
                max="100"
                step="5"
                value={frontierPoints}
                onChange={(e) => setFrontierPoints(parseInt(e.target.value) || 50)}
              />
            </div>
          </div>

          {/* Optional User Portfolio Section */}
          <div className="bg-[#0A0E17] border border-[#1E293B] p-3.5 rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="user-port-toggle"
                  checked={includeUserPortfolio}
                  onChange={(e) => setIncludeUserPortfolio(e.target.checked)}
                  className="rounded border-[#1E293B] bg-[#121824] text-cyan-500 focus:ring-0 cursor-pointer"
                />
                <label
                  htmlFor="user-port-toggle"
                  className="text-xs font-mono font-semibold text-slate-200 cursor-pointer"
                >
                  Evaluate Custom User Portfolio Comparison Marker
                </label>
              </div>

              {includeUserPortfolio && (
                <div className="flex items-center space-x-2 text-xs font-mono">
                  <span className="text-slate-400">Sum:</span>
                  <span
                    className={`font-bold ${
                      Math.abs(totalUserWeight - 100.0) < 0.01 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {totalUserWeight}%
                  </span>
                  <span className="text-slate-500">/ 100%</span>
                </div>
              )}
            </div>

            {includeUserPortfolio && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                {selectedAssets.map((asset) => (
                  <div key={asset} className="bg-[#121824] p-2.5 rounded border border-[#1E293B] space-y-1">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300 font-semibold">{asset}</span>
                      <span className="text-purple-400 font-bold">{userWeights[asset] || 0}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={userWeights[asset] || 0}
                      onChange={(e) => handleUserWeightChange(asset, parseFloat(e.target.value) || 0)}
                      className="w-full accent-purple-400 cursor-pointer"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Action Bar */}
          <div className="flex items-center justify-between pt-1">
            <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span>
                {selectedAssets.includes('Bitcoin')
                  ? 'Bitcoin is selected: Multi-asset optimization is synchronized on calendar year 2017 common trading dates.'
                  : 'Gold & NVIDIA selected: Full historical horizon available.'}
              </span>
            </div>

            <Button
              variant="primary"
              size="md"
              disabled={!canRun}
              onClick={runOptimization}
              className="px-6"
            >
              {loading ? 'Optimizing Frontier...' : 'Optimize Portfolio'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading & Error States */}
      {loading && <LoadingState message="Solving Markowitz Mean-Variance quadratic optimizations and tracing frontier..." />}
      {error && <ErrorState message={error} onRetry={runOptimization} />}

      {!loading && !error && data && (
        <>
          {/* Key Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Maximum Sharpe Card */}
            <MetricCard
              title="Maximum Sharpe Portfolio"
              value={`${(data.optimal_portfolios.max_sharpe.expected_return * 100).toFixed(2)}%`}
              subtitle={`Vol: ${(data.optimal_portfolios.max_sharpe.volatility * 100).toFixed(2)}% | Sharpe: ${data.optimal_portfolios.max_sharpe.sharpe_ratio.toFixed(2)}`}
              icon={<TrendingUp className="w-4 h-4 text-cyan-400" />}
            />

            {/* Minimum Volatility Card */}
            <MetricCard
              title="Minimum Volatility (GMV)"
              value={`${(data.optimal_portfolios.min_volatility.volatility * 100).toFixed(2)}%`}
              subtitle={`Return: ${(data.optimal_portfolios.min_volatility.expected_return * 100).toFixed(2)}% | Sharpe: ${data.optimal_portfolios.min_volatility.sharpe_ratio.toFixed(2)}`}
              icon={<Activity className="w-4 h-4 text-emerald-400" />}
            />

            {/* Equal Weight Card */}
            <MetricCard
              title="Equal Weight Benchmark (1/N)"
              value={`${(data.optimal_portfolios.equal_weight.expected_return * 100).toFixed(2)}%`}
              subtitle={`Vol: ${(data.optimal_portfolios.equal_weight.volatility * 100).toFixed(2)}% | Sharpe: ${data.optimal_portfolios.equal_weight.sharpe_ratio.toFixed(2)}`}
              icon={<Layers className="w-4 h-4 text-amber-400" />}
            />
          </div>

          {/* Efficient Frontier Chart Card */}
          <Card>
            <CardHeader className="py-3">
              <div className="flex items-center justify-between w-full">
                <div>
                  <CardTitle>Markowitz Efficient Frontier & Feasible Portfolio Cloud</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Continuous efficient frontier curve overlaid on {data.random_portfolios.length.toLocaleString()} sampled feasible portfolios (X: Volatility, Y: Expected Return)
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="default" className="font-mono text-[10px]">
                    {data.observations} Aligned Trading Days ({data.start_date} to {data.end_date})
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <EfficientFrontierChart
                efficientFrontier={data.efficient_frontier}
                randomPortfolios={data.random_portfolios}
                optimalPortfolios={data.optimal_portfolios}
                riskFreeRate={data.risk_free_rate}
                height={500}
              />
            </CardContent>
          </Card>

          {/* Allocation Weights Comparison Matrix */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Optimal Portfolio Asset Allocation Weights</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Comparative capital distribution across computed optimal configurations and user portfolio
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Max Sharpe Allocation */}
                <div className="bg-[#0A0E17] border border-cyan-500/30 p-4 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                      <span className="font-mono font-bold text-xs text-cyan-300">Maximum Sharpe</span>
                    </div>
                    <Badge variant="default" className="text-[10px]">
                      Sharpe {data.optimal_portfolios.max_sharpe.sharpe_ratio.toFixed(2)}
                    </Badge>
                  </div>
                  <div className="space-y-2 pt-1 font-mono text-xs">
                    {Object.entries(data.optimal_portfolios.max_sharpe.weights).map(([asset, weight]) => (
                      <div key={asset} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-300">{asset}</span>
                          <span className="font-bold text-cyan-300">{(weight * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-[#121824] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-cyan-400 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, weight * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Minimum Volatility Allocation */}
                <div className="bg-[#0A0E17] border border-emerald-500/30 p-4 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                      <span className="font-mono font-bold text-xs text-emerald-300">Minimum Volatility</span>
                    </div>
                    <Badge variant="default" className="text-[10px]">
                      Vol {(data.optimal_portfolios.min_volatility.volatility * 100).toFixed(2)}%
                    </Badge>
                  </div>
                  <div className="space-y-2 pt-1 font-mono text-xs">
                    {Object.entries(data.optimal_portfolios.min_volatility.weights).map(([asset, weight]) => (
                      <div key={asset} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-300">{asset}</span>
                          <span className="font-bold text-emerald-300">{(weight * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-[#121824] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-400 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, weight * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Equal Weight Allocation */}
                <div className="bg-[#0A0E17] border border-amber-500/30 p-4 rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                      <span className="font-mono font-bold text-xs text-amber-300">Equal Weight (1/N)</span>
                    </div>
                    <Badge variant="default" className="text-[10px]">
                      1/{data.assets.length} Benchmark
                    </Badge>
                  </div>
                  <div className="space-y-2 pt-1 font-mono text-xs">
                    {Object.entries(data.optimal_portfolios.equal_weight.weights).map(([asset, weight]) => (
                      <div key={asset} className="space-y-1">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="text-slate-300">{asset}</span>
                          <span className="font-bold text-amber-300">{(weight * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-[#121824] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-amber-400 rounded-full"
                            style={{ width: `${Math.min(100, Math.max(0, weight * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Descriptive Non-Ranking Comparison Table */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Descriptive Portfolio Strategy Comparison</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Objective quantitative summary of portfolio profiles. Portfolios are presented for comparative analysis without normative rankings.
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead>
                    <tr className="border-b border-[#1E293B] text-slate-400">
                      <th className="py-2.5 px-3">Strategy Designation</th>
                      <th className="py-2.5 px-3 text-right">Expected Return (Ann.)</th>
                      <th className="py-2.5 px-3 text-right">Volatility (Ann.)</th>
                      <th className="py-2.5 px-3 text-right">Sharpe Ratio (Rf={riskFreeRate}%)</th>
                      <th className="py-2.5 px-3">Asset Weight Allocations</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.comparison.map((row) => (
                      <tr key={row.name} className="border-b border-[#1E293B]/60 hover:bg-[#121824]">
                        <td className="py-3 px-3 font-semibold text-slate-200 flex items-center space-x-2">
                          <span
                            className="w-2 h-2 rounded-full"
                            style={{
                              backgroundColor:
                                row.name === 'Maximum Sharpe'
                                  ? '#38BDF8'
                                  : row.name === 'Minimum Volatility'
                                  ? '#10B981'
                                  : row.name === 'Equal Weight'
                                  ? '#F59E0B'
                                  : '#A855F7',
                            }}
                          />
                          <span>{row.name}</span>
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-emerald-400">
                          {row.expected_return >= 0 ? '+' : ''}{(row.expected_return * 100).toFixed(2)}%
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-amber-400">
                          {(row.volatility * 100).toFixed(2)}%
                        </td>
                        <td className="py-3 px-3 text-right font-bold text-cyan-300">
                          {row.sharpe_ratio.toFixed(2)}
                        </td>
                        <td className="py-3 px-3 text-slate-300">
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(row.weights).map(([asset, w]) => (
                              <span
                                key={asset}
                                className="px-1.5 py-0.5 rounded bg-[#0A0E17] border border-[#1E293B] text-[11px]"
                              >
                                {asset}: <b>{(w * 100).toFixed(1)}%</b>
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Methodology Non-Prediction Notice */}
              <div className="bg-[#0A0E17] border border-[#1E293B] p-3 rounded-lg text-xs font-mono text-slate-400 flex items-start space-x-2.5">
                <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-200">Non-Optimization Principle & Disclosure: </span>
                  Markowitz Modern Portfolio Theory calculations are based strictly on historical synchronized sample returns. Past correlations and covariances do not guarantee future performance. No portfolio is labeled or recommended as "best" or an investment directive.
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
