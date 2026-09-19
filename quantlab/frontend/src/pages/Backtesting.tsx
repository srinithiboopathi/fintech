import React from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { StrategySelector } from '../components/backtest/StrategySelector';
import { BacktestForm } from '../components/backtest/BacktestForm';
import { BacktestSummary } from '../components/backtest/BacktestSummary';
import { TradeTable } from '../components/backtest/TradeTable';
import { EquityCurve } from '../components/charts/EquityCurve';
import { DrawdownChart } from '../components/charts/DrawdownChart';
import { useBacktest } from '../hooks/useBacktest';
import { useMarketData } from '../hooks/useMarketData';

export const Backtesting: React.FC = () => {
  const {
    strategies,
    selectedStrategyId,
    selectedStrategy,
    activeResult,
    isRunning,
    setSelectedStrategyId,
    runSimulation,
  } = useBacktest();

  const { assets, selectedSymbol, setSelectedSymbol } = useMarketData();

  return (
    <PageContainer
      title="Systematic Strategy Backtesting Engine"
      subtitle="Event-driven simulation with realistic commission schedules, slippage modeling, and equity tear sheets"
    >
      <div className="space-y-6">
        {/* Strategy Paradigm Selector */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-3">
            1. Select Strategy Model
          </h3>
          <StrategySelector
            strategies={strategies}
            selectedId={selectedStrategyId}
            onSelect={setSelectedStrategyId}
          />
        </div>

        {/* Backtest Configuration Form */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-3">
            2. Configure Capital & Execution Friction
          </h3>
          <BacktestForm
            strategy={selectedStrategy}
            assets={assets}
            selectedSymbol={selectedSymbol}
            onSymbolChange={setSelectedSymbol}
            onSubmit={runSimulation}
            isRunning={isRunning}
          />
        </div>

        {/* Results Tear Sheet */}
        {activeResult && (
          <div className="space-y-6 pt-4 border-t border-slate-800">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
              3. Performance Tear Sheet: {activeResult.strategy_name} ({activeResult.symbol})
            </h3>

            {/* KPI Summary Cards */}
            <BacktestSummary result={activeResult} />

            {/* Charts: Equity Curve & Underwater Drawdown */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <EquityCurve data={activeResult.equity_curve} height={300} />
              <DrawdownChart data={activeResult.equity_curve} height={300} />
            </div>

            {/* Execution Audit Log Table */}
            <TradeTable trades={activeResult.trades} />
          </div>
        )}
      </div>
    </PageContainer>
  );
};
