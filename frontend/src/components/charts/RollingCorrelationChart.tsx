import React from 'react';
import ReactECharts from 'echarts-for-react';
import { RollingCorrelationPoint } from '../../types';

interface RollingCorrelationChartProps {
  data: RollingCorrelationPoint[];
  assetA: string;
  assetB: string;
  window: number;
  height?: number | string;
}

export const RollingCorrelationChart: React.FC<RollingCorrelationChartProps> = ({
  data,
  assetA,
  assetB,
  window,
  height = 300,
}) => {
  const dates = data.map((d) => d.date);
  const values = data.map((d) => d.correlation);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      valueFormatter: (val: number | null) =>
        val !== null && val !== undefined ? val.toFixed(4) : '—',
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '10%',
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
      min: -1,
      max: 1,
      axisLine: { show: false },
      axisLabel: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series: [
      {
        name: `${assetA} / ${assetB} (${window}d Rolling Correlation)`,
        type: 'line',
        data: values,
        showSymbol: false,
        smooth: true,
        lineStyle: { width: 2, color: '#38BDF8' },
        markLine: {
          silent: true,
          data: [{ yAxis: 0, lineStyle: { color: '#475569', type: 'dashed' } }],
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
