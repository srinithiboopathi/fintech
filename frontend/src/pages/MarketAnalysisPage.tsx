import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  Activity,
  Sliders,
  Calendar,
  RotateCcw,
  BarChart2
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Button } from '../components/ui/Button';
import { Input, Select } from '../components/ui/Input';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { PriceChart } from '../components/charts/PriceChart';
import { ReturnsChart } from '../components/charts/ReturnsChart';
import { DrawdownChart } from '../components/charts/DrawdownChart';
import { quantApi } from '../api';
import {
  IndicatorResponse,
  ReturnsResponse,
  RiskMetricsResponse,
  RollingPerformanceResponse,
} from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const MarketAnalysisPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [smaPeriod, setSmaPeriod] = useState<number>(20);
  const [emaPeriod, setEmaPeriod] = useState<number>(50);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [returnsMode, setReturnsMode] = useState<'daily' | 'cumulative'>('daily');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [indicators, setIndicators] = useState<IndicatorResponse | null>(null);
  const [returnsData, setReturnsData] = useState<ReturnsResponse | null>(null);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetricsResponse | null>(null);
  const [rollingPerf, setRollingPerf] = useState<RollingPerformanceResponse | null>(null);

  const canonicalAsset =
    selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA';

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      };

      const [indRes, retRes, riskRes, rollingRes] = await Promise.all([
        quantApi.getIndicators(canonicalAsset, {
          ...params,
          sma_period: smaPeriod,
          ema_period: emaPeriod,
        }),
        quantApi.getReturns(canonicalAsset, params),
        quantApi.getRiskMetrics(canonicalAsset, params),
        quantApi.getRollingPerformance(canonicalAsset, params),
      ]);

      setIndicators(indRes);
      setReturnsData(retRes);
      setRiskMetrics(riskRes);
      setRollingPerf(rollingRes);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedAsset]);

  const handleApplyParams = (e: React.FormEvent) => {
    e.preventDefault();
    fetchData();
  };

  const handleResetDates = () => {
    setStartDate('');
    setEndDate('');
    setSmaPeriod(20);
    setEmaPeriod(50);
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Controls Card */}
      <Card>
        <CardHeader className="py-3">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <CardTitle>Technical Indicators & Filter Controls</CardTitle>
          </div>
          <Button variant="ghost" size="xs" onClick={handleResetDates} className="text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            <span>Reset Filters</span>
          </Button>
        </CardHeader>
        <CardContent className="p-4">
          <form onSubmit={handleApplyParams} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
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

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">SMA Period</label>
              <Input
                type="number"
                min={2}
                max={500}
                value={smaPeriod}
                onChange={(e) => setSmaPeriod(parseInt(e.target.value) || 20)}
              />
            </div>

            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">EMA Period</label>
              <Input
                type="number"
                min={2}
                max={500}
                value={emaPeriod}
                onChange={(e) => setEmaPeriod(parseInt(e.target.value) || 50)}
              />
            </div>

            <div className="flex items-end">
              <Button variant="primary" size="md" type="submit" className="w-full">
                Apply Parameters
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {loading && <LoadingState message={`Calculating quantitative metrics for ${canonicalAsset}...`} />}

      {error && <ErrorState message={error} onRetry={fetchData} />}

      {!loading && !error && (
        <>
          {/* Risk Metrics Scorecard */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Annualized Volatility"
              value={riskMetrics?.annualized_volatility ? (riskMetrics.annualized_volatility * 100).toFixed(2) + '%' : '—'}
              subtitle={`${riskMetrics?.annualization_factor ?? 252} trading day baseline`}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={riskMetrics?.sharpe_ratio !== null ? riskMetrics?.sharpe_ratio?.toFixed(2) : '—'}
              subtitle={`Risk-free rate: ${(riskMetrics?.risk_free_rate ?? 0) * 100}%`}
              isPositiveGood={true}
              icon={<TrendingUp className="w-4 h-4" />}
            />
            <MetricCard
              title="Maximum Drawdown"
              value={riskMetrics?.maximum_drawdown ? (riskMetrics.maximum_drawdown * 100).toFixed(2) + '%' : '—'}
              subtitle="Peak-to-trough drop"
              isPositiveGood={false}
              className="text-rose-400"
              icon={<BarChart2 className="w-4 h-4 text-rose-400" />}
            />
            <MetricCard
              title="Historical Records"
              value={riskMetrics?.records.toLocaleString()}
              subtitle={`${riskMetrics?.start_date} to ${riskMetrics?.end_date}`}
              icon={<Calendar className="w-4 h-4" />}
            />
          </div>

          {/* Main Price & Moving Averages Chart */}
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Historical Price & Trend Indicators • {canonicalAsset}</CardTitle>
                <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                  Daily settlement price with {smaPeriod}-period Simple Moving Average and {emaPeriod}-period Exponential Moving Average
                </p>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              {indicators && (
                <PriceChart
                  data={indicators.data}
                  assetName={canonicalAsset}
                  smaPeriod={smaPeriod}
                  emaPeriod={emaPeriod}
                  height={420}
                />
              )}
            </CardContent>
          </Card>

          {/* Returns and Drawdowns Split View */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Returns Chart */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Return Series Analysis</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    {returnsMode === 'daily' ? 'Arithmetic daily return distribution' : 'Compounded cumulative wealth growth'}
                  </p>
                </div>
                <div className="flex items-center space-x-1 bg-[#121824] p-0.5 rounded border border-[#1E293B]">
                  <button
                    onClick={() => setReturnsMode('daily')}
                    className={`px-2 py-0.5 text-xs font-mono rounded ${
                      returnsMode === 'daily' ? 'bg-cyan-950 text-cyan-300 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    Daily
                  </button>
                  <button
                    onClick={() => setReturnsMode('cumulative')}
                    className={`px-2 py-0.5 text-xs font-mono rounded ${
                      returnsMode === 'cumulative' ? 'bg-cyan-950 text-cyan-300 font-semibold' : 'text-slate-400'
                    }`}
                  >
                    Cumulative
                  </button>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {returnsData && <ReturnsChart data={returnsData.data} mode={returnsMode} height={280} />}
              </CardContent>
            </Card>

            {/* Drawdown Chart */}
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>Underwater Drawdown Profile</CardTitle>
                  <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                    Historical percentage decline from running peak wealth
                  </p>
                </div>
              </CardHeader>
              <CardContent className="p-4">
                {rollingPerf && (
                  <DrawdownChart
                    data={rollingPerf.data.map((d) => ({ date: d.date, drawdown: d.drawdown }))}
                    height={280}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
};
