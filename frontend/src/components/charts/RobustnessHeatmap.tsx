import React from 'react';
import ReactECharts from 'echarts-for-react';
import { RobustnessConfigResult } from '../../types';

interface RobustnessHeatmapProps {
  results: RobustnessConfigResult[];
  metric?: 'total_return' | 'sharpe_ratio' | 'maximum_drawdown';
  height?: number | string;
}

export const RobustnessHeatmap: React.FC<RobustnessHeatmapProps> = ({
  results,
  metric = 'total_return',
  height = 360,
}) => {
  if (!results || results.length === 0) return null;

  // Detect 2 parameter keys
  const firstParams = results[0]?.parameters || {};
  const paramKeys = Object.keys(firstParams);

  if (paramKeys.length < 2) {
    // 1D parameter list or no params
    const xLabels = results.map((r, i) => JSON.stringify(r.parameters) || `#${i + 1}`);
    const values = results.map((r) => r[metric]);

    const barOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0D111A',
        borderColor: '#1E293B',
        textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      },
      grid: { left: '3%', right: '3%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: xLabels,
        axisLine: { lineStyle: { color: '#1E293B' } },
        axisLabel: { color: '#64748B', fontFamily: 'monospace', fontSize: 10, rotate: 30 },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisLabel: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
        splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
      },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: {
            color: '#06B6D4',
          },
        },
      ],
    };

    return (
      <div className="w-full">
        <ReactECharts option={barOption} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
      </div>
    );
  }

  const [xKey, yKey] = paramKeys;
  const xValues = Array.from(new Set(results.map((r) => r.parameters[xKey]))).sort((a, b) => a - b);
  const yValues = Array.from(new Set(results.map((r) => r.parameters[yKey]))).sort((a, b) => a - b);

  const dataGrid: Array<[number, number, number]> = [];
  let minVal = Infinity;
  let maxVal = -Infinity;

  results.forEach((r) => {
    const xIdx = xValues.indexOf(r.parameters[xKey]);
    const yIdx = yValues.indexOf(r.parameters[yKey]);
    const val = r[metric];
    if (xIdx >= 0 && yIdx >= 0 && typeof val === 'number') {
      dataGrid.push([xIdx, yIdx, Number(val.toFixed(4))]);
      if (val < minVal) minVal = val;
      if (val > maxVal) maxVal = val;
    }
  });

  if (minVal === Infinity) {
    minVal = 0;
    maxVal = 1;
  }

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      position: 'top',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: any) => {
        const xV = xValues[params.value[0]];
        const yV = yValues[params.value[1]];
        const val = params.value[2];
        return `
          <div class="font-mono text-xs">
            <div class="text-cyan-400 font-semibold">${xKey}: ${xV} | ${yKey}: ${yV}</div>
            <div class="mt-1">${metric}: <span class="font-bold">${val}</span></div>
          </div>
        `;
      },
    },
    grid: { left: '10%', right: '10%', bottom: '18%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xValues.map((v) => `${xKey}: ${v}`),
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisLabel: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 10 },
    },
    yAxis: {
      type: 'category',
      data: yValues.map((v) => `${yKey}: ${v}`),
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisLabel: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 10 },
    },
    visualMap: {
      min: minVal,
      max: maxVal,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#1E293B', '#0284C7', '#10B981'],
      },
      textStyle: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
    },
    series: [
      {
        name: 'Parameter Sensitivity',
        type: 'heatmap',
        data: dataGrid,
        label: {
          show: true,
          color: '#F8FAFC',
          fontFamily: 'monospace',
          fontSize: 11,
          formatter: (p: any) => p.value[2].toFixed(3),
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
