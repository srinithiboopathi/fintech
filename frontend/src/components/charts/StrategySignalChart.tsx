import React from 'react';
import ReactECharts from 'echarts-for-react';
import { StrategySignalPoint } from '../../types';

interface StrategySignalChartProps {
  data: StrategySignalPoint[];
  assetName: string;
  strategyName: string;
  height?: number | string;
}

export const StrategySignalChart: React.FC<StrategySignalChartProps> = ({
  data,
  assetName,
  strategyName,
  height = 420,
}) => {
  const dates = data.map((d) => d.date);
  const closePrices = data.map((d) => d.close);

  // Filter buy and sell points
  const buyPoints = data
    .filter((d) => d.signal === 1)
    .map((d) => [d.date, d.close]);

  const sellPoints = data
    .filter((d) => d.signal === -1)
    .map((d) => [d.date, d.close]);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
    },
    legend: {
      data: [`${assetName} Price (${strategyName})`, 'BUY Signal', 'SELL Signal'],
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
      scale: true,
      axisLine: { show: false },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: (val: number) => `$${val.toLocaleString()}`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series: [
      {
        name: `${assetName} Price (${strategyName})`,
        type: 'line',
        data: closePrices,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#06B6D4' },
      },
      {
        name: 'BUY Signal',
        type: 'scatter',
        data: buyPoints,
        symbol: 'triangle',
        symbolSize: 12,
        symbolRotate: 0,
        itemStyle: {
          color: '#10B981',
          borderColor: '#064E3B',
          borderWidth: 1.5,
        },
        z: 10,
      },
      {
        name: 'SELL Signal',
        type: 'scatter',
        data: sellPoints,
        symbol: 'triangle',
        symbolSize: 12,
        symbolRotate: 180,
        itemStyle: {
          color: '#F43F5E',
          borderColor: '#881337',
          borderWidth: 1.5,
        },
        z: 10,
      },
    ],
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
