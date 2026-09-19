import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  Gauge,
  ArrowRight,
  ShieldAlert,
  PlayCircle,
  PieChart,
  FileText
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { LoadingState } from '../components/ui/LoadingState';
import { ErrorState } from '../components/ui/ErrorState';
import { CorrelationHeatmap } from '../components/charts/CorrelationHeatmap';
import { PerformanceChart } from '../components/charts/PerformanceChart';
import { quantApi, correlationApi, regimeApi } from '../api';
import {
  AssetQuantSummaryResponse,
  CorrelationMatrixResponse,
  RegimeResponse,
} from '../types';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const DashboardPage: React.FC = () => {
  const { selectedAsset, setSelectedAsset } = useAppStore();

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Asset summaries
  const [goldSummary, setGoldSummary] = useState<AssetQuantSummaryResponse | null>(null);
  const [btcSummary, setBtcSummary] = useState<AssetQuantSummaryResponse | null>(null);
  const [nvdaSummary, setNvdaSummary] = useState<AssetQuantSummaryResponse | null>(null);

  // Comparative performance data
  const [perfSeries, setPerfSeries] = useState<
    Array<{ asset: string; data: Array<{ date: string; cumulative_return: number }>; color: string }>
  >([]);

  // Correlation matrix
  const [corrMatrix, setCorrMatrix] = useState<CorrelationMatrixResponse | null>(null);

  // Current Regime for selected asset
  const [regimeData, setRegimeData] = useState<RegimeResponse | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [
        goldRes,
        btcRes,
        nvdaRes,
        goldRet,
        btcRet,
        nvdaRet,
        matrixRes,
        currentRegimeRes,
      ] = await Promise.all([
        quantApi.getAssetSummary('Gold'),
        quantApi.getAssetSummary('Bitcoin'),
        quantApi.getAssetSummary('NVIDIA'),
        quantApi.getReturns('Gold'),
        quantApi.getReturns('Bitcoin'),
        quantApi.getReturns('NVIDIA'),
        correlationApi.getCorrelationMatrix(),
        regimeApi.getMarketRegimes(
          selectedAsset === 'gold' ? 'Gold' : selectedAsset === 'bitcoin' ? 'Bitcoin' : 'NVIDIA'
        ),
      ]);

      setGoldSummary(goldRes);
      setBtcSummary(btcRes);
      setNvdaSummary(nvdaRes);

      // Build performance comparison series
      const series = [
        {
          asset: 'Gold',
          color: '#F59E0B',
          data: goldRet.data
            .filter((d) => d.cumulative_return !== null)
            .map((d) => ({ date: d.date, cumulative_return: d.cumulative_return! })),
        },
        {
          asset: 'Bitcoin (2017)',
          color: '#F97316',
          data: btcRet.data
            .filter((d) => d.cumulative_return !== null)
            .map((d) => ({ date: d.date, cumulative_return: d.cumulative_return! })),
        },
        {
          asset: 'NVIDIA',
          color: '#84CC16',
          data: nvdaRet.data
            .filter((d) => d.cumulative_return !== null)
            .map((d) => ({ date: d.date, cumulative_return: d.cumulative_return! })),
        },
      ];
      setPerfSeries(series);

      setCorrMatrix(matrixRes);
      setRegimeData(currentRegimeRes);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedAsset]);

  if (loading) {
    return <LoadingState message="Connecting to QUANTLAB Backend telemetry engines..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchDashboardData} />;
  }

  const latestRegimePoint =
    regimeData && regimeData.data.length > 0 ? regimeData.data[regimeData.data.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Platform Title Banner */}
      <div className="bg-[#0D111A] border border-[#1E293B] rounded-lg p-5 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400 font-mono font-bold">
            QL
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold font-mono text-white tracking-wide">
                QUANTLAB MARKET OVERVIEW
              </h1>
              <Badge variant="cyan" size="xs">Live Telemetry</Badge>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Quantitative Multi-Asset Financial Intelligence & Backtesting System
            </p>
          </div>
        </div>

        {/* Target Asset Selector */}
        <div className="flex items-center space-x-2 bg-[#121824] p-1.5 rounded-lg border border-[#1E293B]">
          <span className="text-[11px] font-mono text-slate-400 px-2 uppercase">Focus Asset:</span>
          <button
            onClick={() => setSelectedAsset('gold')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'gold'
                ? 'bg-amber-950/90 text-amber-300 border border-amber-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            GOLD
          </button>
          <button
            onClick={() => setSelectedAsset('bitcoin')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'bitcoin'
                ? 'bg-orange-950/90 text-orange-400 border border-orange-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            BTC
          </button>
          <button
            onClick={() => setSelectedAsset('nvidia')}
            className={`px-3 py-1 text-xs font-mono rounded transition-colors ${
              selectedAsset === 'nvidia'
                ? 'bg-lime-950/90 text-lime-400 border border-lime-700/60 font-semibold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NVDA
          </button>
        </div>
      </div>

      {/* Asset Scorecards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Gold Card */}
        <Card
          variant={selectedAsset === 'gold' ? 'default' : 'subpanel'}
          className={`cursor-pointer transition-all ${
            selectedAsset === 'gold' ? 'ring-1 ring-amber-500/50' : 'hover:border-slate-600'
          }`}
          onClick={() => setSelectedAsset('gold')}
        >
          <CardHeader className="py-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              <CardTitle>Gold Spot (GC=F)</CardTitle>
            </div>
            <Badge variant="gold" size="xs">Commodity</Badge>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-bold font-mono text-slate-100">
                ${goldSummary?.latest_close ? goldSummary.latest_close.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—'}
              </span>
              <span className="text-xs font-mono text-slate-400">
                {goldSummary?.records.toLocaleString()} records
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#1E293B]/70 text-center font-mono">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Ann. Vol</div>
                <div className="text-xs font-semibold text-slate-200">
                  {goldSummary?.annualized_volatility ? (goldSummary.annualized_volatility * 100).toFixed(2) + '%' : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Sharpe</div>
                <div className="text-xs font-semibold text-slate-200">
                  {goldSummary?.sharpe_ratio ? goldSummary.sharpe_ratio.toFixed(2) : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Max DD</div>
                <div className="text-xs font-semibold text-rose-400">
                  {goldSummary?.maximum_drawdown ? (goldSummary.maximum_drawdown * 100).toFixed(1) + '%' : '—'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bitcoin Card */}
        <Card
          variant={selectedAsset === 'bitcoin' ? 'default' : 'subpanel'}
          className={`cursor-pointer transition-all ${
            selectedAsset === 'bitcoin' ? 'ring-1 ring-orange-500/50' : 'hover:border-slate-600'
          }`}
          onClick={() => setSelectedAsset('bitcoin')}
        >
          <CardHeader className="py-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-orange-400"></span>
              <CardTitle>Bitcoin (BTC/USD)</CardTitle>
            </div>
            <Badge variant="btc" size="xs">2017 Dataset</Badge>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-bold font-mono text-slate-100">
                ${btcSummary?.latest_close ? btcSummary.latest_close.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—'}
              </span>
              <span className="text-xs font-mono text-slate-400">
                {btcSummary?.records.toLocaleString()} records
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#1E293B]/70 text-center font-mono">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Ann. Vol</div>
                <div className="text-xs font-semibold text-slate-200">
                  {btcSummary?.annualized_volatility ? (btcSummary.annualized_volatility * 100).toFixed(2) + '%' : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Sharpe</div>
                <div className="text-xs font-semibold text-slate-200">
                  {btcSummary?.sharpe_ratio ? btcSummary.sharpe_ratio.toFixed(2) : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Max DD</div>
                <div className="text-xs font-semibold text-rose-400">
                  {btcSummary?.maximum_drawdown ? (btcSummary.maximum_drawdown * 100).toFixed(1) + '%' : '—'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* NVIDIA Card */}
        <Card
          variant={selectedAsset === 'nvidia' ? 'default' : 'subpanel'}
          className={`cursor-pointer transition-all ${
            selectedAsset === 'nvidia' ? 'ring-1 ring-lime-500/50' : 'hover:border-slate-600'
          }`}
          onClick={() => setSelectedAsset('nvidia')}
        >
          <CardHeader className="py-2.5">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-lime-400"></span>
              <CardTitle>NVIDIA Corp (NVDA)</CardTitle>
            </div>
            <Badge variant="nvda" size="xs">Equities</Badge>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-bold font-mono text-slate-100">
                ${nvdaSummary?.latest_close ? nvdaSummary.latest_close.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—'}
              </span>
              <span className="text-xs font-mono text-slate-400">
                {nvdaSummary?.records.toLocaleString()} records
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[#1E293B]/70 text-center font-mono">
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Ann. Vol</div>
                <div className="text-xs font-semibold text-slate-200">
                  {nvdaSummary?.annualized_volatility ? (nvdaSummary.annualized_volatility * 100).toFixed(2) + '%' : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Sharpe</div>
                <div className="text-xs font-semibold text-slate-200">
                  {nvdaSummary?.sharpe_ratio ? nvdaSummary.sharpe_ratio.toFixed(2) : '—'}
                </div>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase">Max DD</div>
                <div className="text-xs font-semibold text-rose-400">
                  {nvdaSummary?.maximum_drawdown ? (nvdaSummary.maximum_drawdown * 100).toFixed(1) + '%' : '—'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Center Grid: Performance & Correlation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Chart (2 cols) */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Normalized Cumulative Growth Trajectory</CardTitle>
              <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                Compounded growth series across historical timelines (compounded from day 0)
              </p>
            </div>
            <NavLink to="/market-analysis">
              <button className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center space-x-1">
                <span>Detailed Analysis</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </NavLink>
          </CardHeader>
          <CardContent className="p-4">
            <PerformanceChart seriesData={perfSeries} height={320} />
          </CardContent>
        </Card>

        {/* Correlation Snapshot (1 col) */}
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Cross-Asset Correlation</CardTitle>
              <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                Full-sample Pearson matrix
              </p>
            </div>
            <NavLink to="/correlation">
              <button className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center space-x-1">
                <span>Correlation Lab</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </NavLink>
          </CardHeader>
          <CardContent className="p-4">
            {corrMatrix && (
              <CorrelationHeatmap
                assets={corrMatrix.assets}
                matrix={corrMatrix.matrix}
                observations={corrMatrix.observations}
                height={280}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Bottom Grid: Current Market Regime & Quick Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Regime Status Panel (2 cols) */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Gauge className="w-4 h-4 text-cyan-400" />
              <CardTitle>Current Regime State • {regimeData?.asset}</CardTitle>
            </div>
            <NavLink to="/market-regimes">
              <button className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center space-x-1">
                <span>Regime Visualizer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </NavLink>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            {latestRegimePoint ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-[#121824] border border-[#1E293B] p-3 rounded">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Primary Trend</div>
                  <div className="mt-1">
                    <Badge
                      variant={latestRegimePoint.regime === 'BULL' ? 'emerald' : 'rose'}
                      size="md"
                    >
                      {latestRegimePoint.regime || 'WARMUP'}
                    </Badge>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">
                    {latestRegimePoint.trend_window}d SMA: ${latestRegimePoint.trend_value?.toFixed(2) ?? '—'}
                  </div>
                </div>

                <div className="bg-[#121824] border border-[#1E293B] p-3 rounded">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Volatility State</div>
                  <div className="mt-1">
                    <Badge
                      variant={
                        latestRegimePoint.volatility_state === 'HIGH_VOLATILITY' ? 'amber' : 'cyan'
                      }
                      size="md"
                    >
                      {latestRegimePoint.volatility_state || 'WARMUP'}
                    </Badge>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">
                    Threshold: {latestRegimePoint.volatility_threshold ? (latestRegimePoint.volatility_threshold * 100).toFixed(1) + '%' : '—'}
                  </div>
                </div>

                <div className="bg-[#121824] border border-[#1E293B] p-3 rounded">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Rolling Volatility</div>
                  <div className="text-base font-bold font-mono text-slate-100 mt-1">
                    {latestRegimePoint.rolling_volatility ? (latestRegimePoint.rolling_volatility * 100).toFixed(2) + '%' : '—'}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">
                    {latestRegimePoint.volatility_window}d window
                  </div>
                </div>

                <div className="bg-[#121824] border border-[#1E293B] p-3 rounded">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Last Observation</div>
                  <div className="text-base font-bold font-mono text-slate-100 mt-1">
                    {latestRegimePoint.date}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">
                    Close: ${latestRegimePoint.close.toLocaleString()}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs font-mono text-slate-500">No regime data available.</p>
            )}

            {/* Quick regime stats summary */}
            {regimeData?.summary_statistics && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#1E293B] text-xs font-mono">
                <div className="text-slate-400">
                  <span className="text-slate-500 block text-[10px]">BULL DAYS</span>
                  <span className="text-emerald-400 font-bold">
                    {regimeData.summary_statistics.bull.observation_count} ({(regimeData.summary_statistics.bull.percentage * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-500 block text-[10px]">BEAR DAYS</span>
                  <span className="text-rose-400 font-bold">
                    {regimeData.summary_statistics.bear.observation_count} ({(regimeData.summary_statistics.bear.percentage * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-500 block text-[10px]">HIGH VOL DAYS</span>
                  <span className="text-amber-400 font-bold">
                    {regimeData.summary_statistics.high_volatility.observation_count} ({(regimeData.summary_statistics.high_volatility.percentage * 100).toFixed(1)}%)
                  </span>
                </div>
                <div className="text-slate-400">
                  <span className="text-slate-500 block text-[10px]">LOW VOL DAYS</span>
                  <span className="text-cyan-400 font-bold">
                    {regimeData.summary_statistics.low_volatility.observation_count} ({(regimeData.summary_statistics.low_volatility.percentage * 100).toFixed(1)}%)
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Launchpad Navigation */}
        <Card>
          <CardHeader>
            <CardTitle>Research Launchpad</CardTitle>
          </CardHeader>
          <CardContent className="p-3 space-y-2">
            <NavLink
              to="/portfolio"
              className="flex items-center justify-between p-2.5 rounded bg-[#121824] hover:bg-[#161F2E] border border-[#1E293B] text-xs font-mono text-slate-300 transition-colors group"
            >
              <div className="flex items-center space-x-2.5">
                <PieChart className="w-4 h-4 text-amber-400 group-hover:text-amber-300" />
                <span>Portfolio Analytics</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400" />
            </NavLink>

            <NavLink
              to="/strategy-builder"
              className="flex items-center justify-between p-2.5 rounded bg-[#121824] hover:bg-[#161F2E] border border-[#1E293B] text-xs font-mono text-slate-300 transition-colors group"
            >
              <div className="flex items-center space-x-2.5">
                <Activity className="w-4 h-4 text-cyan-400 group-hover:text-cyan-300" />
                <span>Strategy Signals</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400" />
            </NavLink>

            <NavLink
              to="/backtesting"
              className="flex items-center justify-between p-2.5 rounded bg-[#121824] hover:bg-[#161F2E] border border-[#1E293B] text-xs font-mono text-slate-300 transition-colors group"
            >
              <div className="flex items-center space-x-2.5">
                <PlayCircle className="w-4 h-4 text-emerald-400 group-hover:text-emerald-300" />
                <span>Backtest Simulator</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-emerald-400" />
            </NavLink>

            <NavLink
              to="/robustness"
              className="flex items-center justify-between p-2.5 rounded bg-[#121824] hover:bg-[#161F2E] border border-[#1E293B] text-xs font-mono text-slate-300 transition-colors group"
            >
              <div className="flex items-center space-x-2.5">
                <ShieldAlert className="w-4 h-4 text-amber-400 group-hover:text-amber-300" />
                <span>Robustness Lab</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-amber-400" />
            </NavLink>

            <NavLink
              to="/research-report"
              className="flex items-center justify-between p-2.5 rounded bg-[#121824] hover:bg-[#161F2E] border border-[#1E293B] text-xs font-mono text-slate-300 transition-colors group"
            >
              <div className="flex items-center space-x-2.5">
                <FileText className="w-4 h-4 text-purple-400 group-hover:text-purple-300" />
                <span>Research Teardown</span>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-purple-400" />
            </NavLink>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
