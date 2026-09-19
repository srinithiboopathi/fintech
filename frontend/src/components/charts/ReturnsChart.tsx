import React from 'react';
import ReactECharts from 'echarts-for-react';
import { ReturnDataPoint } from '../../types';

interface ReturnsChartProps {
  data: ReturnDataPoint[];
  mode?: 'daily' | 'cumulative';
  height?: number | string;
}

export const ReturnsChart: React.FC<ReturnsChartProps> = ({
  data,
  mode = 'daily',
  height = 320,
}) => {
  const dates = data.map((d) => d.date);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      valueFormatter: (val: number) =>
        val !== null && val !== undefined ? `${(val * 100).toFixed(2)}%` : '—',
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '8%',
      containLabel: true,
    },
    dataZoom: [
      { type: 'inside', start: 70, end: 100 },
      {
        type: 'slider',
        start: 70,
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
      axisLine: { show: false },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: (val: number) => `${(val * 100).toFixed(1)}%`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series: [
      mode === 'daily'
        ? {
            name: 'Daily Return',
            type: 'bar',
            data: data.map((d) => {
              const val = d.daily_return ?? 0;
              return {
                value: val,
                itemStyle: {
                  color: val >= 0 ? '#10B981' : '#F43F5E',
                },
              };
            }),
          }
        : {
            name: 'Cumulative Return',
            type: 'line',
            data: data.map((d) => d.cumulative_return ?? 0),
            showSymbol: false,
            smooth: true,
            lineStyle: { width: 1.5, color: '#06B6D4' },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(6, 182, 212, 0.3)' },
                  { offset: 1, color: 'rgba(6, 182, 212, 0.0)' },
                ],
              },
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
