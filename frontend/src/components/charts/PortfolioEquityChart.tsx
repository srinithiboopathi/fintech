import React from 'react';
import ReactECharts from 'echarts-for-react';
import { PortfolioDataPoint } from '../../types';

interface PortfolioEquityChartProps {
  data: PortfolioDataPoint[];
  initialCapital?: number;
  height?: number | string;
}

export const PortfolioEquityChart: React.FC<PortfolioEquityChartProps> = ({
  data,
  initialCapital = 100000,
  height = 400,
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500 font-mono text-xs">
        No portfolio equity data available
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const values = data.map((d) => (isFinite(d.portfolio_value) ? d.portfolio_value : null));
  const cumReturns = data.map((d) => (isFinite(d.cumulative_return) ? d.cumulative_return : 0));

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      formatter: (params: any[]) => {
        if (!params || params.length === 0) return '';
        const index = params[0].dataIndex;
        const dateStr = dates[index];
        const val = values[index];
        const ret = cumReturns[index];
        const formattedVal =
          val !== null && val !== undefined
            ? `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : '—';
        const formattedRet = `${ret >= 0 ? '+' : ''}${(ret * 100).toFixed(2)}%`;
        const retColor = ret >= 0 ? '#10B981' : '#F43F5E';

        return `
          <div style="font-weight: 600; margin-bottom: 4px; color: #94A3B8;">${dateStr}</div>
          <div style="display: flex; justify-content: space-between; gap: 16px; margin-bottom: 2px;">
            <span style="color: #06B6D4;">Portfolio Value:</span>
            <span style="font-weight: 600;">${formattedVal}</span>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 16px;">
            <span style="color: #94A3B8;">Cumulative Return:</span>
            <span style="font-weight: 600; color: ${retColor};">${formattedRet}</span>
          </div>
        `;
      },
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '8%',
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
        name: 'Portfolio Equity',
        type: 'line',
        data: values,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 2.5, color: '#06B6D4' },
        itemStyle: { color: '#06B6D4' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(6, 182, 212, 0.25)' },
              { offset: 1, color: 'rgba(6, 182, 212, 0.0)' },
            ],
          },
        },
        markLine: {
          symbol: 'none',
          silent: true,
          data: [
            {
              yAxis: initialCapital,
              lineStyle: { color: '#64748B', type: 'dashed', width: 1 },
              label: {
                show: true,
                position: 'insideEndTop',
                formatter: `Inception: $${initialCapital.toLocaleString()}`,
                color: '#64748B',
                fontFamily: 'monospace',
                fontSize: 10,
              },
            },
          ],
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
