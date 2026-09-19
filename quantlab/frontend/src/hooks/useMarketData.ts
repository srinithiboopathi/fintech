import { useEffect } from 'react';
import { useMarketStore } from '../store/marketStore';

export function useMarketData() {
  const {
    assets,
    selectedSymbol,
    selectedAsset,
    historicalBars,
    isLoading,
    loadAssets,
    setSelectedSymbol,
    loadHistoricalBars,
  } = useMarketStore();

  useEffect(() => {
    if (assets.length === 0) {
      loadAssets();
    }
  }, [assets.length, loadAssets]);

  useEffect(() => {
    if (selectedSymbol) {
      loadHistoricalBars(selectedSymbol);
    }
  }, [selectedSymbol, loadHistoricalBars]);

  return {
    assets,
    selectedSymbol,
    selectedAsset,
    historicalBars,
    isLoading,
    setSelectedSymbol,
    refreshBars: () => loadHistoricalBars(selectedSymbol),
  };
}
