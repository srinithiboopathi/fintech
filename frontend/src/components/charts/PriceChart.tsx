import React from 'react';
import ReactECharts from 'echarts-for-react';
import { IndicatorDataPoint } from '../../types';

interface PriceChartProps {
  data: IndicatorDataPoint[];
  assetName: string;
  smaPeriod?: number;
  emaPeriod?: number;
  height?: number | string;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  data,
  assetName,
  smaPeriod = 20,
  emaPeriod = 20,
  height = 400,
}) => {
  const dates = data.map((d) => d.date);
  const closePrices = data.map((d) => d.close);
  const smaValues = data.map((d) => d.sma);
  const emaValues = data.map((d) => d.ema);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      axisPointer: { type: 'cross', lineStyle: { color: '#334155', type: 'dashed' } },
    },
    legend: {
      data: [`${assetName} Close`, `SMA (${smaPeriod})`, `EMA (${emaPeriod})`],
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
      {
        type: 'inside',
        start: 70,
        end: 100,
      },
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
      splitLine: { show: false },
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
        name: `${assetName} Close`,
        type: 'line',
        data: closePrices,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#06B6D4' },
        itemStyle: { color: '#06B6D4' },
      },
      {
        name: `SMA (${smaPeriod})`,
        type: 'line',
        data: smaValues,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: '#F59E0B', type: 'solid' },
        itemStyle: { color: '#F59E0B' },
      },
      {
        name: `EMA (${emaPeriod})`,
        type: 'line',
        data: emaValues,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.2, color: '#A855F7', type: 'dashed' },
        itemStyle: { color: '#A855F7' },
      },
    ],
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
