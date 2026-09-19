import React from 'react';
import ReactECharts from 'echarts-for-react';
import { EquityCurvePoint, TradeRecord } from '../../types';

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  trades?: TradeRecord[];
  strategyName: string;
  assetName: string;
  height?: number | string;
}

export const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  data,
  trades = [],
  strategyName,
  assetName,
  height = 420,
}) => {
  const dates = data.map((d) => d.date);
  const strategyEquity = data.map((d) => d.portfolio_value);
  const benchmarkEquity = data.map((d) => d.benchmark_value);

  // Map trades to entry/exit points on strategy equity curve
  const dateToValueMap = new Map(data.map((d) => [d.date, d.portfolio_value]));

  const entryMarkers = trades
    .filter((t) => dateToValueMap.has(t.entry_date))
    .map((t) => [t.entry_date, dateToValueMap.get(t.entry_date)]);

  const exitMarkers = trades
    .filter((t) => dateToValueMap.has(t.exit_date))
    .map((t) => [t.exit_date, dateToValueMap.get(t.exit_date)]);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      valueFormatter: (val: number | null) =>
        val !== null && val !== undefined ? `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—',
    },
    legend: {
      data: [`${strategyName} Equity`, `${assetName} Buy & Hold`, 'Trade Entry', 'Trade Exit'],
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
        formatter: (val: number) => `$${val.toLocaleString()}`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series: [
      {
        name: `${strategyName} Equity`,
        type: 'line',
        data: strategyEquity,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 2, color: '#06B6D4' },
        itemStyle: { color: '#06B6D4' },
      },
      {
        name: `${assetName} Buy & Hold`,
        type: 'line',
        data: benchmarkEquity,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#64748B', type: 'dashed' },
        itemStyle: { color: '#64748B' },
      },
      {
        name: 'Trade Entry',
        type: 'scatter',
        data: entryMarkers,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#10B981', borderColor: '#064E3B', borderWidth: 1.5 },
        z: 10,
      },
      {
        name: 'Trade Exit',
        type: 'scatter',
        data: exitMarkers,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#F43F5E', borderColor: '#881337', borderWidth: 1.5 },
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
