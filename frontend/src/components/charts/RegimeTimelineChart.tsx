import React from 'react';
import ReactECharts from 'echarts-for-react';
import { RegimeDataPoint } from '../../types';

interface RegimeTimelineChartProps {
  data: RegimeDataPoint[];
  assetName: string;
  height?: number | string;
}

export const RegimeTimelineChart: React.FC<RegimeTimelineChartProps> = ({
  data,
  assetName,
  height = 420,
}) => {
  const dates = data.map((d) => d.date);
  const closePrices = data.map((d) => d.close);
  const trendValues = data.map((d) => d.trend_value);
  const rollingVols = data.map((d) => (d.rolling_volatility !== null ? Number((d.rolling_volatility * 100).toFixed(2)) : null));
  const thresholds = data.map((d) => (d.volatility_threshold !== null ? Number((d.volatility_threshold * 100).toFixed(2)) : null));

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: any) => {
        const date = params[0]?.axisValue;
        const item = data.find((d) => d.date === date);
        if (!item) return '';

        const regimeColor = item.regime === 'BULL' ? '#10B981' : item.regime === 'BEAR' ? '#F43F5E' : '#94A3B8';
        const volColor = item.volatility_state === 'HIGH_VOLATILITY' ? '#F59E0B' : item.volatility_state === 'LOW_VOLATILITY' ? '#06B6D4' : '#94A3B8';

        return `
          <div class="font-mono text-xs p-1">
            <div class="font-bold text-slate-200 border-b border-[#1E293B] pb-1 mb-1.5">${date} (${assetName})</div>
            <div class="flex justify-between gap-4"><span>Close:</span> <span class="font-bold text-slate-100">$${item.close.toLocaleString()}</span></div>
            <div class="flex justify-between gap-4"><span>Trend (${item.trend_window}d):</span> <span class="text-slate-300">${item.trend_value !== null ? '$' + item.trend_value.toFixed(2) : '—'}</span></div>
            <div class="flex justify-between gap-4 mt-1 border-t border-[#1E293B]/60 pt-1"><span>Trend Regime:</span> <span class="font-bold" style="color:${regimeColor}">${item.regime || 'WARMUP'}</span></div>
            <div class="flex justify-between gap-4"><span>Vol State (${item.volatility_window}d):</span> <span class="font-bold" style="color:${volColor}">${item.volatility_state || 'WARMUP'}</span></div>
            <div class="flex justify-between gap-4 text-[10px] text-slate-400"><span>Rolling Vol:</span> <span>${item.rolling_volatility !== null ? (item.rolling_volatility * 100).toFixed(2) + '%' : '—'}</span></div>
            <div class="flex justify-between gap-4 text-[10px] text-slate-400"><span>Threshold:</span> <span>${item.volatility_threshold !== null ? (item.volatility_threshold * 100).toFixed(2) + '%' : '—'}</span></div>
          </div>
        `;
      },
    },
    legend: {
      data: [`${assetName} Price`, 'Trend SMA', 'Rolling Volatility (%)', 'Vol Threshold (%)'],
      textStyle: { color: '#94A3B8', fontFamily: 'monospace', fontSize: 11 },
      top: 0,
      right: 10,
    },
    grid: [
      { left: '3%', right: '3%', top: '12%', height: '50%', containLabel: true },
      { left: '3%', right: '3%', top: '68%', height: '20%', containLabel: true },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 70,
        end: 100,
        backgroundColor: '#0A0E17',
        borderColor: '#1E293B',
        fillerColor: 'rgba(6, 182, 212, 0.15)',
        handleStyle: { color: '#06B6D4' },
        textStyle: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
        bottom: 0,
        height: 18,
      },
    ],
    xAxis: [
      {
        gridIndex: 0,
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#1E293B' } },
        axisLabel: { show: false },
      },
      {
        gridIndex: 1,
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#1E293B' } },
        axisLabel: { color: '#64748B', fontFamily: 'monospace', fontSize: 10 },
      },
    ],
    yAxis: [
      {
        gridIndex: 0,
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
      {
        gridIndex: 1,
        type: 'value',
        scale: true,
        axisLine: { show: false },
        axisLabel: {
          color: '#64748B',
          fontFamily: 'monospace',
          fontSize: 10,
          formatter: (val: number) => `${val}%`,
        },
        splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
      },
    ],
    series: [
      {
        gridIndex: 0,
        name: `${assetName} Price`,
        type: 'line',
        data: closePrices,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 2, color: '#38BDF8' },
      },
      {
        gridIndex: 0,
        name: 'Trend SMA',
        type: 'line',
        data: trendValues,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#F59E0B', type: 'dashed' },
      },
      {
        gridIndex: 1,
        xAxisIndex: 1,
        yAxisIndex: 1,
        name: 'Rolling Volatility (%)',
        type: 'line',
        data: rollingVols,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#EC4899' },
      },
      {
        gridIndex: 1,
        xAxisIndex: 1,
        yAxisIndex: 1,
        name: 'Vol Threshold (%)',
        type: 'line',
        data: thresholds,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1.2, color: '#EAB308', type: 'dotted' },
      },
    ],
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
