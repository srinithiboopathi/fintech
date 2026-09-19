import { useEffect } from 'react';
import { useBacktestStore } from '../store/backtestStore';

export function useBacktest() {
  const {
    strategies,
    selectedStrategyId,
    activeResult,
    isRunning,
    history,
    loadStrategies,
    setSelectedStrategyId,
    runSimulation,
  } = useBacktestStore();

  useEffect(() => {
    if (strategies.length === 0) {
      loadStrategies();
    }
  }, [strategies.length, loadStrategies]);

  const selectedStrategy = strategies.find((s) => s.id === selectedStrategyId) || strategies[0];

  return {
    strategies,
    selectedStrategyId,
    selectedStrategy,
    activeResult,
    isRunning,
    history,
    setSelectedStrategyId,
    runSimulation,
  };
}
