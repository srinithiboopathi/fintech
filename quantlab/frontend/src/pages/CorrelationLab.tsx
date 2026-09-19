import React, { useState, useEffect } from 'react';
import { PageContainer } from '../components/layout/PageContainer';
import { CorrelationHeatmap } from '../components/charts/CorrelationHeatmap';
import { RollingCorrelation } from '../components/charts/RollingCorrelation';
import { Card } from '../components/ui/Card';
import { Select } from '../components/ui/Select';
import { CorrelationApi } from '../services/correlationApi';
import { CorrelationMatrixData, RollingCorrelationPoint } from '../types';
import { GitCompare, Sparkles, TrendingUp, Info } from 'lucide-react';

export const CorrelationLab: React.FC = () => {
  const [matrixData, setMatrixData] = useState<CorrelationMatrixData | null>(null);
  const [rollingData, setRollingData] = useState<RollingCorrelationPoint[]>([]);
  const [assetA, setAssetA] = useState('BTC-USD');
  const [assetB, setAssetB] = useState('GC=F');
  const [window, setWindow] = useState(30);

  useEffect(() => {
    CorrelationApi.getMatrix().then(setMatrixData);
  }, []);

  useEffect(() => {
    CorrelationApi.getRollingCorrelation(assetA, assetB, window).then(setRollingData);
  }, [assetA, assetB, window]);

  const handleCellClick = (a: string, b: string) => {
    if (a !== b) {
      setAssetA(a);
      setAssetB(b);
    }
  };

  return (
    <PageContainer
      title="Cross-Asset Correlation & Decoupling Lab"
      subtitle="Examine macro structural relationships, statistical decoupling, and pair-trading cointegration"
    >
      <div className="space-y-6">
        {/* Heatmap Matrix */}
        <CorrelationHeatmap data={matrixData} onCellClick={handleCellClick} />

        {/* Rolling Correlation Controls */}
        <Card variant="glass" className="p-4 border border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-bold uppercase tracking-wider font-mono text-slate-200">
                Pair Correlation Time Series Controls
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Select
                value={assetA}
                onChange={(e) => setAssetA(e.target.value)}
                options={[
                  { value: 'BTC-USD', label: 'Bitcoin (BTC)' },
                  { value: 'NVDA', label: 'NVIDIA (NVDA)' },
                  { value: 'GC=F', label: 'Gold (GC=F)' },
                ]}
              />
              <span className="text-xs text-slate-500 font-mono">vs</span>
              <Select
                value={assetB}
                onChange={(e) => setAssetB(e.target.value)}
                options={[
                  { value: 'GC=F', label: 'Gold (GC=F)' },
                  { value: 'BTC-USD', label: 'Bitcoin (BTC)' },
                  { value: 'NVDA', label: 'NVIDIA (NVDA)' },
                ]}
              />
              <Select
                value={window.toString()}
                onChange={(e) => setWindow(Number(e.target.value))}
                options={[
                  { value: '30', label: '30-Day Rolling Window' },
                  { value: '60', label: '60-Day Rolling Window' },
                  { value: '90', label: '90-Day Rolling Window' },
                ]}
              />
            </div>
          </div>
        </Card>

        {/* Rolling Correlation Chart */}
        <RollingCorrelation
          series={rollingData}
          assetA={assetA}
          assetB={assetB}
          window={window}
          height={240}
        />

        {/* Quant Insights Banner */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card variant="glass" className="p-5 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs font-mono">
              <Sparkles className="w-4 h-4" /> Decoupling & Diversification Benefit
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Gold (GC=F) and Bitcoin (BTC) exhibit low long-term correlation (r ≈ 0.08), providing substantial diversification when combined in a risk-parity portfolio.
            </p>
          </Card>

          <Card variant="glass" className="p-5 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-bold text-xs font-mono">
              <Info className="w-4 h-4" /> Statistical Arbitrage / Pair Trading
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              NVIDIA and Bitcoin show moderate positive risk-on correlation (r ≈ 0.46) during high-liquidity market regimes, diverging during tech earnings cycles.
            </p>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};
