import React from 'react';
import ReactECharts from 'echarts-for-react';
import { PortfolioComparisonPoint } from '../../types';

interface PortfolioComparisonChartProps {
  data: PortfolioComparisonPoint[];
  height?: number | string;
}

const ASSET_COLORS: Record<string, string> = {
  Gold: '#F59E0B',
  Bitcoin: '#F97316',
  NVIDIA: '#10B981',
};

export const PortfolioComparisonChart: React.FC<PortfolioComparisonChartProps> = ({
  data,
  height = 400,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 font-mono text-xs">
        No comparison data available
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const portfolioValues = data.map((d) => (isFinite(d.portfolio) ? d.portfolio : null));

  // Determine active assets
  const sampleAssets = data[0]?.assets || {};
  const activeAssetNames = Object.keys(sampleAssets);

  const series: any[] = [
    {
      name: 'Portfolio',
      type: 'line',
      data: portfolioValues,
      smooth: false,
      showSymbol: false,
      lineStyle: { width: 3, color: '#06B6D4' },
      itemStyle: { color: '#06B6D4' },
      z: 5,
    },
  ];

  activeAssetNames.forEach((assetName) => {
    const assetColor = ASSET_COLORS[assetName] || '#A855F7';
    const values = data.map((d) => (d.assets && isFinite(d.assets[assetName]) ? d.assets[assetName] : null));

    series.push({
      name: assetName,
      type: 'line',
      data: values,
      smooth: false,
      showSymbol: false,
      lineStyle: { width: 1.8, color: assetColor, type: 'solid' },
      itemStyle: { color: assetColor },
      z: 3,
    });
  });

  const legendNames = ['Portfolio', ...activeAssetNames];

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: any[]) => {
        if (!params || params.length === 0) return '';
        const dateStr = params[0].axisValue;
        let html = `<div style="font-weight: 600; margin-bottom: 6px; color: #94A3B8;">${dateStr} (Base = 100)</div>`;

        params.forEach((p) => {
          const val = p.value;
          const formattedVal = val !== null && val !== undefined ? Number(val).toFixed(2) : '—';
          const returnFromBase = val !== null && val !== undefined ? `${val >= 100 ? '+' : ''}${(val - 100).toFixed(2)}%` : '—';
          const retColor = val >= 100 ? '#10B981' : '#F43F5E';

          html += `
            <div style="display: flex; justify-content: space-between; gap: 16px; margin-bottom: 2px;">
              <span style="display: flex; align-items: center; gap: 6px;">
                <span style="width: 8px; height: 8px; border-radius: 50%; background-color: ${p.color}; display: inline-block;"></span>
                <span>${p.seriesName}:</span>
              </span>
              <span style="font-weight: 600;">${formattedVal} <span style="color: ${retColor}; font-size: 10px;">(${returnFromBase})</span></span>
            </div>
          `;
        });

        return html;
      },
    },
    legend: {
      data: legendNames,
      textStyle: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 11 },
      top: 0,
      right: 10,
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '12%',
      containLabel: true,
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      {
        type: 'slider',
        start: 0,
        end: 100,
        backgroundColor: '#0A0E17',
        borderColor: '#1E293B',
        fillerColor: 'rgba(6, 182, 212, 0.15)',
        handleStyle: { color: '#06B6D4' },
        textStyle: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
        bottom: 5,
        height: 20,
      },
    ],
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisLabel: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { show: false },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: (val: number) => `${val.toFixed(0)}`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series,
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
