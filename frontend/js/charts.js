/**
 * Quantexa — Chart.js Manager
 * Provides unified dark-theme styling, responsive canvases, and lifecycle management.
 */

class QuantexaChartManager {
  constructor() {
    this._instances = new Map();
    this._initChartDefaults();
  }

  _initChartDefaults() {
    if (typeof Chart === 'undefined') return;

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.9)';
    Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
    Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
  }

  destroy(canvasId) {
    if (this._instances.has(canvasId)) {
      this._instances.get(canvasId).destroy();
      this._instances.delete(canvasId);
    }
  }

  destroyAll() {
    for (const [id, chart] of this._instances.entries()) {
      chart.destroy();
    }
    this._instances.clear();
  }

  _getCanvas(canvasId) {
    const el = document.getElementById(canvasId);
    if (!el) return null;
    this.destroy(canvasId);
    return el.getContext('2d');
  }

  // 1. Price & Indicators Chart
  renderPriceChart(canvasId, { labels, prices, sma, ema, assetName }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const datasets = [
      {
        label: `${assetName} Close ($)`,
        data: prices,
        borderColor: '#38bdf8',
        backgroundColor: (context) => {
          const chart = context.chart;
          const { ctx, chartArea } = chart;
          if (!chartArea) return null;
          const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, 'rgba(56, 189, 248, 0.25)');
          gradient.addColorStop(1, 'rgba(56, 189, 248, 0.0)');
          return gradient;
        },
        fill: true,
        borderWidth: 2,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#38bdf8',
      }
    ];

    if (sma && sma.some(v => v !== null)) {
      datasets.push({
        label: 'SMA',
        data: sma,
        borderColor: '#f59e0b',
        borderWidth: 1.5,
        borderDash: [4, 4],
        fill: false,
        tension: 0.1,
        pointRadius: 0
      });
    }

    if (ema && ema.some(v => v !== null)) {
      datasets.push({
        label: 'EMA',
        data: ema,
        borderColor: '#a855f7',
        borderWidth: 1.5,
        borderDash: [2, 2],
        fill: false,
        tension: 0.1,
        pointRadius: 0
      });
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: { boxWidth: 12, usePointStyle: true }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: $${Number(ctx.parsed.y).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => `$${Number(v).toLocaleString()}`
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 2. Returns Chart (Bar with pos/neg coloring)
  renderReturnsChart(canvasId, { labels, returns }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const backgroundColors = returns.map(v => v >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)');
    const borderColors = returns.map(v => v >= 0 ? '#10b981' : '#f43f5e');

    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Daily Return (%)',
          data: returns,
          backgroundColor: backgroundColors,
          borderColor: borderColors,
          borderWidth: 1,
          borderRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Daily Return: ${ctx.parsed.y != null && !isNaN(ctx.parsed.y) ? (ctx.parsed.y >= 0 ? '+' : '') + Number(ctx.parsed.y).toFixed(2) + '%' : '--'}`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => `${v}%`
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 3. Volatility Chart
  renderVolatilityChart(canvasId, { labels, volatility, threshold }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const datasets = [{
      label: 'Rolling Volatility (%)',
      data: volatility,
      borderColor: '#f59e0b',
      backgroundColor: 'rgba(245, 158, 11, 0.1)',
      fill: true,
      borderWidth: 2,
      tension: 0.1,
      pointRadius: 0
    }];

    if (threshold !== null && threshold !== undefined) {
      datasets.push({
        label: `Threshold (${threshold.toFixed(2)}%)`,
        data: Array(labels.length).fill(threshold),
        borderColor: 'rgba(244, 63, 94, 0.8)',
        borderWidth: 1.5,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false
      });
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y != null && !isNaN(ctx.parsed.y) ? Number(ctx.parsed.y).toFixed(2) + '%' : '--'}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => `${v}%`
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 4. Maximum Drawdown Chart (Underwater chart)
  renderDrawdownChart(canvasId, { labels, drawdowns }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Drawdown (%)',
          data: drawdowns,
          borderColor: '#f43f5e',
          backgroundColor: (context) => {
            const chart = context.chart;
            const { ctx, chartArea } = chart;
            if (!chartArea) return null;
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, 'rgba(244, 63, 94, 0.05)');
            gradient.addColorStop(1, 'rgba(244, 63, 94, 0.35)');
            return gradient;
          },
          fill: true,
          borderWidth: 1.5,
          tension: 0.1,
          pointRadius: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Drawdown: ${ctx.parsed.y != null && !isNaN(ctx.parsed.y) ? Number(ctx.parsed.y).toFixed(2) + '%' : '--'}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => `${v}%`
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 5. Rolling Correlation Chart
  renderRollingCorrelationChart(canvasId, { labels, series, pairLabel, window }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: `${pairLabel} (${window}-day rolling)`,
            data: series,
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            fill: true,
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0
          },
          {
            label: 'Zero Baseline',
            data: Array(labels.length).fill(0),
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            borderDash: [4, 4],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y != null && !isNaN(ctx.parsed.y) ? Number(ctx.parsed.y).toFixed(3) : '--'}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            min: -1.0,
            max: 1.0,
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => v.toFixed(1)
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 6. Dual-line Equity Curve Chart (Strategy vs Buy & Hold)
  renderEquityCurveChart(canvasId, { labels, strategyValues, benchmarkValues, strategyName }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: `${strategyName} Strategy`,
            data: strategyValues,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0,
            fill: true
          },
          {
            label: 'Buy & Hold Benchmark',
            data: benchmarkValues,
            borderColor: '#94a3b8',
            borderWidth: 1.5,
            borderDash: [4, 4],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: true, position: 'top' },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: $${Number(ctx.parsed.y).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: { maxTicksLimit: 10, font: { family: "'JetBrains Mono', monospace", size: 10 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.04)' },
            ticks: {
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              callback: (v) => `$${Number(v).toLocaleString()}`
            }
          }
        }
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }

  // 7. Regime Distribution Donut Chart
  renderRegimeDistributionChart(canvasId, { labels, counts }) {
    const ctx = this._getCanvas(canvasId);
    if (!ctx) return;

    const colorPalette = [
      '#10b981', // Bullish Low Vol
      '#3b82f6', // Bullish High Vol
      '#f59e0b', // Bearish Low Vol
      '#f43f5e', // Bearish High Vol
      '#a855f7', // Sideways
      '#64748b'  // Unknown
    ];

    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data: counts,
          backgroundColor: colorPalette.slice(0, labels.length),
          borderColor: '#0f172a',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right',
            labels: { boxWidth: 12, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const total = counts.reduce((a, b) => a + b, 0) || 1;
                return ` ${ctx.label}: ${ctx.raw} bars (${((ctx.raw / total) * 100).toFixed(1)}%)`;
              }
            }
          }
        },
        cutout: '65%'
      }
    });

    this._instances.set(canvasId, chart);
    return chart;
  }
}

// Global chart manager singleton
window.quantexaCharts = new QuantexaChartManager();
