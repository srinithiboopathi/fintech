import React from 'react';
import ReactECharts from 'echarts-for-react';

interface CorrelationHeatmapProps {
  assets: string[];
  matrix: Record<string, Record<string, number | null>>;
  observations?: number;
  height?: number | string;
}

export const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({
  assets,
  matrix,
  observations,
  height = 340,
}) => {
  // Convert matrix to [xIndex, yIndex, value] format
  const heatmapData: Array<[number, number, number]> = [];
  assets.forEach((assetY, yIdx) => {
    assets.forEach((assetX, xIdx) => {
      const val = matrix[assetY]?.[assetX];
      if (val !== undefined && val !== null) {
        heatmapData.push([xIdx, yIdx, Number(val.toFixed(4))]);
      }
    });
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      position: 'top',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: any) => {
        const xAsset = assets[params.value[0]];
        const yAsset = assets[params.value[1]];
        const corr = params.value[2];
        return `
          <div class="font-mono text-xs">
            <div class="text-cyan-400 font-semibold">${xAsset} × ${yAsset}</div>
            <div class="mt-1">Correlation: <span class="font-bold">${corr >= 0 ? '+' : ''}${corr.toFixed(4)}</span></div>
            ${observations ? `<div class="text-slate-400 text-[10px]">Observations: ${observations.toLocaleString()}</div>` : ''}
          </div>
        `;
      },
    },
    grid: {
      left: '12%',
      right: '12%',
      bottom: '15%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: assets,
      splitArea: { show: true, areaStyle: { color: ['transparent', 'rgba(18, 24, 36, 0.4)'] } },
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisLabel: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: assets,
      splitArea: { show: true, areaStyle: { color: ['transparent', 'rgba(18, 24, 36, 0.4)'] } },
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisLabel: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 11 },
    },
    visualMap: {
      min: -1,
      max: 1,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#F43F5E', '#1E293B', '#10B981'],
      },
      textStyle: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
    },
    series: [
      {
        name: 'Correlation Matrix',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          color: '#F8FAFC',
          fontFamily: 'monospace',
          fontSize: 12,
          fontWeight: 'bold',
          formatter: (p: any) => p.value[2].toFixed(2),
        },
        itemStyle: {
          borderColor: '#0D111A',
          borderWidth: 2,
        },
      },
    ],
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
