import React, { useState, useEffect } from 'react';
import { StrategyInfo, BacktestRequest, AssetOverview } from '../../types';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Card } from '../ui/Card';
import { Play, RotateCcw } from 'lucide-react';

interface BacktestFormProps {
  strategy: StrategyInfo;
  assets: AssetOverview[];
  selectedSymbol: string;
  onSymbolChange: (sym: string) => void;
  onSubmit: (req: BacktestRequest) => void;
  isRunning: boolean;
}

export const BacktestForm: React.FC<BacktestFormProps> = ({
  strategy,
  assets,
  selectedSymbol,
  onSymbolChange,
  onSubmit,
  isRunning,
}) => {
  const [params, setParams] = useState<Record<string, any>>({});
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [positionSizing, setPositionSizing] = useState<string>('percent_equity');
  const [positionSizeValue, setPositionSizeValue] = useState<number>(0.95);
  const [commissionBps, setCommissionBps] = useState<number>(5.0);
  const [slippagePct, setSlippagePct] = useState<number>(0.001);
  const [startDate, setStartDate] = useState<string>('2021-01-04');
  const [endDate, setEndDate] = useState<string>('2024-09-02');

  useEffect(() => {
    if (strategy && strategy.parameters) {
      const initialP: Record<string, any> = {};
      Object.entries(strategy.parameters).forEach(([key, def]) => {
        initialP[key] = def.default;
      });
      setParams(initialP);
    }
  }, [strategy]);

  const handleParamChange = (key: string, val: string, type: 'int' | 'float') => {
    const num = type === 'int' ? parseInt(val, 10) : parseFloat(val);
    setParams((prev) => ({ ...prev, [key]: isNaN(num) ? 0 : num }));
  };

  const handleRun = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      strategy_id: strategy.id,
      symbol: selectedSymbol,
      parameters: params,
      initial_capital: Number(initialCapital),
      position_sizing: positionSizing,
      position_size_value: Number(positionSizeValue),
      commission_bps: Number(commissionBps),
      slippage_pct: Number(slippagePct),
      start_date: startDate,
      end_date: endDate,
    });
  };

  return (
    <form onSubmit={handleRun} className="space-y-4">
      <Card variant="glass" className="border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2 font-mono">
            Backtest Execution Parameters
          </h3>
          <span className="text-xs text-emerald-400 font-mono font-semibold">
            {strategy?.name || 'Selected Strategy'}
          </span>
        </div>

        {/* Global Strategy Parameters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Select
            label="Target Asset"
            value={selectedSymbol}
            onChange={(e) => onSymbolChange(e.target.value)}
            options={assets.map((a) => ({ value: a.symbol, label: `${a.symbol} (${a.name})` }))}
          />
          <Input
            label="Initial Capital ($)"
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
          />
          <Input
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <Input
            label="End Date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        {/* Dynamic Strategy Specific Parameters */}
        <div className="pt-2 border-t border-slate-800/80">
          <div className="text-xs font-semibold text-slate-400 mb-3 font-mono">
            Strategy Mathematical Tuners
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {strategy?.parameters &&
              Object.entries(strategy.parameters).map(([key, def]) => (
                <div key={key}>
                  <Input
                    label={`${def.label} (${def.min}-${def.max})`}
                    type="number"
                    step={def.type === 'float' ? '0.01' : '1'}
                    min={def.min}
                    max={def.max}
                    value={params[key] ?? def.default}
                    onChange={(e) => handleParamChange(key, e.target.value, def.type)}
                  />
                </div>
              ))}
          </div>
        </div>

        {/* Execution Friction Controls */}
        <div className="pt-2 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Input
            label="Commission (Basis Points)"
            type="number"
            step="0.5"
            value={commissionBps}
            onChange={(e) => setCommissionBps(Number(e.target.value))}
          />
          <Input
            label="Slippage Rate (e.g. 0.001 = 0.1%)"
            type="number"
            step="0.0005"
            value={slippagePct}
            onChange={(e) => setSlippagePct(Number(e.target.value))}
          />
          <Select
            label="Position Sizing Mode"
            value={positionSizing}
            onChange={(e) => setPositionSizing(e.target.value)}
            options={[
              { value: 'percent_equity', label: '95% Portfolio Net Equity' },
              { value: 'volatility_parity', label: 'Volatility Parity Par' },
              { value: 'fixed_amount', label: 'Fixed Capital ($)' },
            ]}
          />
        </div>

        {/* Submit Actions */}
        <div className="pt-3 flex items-center justify-end gap-3 border-t border-slate-800/80">
          <Button
            type="submit"
            variant="glow"
            isLoading={isRunning}
            leftIcon={<Play className="w-4 h-4 fill-current" />}
            className="w-full sm:w-auto px-6 py-2.5 font-bold"
          >
            {isRunning ? 'Simulating Bar-by-Bar...' : 'Execute Backtest Engine'}
          </Button>
        </div>
      </Card>
    </form>
  );
};
