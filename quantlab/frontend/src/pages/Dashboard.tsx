import React, { useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { AssetCard } from '../components/market/AssetCard';
import { MetricCard } from '../components/market/MetricCard';
import { PriceChart } from '../components/charts/PriceChart';
import { EquityCurve } from '../components/charts/EquityCurve';
import { useMarketData } from '../hooks/useMarketData';
import { useBacktest } from '../hooks/useBacktest';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, ShieldAlert, Zap, PlaySquare, ArrowRight, Award, Activity } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { assets, selectedSymbol, setSelectedSymbol, historicalBars } = useMarketData();
  const { activeResult, runSimulation } = useBacktest();
  const navigate = useNavigate();

  useEffect(() => {
    // Run an initial demo backtest if none exists
    if (!activeResult && assets.length > 0) {
      runSimulation({
        strategy_id: 'sma_crossover',
        symbol: 'NVDA',
        parameters: { fast_period: 20, slow_period: 50 },
        initial_capital: 100000,
        position_sizing: 'percent_equity',
        position_size_value: 0.95,
        commission_bps: 5.0,
        slippage_pct: 0.001,
      });
    }
  }, [assets, activeResult, runSimulation]);

  return (
    <PageContainer
      title="Quantitative Command Center"
      subtitle="Institutional alpha metrics, live market feeds, and active strategy monitoring"
      actions={
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/market-analysis')}
            leftIcon={<Activity className="w-3.5 h-3.5" />}
          >
            Terminal View
          </Button>
          <Button
            variant="glow"
            size="sm"
            onClick={() => navigate('/backtesting')}
            leftIcon={<Zap className="w-3.5 h-3.5" />}
          >
            New Backtest
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Global Strategy KPI Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Sharpe Ratio (1Y)"
            value="2.34"
            subValue="Sortino: 3.12"
            change={12.4}
            icon={<Award className="w-4 h-4" />}
            tooltip="Risk-adjusted annualized excess return"
          />
          <MetricCard
            label="Annualized CAGR"
            value="+58.4%"
            subValue="Benchmark: +24.1%"
            change={34.3}
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <MetricCard
            label="Maximum Drawdown"
            value="-14.2%"
            subValue="Recovery: 18 Days"
            icon={<ShieldAlert className="w-4 h-4" />}
          />
          <MetricCard
            label="Execution Win Rate"
            value="68.5%"
            subValue="Profit Factor: 2.35"
            icon={<Zap className="w-4 h-4" />}
          />
        </div>

        {/* Live Multi-Asset Grid */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
              Live Core Assets & Regimes
            </h3>
            <span className="text-[11px] font-mono text-emerald-400">Click asset to inspect chart</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {assets.map((asset) => (
              <AssetCard
                key={asset.symbol}
                asset={asset}
                isSelected={asset.symbol === selectedSymbol}
                onClick={() => setSelectedSymbol(asset.symbol)}
              />
            ))}
          </div>
        </div>

        {/* Charts Split: Price Action + Active Strategy Equity Curve */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PriceChart
            bars={historicalBars}
            title={`${selectedSymbol} Price Matrix & Volume Profile`}
            height={320}
          />
          {activeResult ? (
            <EquityCurve
              data={activeResult.equity_curve}
              title={`Active Model: ${activeResult.strategy_name} (${activeResult.symbol})`}
              height={320}
            />
          ) : (
            <Card variant="glass" className="h-[320px] flex items-center justify-center text-slate-500 font-mono">
              Running live vectorized simulation...
            </Card>
          )}
        </div>

        {/* Action Widgets Bottom Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card
            variant="glass"
            className="p-5 cursor-pointer hover:border-emerald-400/50 group"
            onClick={() => navigate('/correlation-lab')}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase text-emerald-400 font-mono">Correlation Lab</span>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-sm font-semibold text-slate-200 mb-1">Cross-Asset Heatmap Matrix</p>
            <p className="text-xs text-slate-400">
              Analyze Pearson & Spearman decoupling between Gold, BTC, and NVDA.
            </p>
          </Card>

          <Card
            variant="glass"
            className="p-5 cursor-pointer hover:border-cyan-400/50 group"
            onClick={() => navigate('/robustness-lab')}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase text-cyan-400 font-mono">Robustness Lab</span>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-sm font-semibold text-slate-200 mb-1">Monte Carlo Stress Testing</p>
            <p className="text-xs text-slate-400">
              Execute 1,000 resampled simulations to evaluate tail risk distributions.
            </p>
          </Card>

          <Card
            variant="glass"
            className="p-5 cursor-pointer hover:border-purple-400/50 group"
            onClick={() => navigate('/research-report')}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase text-purple-400 font-mono">Research Report</span>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
            </div>
            <p className="text-sm font-semibold text-slate-200 mb-1">Institutional Tear Sheet</p>
            <p className="text-xs text-slate-400">
              Generate formatted PDF/HTML tear sheets for investment committees.
            </p>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};
