import React from 'react';
import ReactECharts from 'echarts-for-react';

interface MultiAssetSeries {
  asset: string;
  data: Array<{ date: string; cumulative_return: number }>;
  color: string;
}

interface PerformanceChartProps {
  seriesData: MultiAssetSeries[];
  height?: number | string;
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  seriesData,
  height = 360,
}) => {
  // Collect all unique dates
  const allDates = Array.from(
    new Set(seriesData.flatMap((s) => s.data.map((d) => d.date)))
  ).sort();

  const series = seriesData.map((s) => {
    const map = new Map(s.data.map((d) => [d.date, d.cumulative_return]));
    const alignedValues = allDates.map((date) => map.get(date) ?? null);

    return {
      name: s.asset,
      type: 'line',
      data: alignedValues,
      showSymbol: false,
      smooth: true,
      lineStyle: { width: 2, color: s.color },
      itemStyle: { color: s.color },
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      textStyle: { color: '#E2E8F0', fontFamily: 'monospace', fontSize: 11 },
      valueFormatter: (val: number | null) =>
        val !== null ? `${(val * 100).toFixed(2)}%` : '—',
    },
    legend: {
      data: seriesData.map((s) => s.asset),
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
        start: 0,
        end: 100,
      },
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
      data: allDates,
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
        formatter: (val: number) => `${(val * 100).toFixed(0)}%`,
      },
      splitLine: { lineStyle: { color: '#1E293B', type: 'dashed' } },
    },
    series,
  };

  return (
    <div className="w-full">
      <ReactECharts option={option} style={{ height, width: '100%' }} notMerge={true} lazyUpdate={true} />
    </div>
  );
};
