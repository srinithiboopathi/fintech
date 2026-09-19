import React from 'react';
import ReactECharts from 'echarts-for-react';

interface DrawdownChartProps {
  data: Array<{ date: string; drawdown: number | null }>;
  height?: number | string;
  title?: string;
}

export const DrawdownChart: React.FC<DrawdownChartProps> = ({
  data,
  height = 260,
  title = "Historical Drawdown",
}) => {
  const dates = data.map((d) => d.date);
  const drawdowns = data.map((d) => d.drawdown ?? 0);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      valueFormatter: (val: number) => `${(val * 100).toFixed(2)}%`,
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '10%',
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
        fillerColor: 'rgba(244, 63, 94, 0.15)',
        handleStyle: { color: '#F43F5E' },
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
      max: 0,
      axisLine: { show: false },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: (val: number) => `${(val * 100).toFixed(0)}%`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series: [
      {
        name: title,
        type: 'line',
        data: drawdowns,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#F43F5E' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(244, 63, 94, 0.1)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0.4)' },
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
