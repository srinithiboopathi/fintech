import React from 'react';
import ReactECharts from 'echarts-for-react';
import {
  EfficientFrontierPoint,
  RandomPortfolioPoint,
  OptimalPortfoliosContainer,
} from '../../types';

interface EfficientFrontierChartProps {
  efficientFrontier: EfficientFrontierPoint[];
  randomPortfolios: RandomPortfolioPoint[];
  optimalPortfolios: OptimalPortfoliosContainer;
  riskFreeRate?: number;
  height?: number | string;
}

export const EfficientFrontierChart: React.FC<EfficientFrontierChartProps> = ({
  efficientFrontier,
  randomPortfolios,
  optimalPortfolios,
  height = 520,
}) => {
  if (!efficientFrontier || efficientFrontier.length === 0) {
    return (
      <div className="flex items-center justify-center h-80 text-slate-500 font-mono text-xs">
        No optimization data available to plot
      </div>
    );
  }

  // Format random portfolio scatter points: [volatility%, return%, sharpe, weights]
  const randomScatterData = randomPortfolios.map((p) => [
    Number((p.volatility * 100).toFixed(2)),
    Number((p.expected_return * 100).toFixed(2)),
    Number(p.sharpe_ratio.toFixed(3)),
    p.weights,
  ]);

  // Format frontier points sorted by volatility
  const sortedFrontier = [...efficientFrontier].sort((a, b) => a.volatility - b.volatility);
  const frontierLineData = sortedFrontier.map((p) => [
    Number((p.volatility * 100).toFixed(2)),
    Number((p.expected_return * 100).toFixed(2)),
    Number(p.sharpe_ratio.toFixed(3)),
    p.weights,
  ]);

  // Format optimal portfolio markers
  const maxSharpe = optimalPortfolios.max_sharpe;
  const minVol = optimalPortfolios.min_volatility;
  const eqWeight = optimalPortfolios.equal_weight;
  const userPort = optimalPortfolios.user_portfolio;

  const maxSharpeData = maxSharpe
    ? [
        [
          Number((maxSharpe.volatility * 100).toFixed(2)),
          Number((maxSharpe.expected_return * 100).toFixed(2)),
          Number(maxSharpe.sharpe_ratio.toFixed(3)),
          maxSharpe.weights,
        ],
      ]
    : [];

  const minVolData = minVol
    ? [
        [
          Number((minVol.volatility * 100).toFixed(2)),
          Number((minVol.expected_return * 100).toFixed(2)),
          Number(minVol.sharpe_ratio.toFixed(3)),
          minVol.weights,
        ],
      ]
    : [];

  const eqWeightData = eqWeight
    ? [
        [
          Number((eqWeight.volatility * 100).toFixed(2)),
          Number((eqWeight.expected_return * 100).toFixed(2)),
          Number(eqWeight.sharpe_ratio.toFixed(3)),
          eqWeight.weights,
        ],
      ]
    : [];

  const userPortData = userPort
    ? [
        [
          Number((userPort.volatility * 100).toFixed(2)),
          Number((userPort.expected_return * 100).toFixed(2)),
          Number(userPort.sharpe_ratio.toFixed(3)),
          userPort.weights,
        ],
      ]
    : [];

  const formatTooltipWeights = (weights: Record<string, number> | undefined) => {
    if (!weights) return '';
    return Object.entries(weights)
      .map(
        ([asset, w]) =>
          `<span style="margin-right: 8px; color: #CBD5E1;">${asset}: <b style="color: #38BDF8;">${(
            w * 100
          ).toFixed(1)}%</b></span>`
      )
      .join('');
  };

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#0D111A',
      borderColor: '#1E293B',
      borderWidth: 1,
      padding: [10, 14],
      textStyle: {
        color: '#E2E8F0',
        fontFamily: 'monospace',
        fontSize: 11,
      },
      formatter: (params: any) => {
        const seriesName = params.seriesName;
        const [vol, ret, sharpe, weights] = params.value || [];
        const retColor = ret >= 0 ? '#10B981' : '#F43F5E';

        return `
          <div style="font-weight: 700; margin-bottom: 6px; color: #38BDF8; text-transform: uppercase; font-size: 11px;">
            ${seriesName}
          </div>
          <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 3px;">
            <span style="color: #94A3B8;">Expected Return:</span>
            <span style="font-weight: 700; color: ${retColor};">${ret >= 0 ? '+' : ''}${ret}%</span>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 3px;">
            <span style="color: #94A3B8;">Annualized Volatility:</span>
            <span style="font-weight: 700; color: #F59E0B;">${vol}%</span>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 20px; margin-bottom: 6px;">
            <span style="color: #94A3B8;">Sharpe Ratio:</span>
            <span style="font-weight: 700; color: #A855F7;">${sharpe}</span>
          </div>
          <div style="border-top: 1px solid #1E293B; padding-top: 6px; margin-top: 4px; font-size: 10px;">
            <div style="color: #64748B; margin-bottom: 2px;">Asset Allocation:</div>
            <div>${formatTooltipWeights(weights)}</div>
          </div>
        `;
      },
    },
    legend: {
      top: 4,
      right: 12,
      textStyle: {
        color: '#94A3B8',
        fontFamily: 'monospace',
        fontSize: 11,
      },
      itemGap: 14,
      data: [
        'Maximum Sharpe',
        'Minimum Volatility',
        'Equal Weight',
        ...(userPort ? ['User Portfolio'] : []),
        'Efficient Frontier',
        'Feasible Portfolios',
      ],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '6%',
      top: '12%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: 'Annualized Volatility (Risk %)',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: {
        color: '#94A3B8',
        fontFamily: 'monospace',
        fontSize: 11,
      },
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisTick: { lineStyle: { color: '#1E293B' } },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: '{value}%',
      },
      splitLine: {
        lineStyle: {
          color: '#1E293B',
          type: 'dashed',
          opacity: 0.6,
        },
      },
      scale: true,
    },
    yAxis: {
      type: 'value',
      name: 'Expected Annual Return (%)',
      nameLocation: 'middle',
      nameGap: 45,
      nameTextStyle: {
        color: '#94A3B8',
        fontFamily: 'monospace',
        fontSize: 11,
      },
      axisLine: { lineStyle: { color: '#1E293B' } },
      axisTick: { lineStyle: { color: '#1E293B' } },
      axisLabel: {
        color: '#64748B',
        fontFamily: 'monospace',
        fontSize: 10,
        formatter: '{value}%',
      },
      splitLine: {
        lineStyle: {
          color: '#1E293B',
          type: 'dashed',
          opacity: 0.6,
        },
      },
      scale: true,
    },
    series: [
      {
        name: 'Feasible Portfolios',
        type: 'scatter',
        data: randomScatterData,
        symbolSize: 4,
        itemStyle: {
          color: 'rgba(56, 189, 248, 0.22)',
        },
        large: true,
        z: 2,
      },
      {
        name: 'Efficient Frontier',
        type: 'line',
        data: frontierLineData,
        smooth: 0.3,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 3.5,
          color: '#06B6D4',
          shadowColor: 'rgba(6, 182, 212, 0.6)',
          shadowBlur: 8,
        },
        itemStyle: {
          color: '#06B6D4',
        },
        z: 10,
      },
      {
        name: 'Minimum Volatility',
        type: 'scatter',
        data: minVolData,
        symbol: 'circle',
        symbolSize: 15,
        itemStyle: {
          color: '#10B981',
          borderColor: '#FFFFFF',
          borderWidth: 2,
          shadowColor: '#10B981',
          shadowBlur: 10,
        },
        z: 20,
      },
      {
        name: 'Maximum Sharpe',
        type: 'scatter',
        data: maxSharpeData,
        symbol: 'diamond',
        symbolSize: 18,
        itemStyle: {
          color: '#38BDF8',
          borderColor: '#FFFFFF',
          borderWidth: 2,
          shadowColor: '#38BDF8',
          shadowBlur: 12,
        },
        z: 20,
      },
      {
        name: 'Equal Weight',
        type: 'scatter',
        data: eqWeightData,
        symbol: 'triangle',
        symbolSize: 15,
        itemStyle: {
          color: '#F59E0B',
          borderColor: '#FFFFFF',
          borderWidth: 2,
          shadowColor: '#F59E0B',
          shadowBlur: 10,
        },
        z: 20,
      },
      ...(userPort
        ? [
            {
              name: 'User Portfolio',
              type: 'scatter',
              data: userPortData,
              symbol: 'pin',
              symbolSize: 22,
              itemStyle: {
                color: '#A855F7',
                borderColor: '#FFFFFF',
                borderWidth: 2,
                shadowColor: '#A855F7',
                shadowBlur: 12,
              },
              z: 25,
            },
          ]
        : []),
    ],
  };

  return (
    <div className="w-full bg-[#0A0E17] border border-[#1E293B] rounded-lg p-3">
      <ReactECharts
        option={option}
        style={{ height, width: '100%' }}
        opts={{ renderer: 'canvas' }}
        notMerge={true}
      />
    </div>
  );
};
