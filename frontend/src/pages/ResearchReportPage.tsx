import React, { useEffect, useState } from 'react';
import {
  FileText,
  Printer,
  ShieldCheck,
  RotateCcw
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Select, Input } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { CorrelationHeatmap } from '../components/charts/CorrelationHeatmap';
import { PriceChart } from '../components/charts/PriceChart';
import { quantApi, correlationApi, strategyApi, regimeApi } from '../api';
import {
  AssetQuantSummaryResponse,
  IndicatorResponse,
  CorrelationMatrixResponse,
  StrategyResponse,
  RegimeResponse,
} from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const ResearchReportPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<AssetQuantSummaryResponse | null>(null);
  const [indicators, setIndicators] = useState<IndicatorResponse | null>(null);
  const [matrixData, setMatrixData] = useState<CorrelationMatrixResponse | null>(null);
  const [strategyData, setStrategyData] = useState<StrategyResponse | null>(null);
  const [regimeData, setRegimeData] = useState<RegimeResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const [sumRes, indRes, matRes, stratRes, regRes] = await Promise.all([
        quantApi.getAssetSummary(canonicalAsset, params),
        quantApi.getIndicators(canonicalAsset, { ...params, sma_period: 20, ema_period: 50 }),
        correlationApi.getCorrelationMatrix(params),
        strategyApi.getStrategySignals(canonicalAsset, 'sma_crossover', {
          ...params,
          fast_period: 20,
          slow_period: 50,
        }),
        regimeApi.getMarketRegimes(canonicalAsset, {
          ...params,
          trend_window: 50,
          volatility_window: 20,
        }),
      ]);

      setSummary(sumRes);
      setIndicators(indRes);
      setMatrixData(matRes);
      setStrategyData(stratRes);
      setRegimeData(regRes);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportData();
  }, [selectedAsset]);

  const handlePrint = () => {
    window.print();
  };

  const handleReset = () => {
    setStartDate('');
    setEndDate('');
  };

  return (
    <div className="space-y-6">
      {/* Top Action & Selector Card */}
      <Card className="print:hidden">
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-purple-400" />
            <CardTitle>Institutional Research Report Generator</CardTitle>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="xs" onClick={handleReset} className="text-slate-400">
              <RotateCcw className="w-3 h-3 mr-1" />
              <span>Reset</span>
            </Button>
            <Button variant="secondary" size="xs" onClick={handlePrint}>
              <Printer className="w-3.5 h-3.5 mr-1 text-slate-300" />
              <span>Print / Export PDF</span>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchReportData();
            }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
          >
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Target Asset</label>
              <Select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value as any)}
              >
                <option value="gold">Gold Spot (GC=F)</option>
                <option value="bitcoin">Bitcoin (2017 Dataset)</option>
                <option value="nvidia">NVIDIA Corp (NVDA)</option>
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

            <div className="flex items-end">
              <Button variant="primary" size="md" type="submit" className="w-full">
                Generate Teardown Report
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading && <LoadingState message={`Compiling institutional quantitative teardown for ${canonicalAsset}...`} />}

      {error && <ErrorState message={error} onRetry={fetchReportData} />}

      {!loading && !error && summary && (
        <div className="space-y-6">
          {/* Report Header Card */}
          <Card className="bg-[#0A0E17] border border-[#1E293B] p-6 shadow-2xl">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#1E293B] pb-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono text-cyan-400 uppercase tracking-widest font-semibold">
                    QUANTLAB RESEARCH MEMORANDUM
                  </span>
                  <Badge variant="cyan" size="xs">CONFIDENTIAL / RESEARCH</Badge>
                </div>
                <h1 className="text-xl sm:text-2xl font-bold font-mono text-slate-100 mt-1">
                  Quantitative Analysis & Regime Profile: {canonicalAsset}
                </h1>
                <p className="text-xs font-mono text-slate-400 mt-0.5">
                  Coverage: {summary.start_date} to {summary.end_date} • {summary.records.toLocaleString()} Daily Sessions
                </p>
              </div>

              <div className="text-right font-mono text-xs text-slate-400">
                <div>Engine: <span className="text-slate-200">FastAPI v0.1.0</span></div>
                <div>Status: <span className="text-emerald-400">Validated</span></div>
              </div>
            </div>

            {/* Executive Risk & Return Summary */}
            <div className="mt-6">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3">
                1. Executive Quantitative Profile
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <MetricCard
                  title="Latest Close"
                  value={`$${summary.latest_close.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                  variant="subpanel"
                />
                <MetricCard
                  title="Cumulative Return"
                  value={summary.cumulative_return ? `${(summary.cumulative_return * 100).toFixed(2)}%` : '—'}
                  isPositiveGood={true}
                  variant="subpanel"
                />
                <MetricCard
                  title="Ann. Volatility"
                  value={summary.annualized_volatility ? `${(summary.annualized_volatility * 100).toFixed(2)}%` : '—'}
                  variant="subpanel"
                />
                <MetricCard
                  title="Sharpe Ratio"
                  value={summary.sharpe_ratio !== null ? summary.sharpe_ratio?.toFixed(2) : '—'}
                  variant="subpanel"
                />
                <MetricCard
                  title="Max Drawdown"
                  value={summary.maximum_drawdown ? `${(summary.maximum_drawdown * 100).toFixed(2)}%` : '—'}
                  isPositiveGood={false}
                  className="text-rose-400"
                  variant="subpanel"
                />
                <MetricCard
                  title="Win Days Ratio"
                  value={`${((summary.return_statistics.positive_days / summary.records) * 100).toFixed(1)}%`}
                  subtitle={`${summary.return_statistics.positive_days} Up / ${summary.return_statistics.negative_days} Down`}
                  variant="subpanel"
                />
              </div>
            </div>
          </Card>

          {/* Price & Moving Average Indicators */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>2. Trend Indicator & Price Evolution</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Simple Moving Average (20) and Exponential Moving Average (50) overlay
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              {indicators && (
                <PriceChart
                  data={indicators.data}
                  assetName={canonicalAsset}
                  smaPeriod={20}
                  emaPeriod={50}
                  height={320}
                />
              )}
            </CardContent>
          </Card>

          {/* Cross-Asset Correlation & Regime Sections */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Correlation Context */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>3. Portfolio Correlation Context</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Pearson covariance matrix across multi-asset universe
                  </p>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {matrixData && (
                  <CorrelationHeatmap
                    assets={matrixData.assets}
                    matrix={matrixData.matrix}
                    observations={matrixData.observations}
                    height={260}
                  />
                )}
              </CardContent>
            </Card>

            {/* Regime Breakdown */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>4. Historical Market Regime Breakdown</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Empirical distributions across trend and volatility states
                  </p>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {regimeData?.summary_statistics ? (
                  <div className="space-y-3 font-mono text-xs">
                    <div className="flex justify-between items-center p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                      <Badge variant="emerald" size="xs">BULL REGIME</Badge>
                      <span className="text-slate-300">
                        {regimeData.summary_statistics.bull.observation_count} days ({(regimeData.summary_statistics.bull.percentage * 100).toFixed(1)}%) • Sharpe: {regimeData.summary_statistics.bull.sharpe_ratio?.toFixed(2) ?? '—'}
                      </span>
                    </div>

                    <div className="flex justify-between items-center p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                      <Badge variant="rose" size="xs">BEAR REGIME</Badge>
                      <span className="text-slate-300">
                        {regimeData.summary_statistics.bear.observation_count} days ({(regimeData.summary_statistics.bear.percentage * 100).toFixed(1)}%) • Sharpe: {regimeData.summary_statistics.bear.sharpe_ratio?.toFixed(2) ?? '—'}
                      </span>
                    </div>

                    <div className="flex justify-between items-center p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                      <Badge variant="amber" size="xs">HIGH VOLATILITY</Badge>
                      <span className="text-slate-300">
                        {regimeData.summary_statistics.high_volatility.observation_count} days ({(regimeData.summary_statistics.high_volatility.percentage * 100).toFixed(1)}%) • Ann. Vol: {regimeData.summary_statistics.high_volatility.annualized_volatility ? (regimeData.summary_statistics.high_volatility.annualized_volatility * 100).toFixed(1) + '%' : '—'}
                      </span>
                    </div>

                    <div className="flex justify-between items-center p-2.5 bg-[#121824] rounded border border-[#1E293B]">
                      <Badge variant="cyan" size="xs">LOW VOLATILITY</Badge>
                      <span className="text-slate-300">
                        {regimeData.summary_statistics.low_volatility.observation_count} days ({(regimeData.summary_statistics.low_volatility.percentage * 100).toFixed(1)}%) • Ann. Vol: {regimeData.summary_statistics.low_volatility.annualized_volatility ? (regimeData.summary_statistics.low_volatility.annualized_volatility * 100).toFixed(1) + '%' : '—'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs font-mono text-slate-500">No regime data available.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Strategy Baseline Snapshot */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>5. Deterministic Strategy Signal Baseline</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Benchmark SMA Crossover (20/50) point-in-time signal counts
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              {strategyData && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                  <div className="p-3 bg-[#121824] rounded border border-[#1E293B] text-center">
                    <span className="text-[10px] text-slate-400 uppercase block mb-1">BUY Signals</span>
                    <span className="text-base font-bold text-emerald-400">{strategyData.signal_counts.buy}</span>
                  </div>
                  <div className="p-3 bg-[#121824] rounded border border-[#1E293B] text-center">
                    <span className="text-[10px] text-slate-400 uppercase block mb-1">SELL Signals</span>
                    <span className="text-base font-bold text-rose-400">{strategyData.signal_counts.sell}</span>
                  </div>
                  <div className="p-3 bg-[#121824] rounded border border-[#1E293B] text-center">
                    <span className="text-[10px] text-slate-400 uppercase block mb-1">HOLD Days</span>
                    <span className="text-base font-bold text-slate-300">{strategyData.signal_counts.hold.toLocaleString()}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Mandatory Research Disclaimer */}
          <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-4 text-xs font-mono text-slate-500 space-y-1">
            <div className="flex items-center space-x-2 text-slate-400 font-semibold uppercase text-[11px]">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Institutional Research Disclaimer</span>
            </div>
            <p>
              Historical performance metrics, quantitative indicator calculations, market regime classifications, and backtested simulations are generated for empirical research, analytical benchmarking, and quantitative modeling purposes only. Past performance and statistical metrics do not guarantee future performance or future distribution characteristics.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
