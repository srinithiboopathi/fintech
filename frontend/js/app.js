/**
 * Quantexa — Main Application Controller & View Router
 */

const ASSETS = {
  nvidia: {
    name: 'NVIDIA Corporation',
    symbol: 'NVDA',
    assetClass: 'Equity',
    color: '#10b981',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  },
  bitcoin: {
    name: 'Bitcoin',
    symbol: 'BTC/USD',
    assetClass: 'Cryptocurrency',
    color: '#f59e0b',
    badgeClass: 'bg-amber-500/10 text-amber-400 border-amber-500/20'
  },
  gold: {
    name: 'Gold Bullion',
    symbol: 'XAU/USD',
    assetClass: 'Commodity',
    color: '#eab308',
    badgeClass: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
  }
};

class QuantexaApp {
  constructor() {
    this.activeAsset = 'nvidia';
    this.activeView = 'overview';
    this.api = window.quantexaApi;
    this.charts = window.quantexaCharts;
    this.conversationId = null;
    this.isAiSending = false;
    this.lastUserMessage = '';
    this.state = {
      overviewData: null,
      marketData: null,
      correlationData: null,
      regimesData: null,
      backtestResult: null,
      comparisonResult: null,
      robustnessResult: null
    };
  }

  init() {
    this._bindEvents();
    this.checkHealth();
    this.switchView('overview');
    this.loadAssetData(this.activeAsset);
  }

  _bindEvents() {
    // Nav Links
    document.querySelectorAll('.nav-link').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        if (view) this.switchView(view);
      });
    });

    // Asset Pills
    document.querySelectorAll('.asset-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const asset = e.currentTarget.dataset.asset;
        if (asset) this.selectAsset(asset);
      });
    });

    // Refresh Button
    const refreshBtn = document.getElementById('btn-global-refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshAll());
    }

    // AI Chat Launcher & Drawer Triggers
    const floatingAiBtn = document.getElementById('btn-floating-ai');
    if (floatingAiBtn) {
      floatingAiBtn.addEventListener('click', () => this.openAiChat());
    }

    const topbarAiBtn = document.getElementById('btn-topbar-ai');
    if (topbarAiBtn) {
      topbarAiBtn.addEventListener('click', () => this.openAiChat());
    }

    const closeAiBtn = document.getElementById('btn-close-ai-drawer');
    const aiDrawerOverlay = document.getElementById('ai-drawer-overlay');
    if (closeAiBtn) {
      closeAiBtn.addEventListener('click', () => this.closeAiChat());
    }
    if (aiDrawerOverlay) {
      aiDrawerOverlay.addEventListener('click', () => this.closeAiChat());
    }

    const drawerClearBtn = document.getElementById('btn-drawer-clear-chat');
    if (drawerClearBtn) {
      drawerClearBtn.addEventListener('click', () => this.clearChat());
    }

    // Drawer Form Send
    const drawerSendBtn = document.getElementById('btn-drawer-ai-send') || document.getElementById('btn-ai-send');
    const drawerInput = document.getElementById('drawer-ai-chat-input') || document.getElementById('ai-chat-input');
    if (drawerSendBtn && drawerInput) {
      drawerSendBtn.addEventListener('click', () => {
        this.sendChatMessage(drawerInput.value, 'drawer');
      });
      drawerInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendChatMessage(drawerInput.value, 'drawer');
        }
      });
    }

    // Page Studio Form Send
    const pageSendBtn = document.getElementById('btn-page-ai-send');
    const pageInput = document.getElementById('page-ai-chat-input');
    if (pageSendBtn && pageInput) {
      pageSendBtn.addEventListener('click', () => {
        this.sendChatMessage(pageInput.value, 'page');
      });
      pageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendChatMessage(pageInput.value, 'page');
        }
      });
    }

    // Suggested Prompt Chips
    document.querySelectorAll('.suggested-prompt-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const prompt = e.currentTarget.dataset.prompt || e.currentTarget.textContent.trim();
        if (prompt) {
          const drawer = document.getElementById('ai-chat-drawer');
          const isDrawerOpen = drawer && !drawer.classList.contains('translate-x-full');
          if (this.activeView !== 'ai' && !isDrawerOpen) {
            this.openAiChat(prompt);
          } else {
            this.sendChatMessage(prompt, this.activeView === 'ai' ? 'page' : 'drawer');
          }
        }
      });
    });

    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('btn-mobile-menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');

    if (mobileMenuBtn && sidebar && overlay) {
      mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('-translate-x-full');
        overlay.classList.toggle('hidden');
      });
      overlay.addEventListener('click', () => {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
      });
    }
  }

  // View Navigation
  switchView(viewId) {
    this.activeView = viewId;

    // Update Nav Link Active States
    document.querySelectorAll('.nav-link').forEach(link => {
      if (link.dataset.view === viewId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });

    // Toggle View Sections
    document.querySelectorAll('.view-section').forEach(sec => {
      if (sec.id === `view-${viewId}`) {
        sec.classList.remove('hidden');
      } else {
        sec.classList.add('hidden');
      }
    });

    // Close mobile sidebar if open
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('mobile-overlay');
    if (sidebar && !sidebar.classList.contains('-translate-x-full') && window.innerWidth < 1024) {
      sidebar.classList.add('-translate-x-full');
      if (overlay) overlay.classList.add('hidden');
    }

    // Load Data for active view
    this.renderCurrentView();
  }

  selectAsset(assetId) {
    if (this.activeAsset === assetId) return;
    this.activeAsset = assetId;

    // Update pill styles
    document.querySelectorAll('.asset-pill').forEach(pill => {
      if (pill.dataset.asset === assetId) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    // Update selected asset label in topbar
    const label = document.getElementById('topbar-asset-label');
    if (label) label.innerText = ASSETS[assetId].symbol;

    this.loadAssetData(assetId);
  }

  async loadAssetData(assetId) {
    this.renderCurrentView();
  }

  async refreshAll() {
    const icon = document.getElementById('global-refresh-icon');
    if (icon) icon.classList.add('animate-spin');

    this.api.clearCache();
    await this.checkHealth();
    await this.renderCurrentView(true);

    if (icon) icon.classList.remove('animate-spin');
    this.showToast('Data Refreshed', 'Successfully synchronized latest financial data.');
  }

  async checkHealth() {
    try {
      const health = await this.api.getHealth();
      const statusPill = document.getElementById('backend-status-pill');
      const statusText = document.getElementById('backend-status-text');
      if (health.status === 'healthy') {
        if (statusPill) statusPill.className = 'flex items-center gap-2 px-3 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400';
        if (statusText) statusText.innerText = `Online (${health.active_provider || 'Twelve Data'})`;
      }
    } catch (e) {
      const statusPill = document.getElementById('backend-status-pill');
      const statusText = document.getElementById('backend-status-text');
      if (statusPill) statusPill.className = 'flex items-center gap-2 px-3 py-1 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400';
      if (statusText) statusText.innerText = 'Backend Offline';
    }
  }

  renderCurrentView(forceRefresh = false) {
    switch (this.activeView) {
      case 'overview':
        return this.loadOverview(forceRefresh);
      case 'market':
        return this.loadMarketAnalysis(forceRefresh);
      case 'indicators':
        return this.loadIndicators(forceRefresh);
      case 'risk':
        return this.loadRiskMetrics(forceRefresh);
      case 'correlation':
        return this.loadCorrelation(forceRefresh);
      case 'strategies':
        return this.loadStrategies(forceRefresh);
      case 'backtest':
        return this.loadBacktest(forceRefresh);
      case 'comparison':
        return this.loadComparison(forceRefresh);
      case 'robustness':
        return this.loadRobustness(forceRefresh);
      case 'regimes':
        return this.loadRegimes(forceRefresh);
      case 'system':
        return this.loadSystemStatus(forceRefresh);
    }
  }

  // ==========================================
  // VIEW 1: OVERVIEW HUD
  // ==========================================
  async loadOverview(refresh = false) {
    const asset = this.activeAsset;
    this._showSkeleton('overview-kpi-container');

    try {
      // Parallel fetch of latest, risk-analysis, regimes summary
      const [latest, risk, regimesSummary, summary] = await Promise.all([
        this.api.getLatest(asset, refresh),
        this.api.getRiskAnalysis(asset, 0.0, 252, refresh),
        this.api.getMarketRegimesSummary(asset, 50, 20, null, 0.0, refresh),
        this.api.getDataSummary(asset, refresh)
      ]);

      // Update Ticker Strip for all 3 assets
      this._updateTickerCards();

      // Render Hero Card
      document.getElementById('overview-hero-name').innerText = latest.asset || ASSETS[asset].name;
      document.getElementById('overview-hero-symbol').innerText = latest.symbol || ASSETS[asset].symbol;
      document.getElementById('overview-hero-price').innerText = this._formatCurrency(latest.price);
      document.getElementById('overview-hero-timestamp').innerText = `UTC Timestamp: ${latest.timestamp || '--'}`;

      const changeEl = document.getElementById('overview-hero-change');
      if (latest.change !== null && latest.change !== undefined) {
        const isPos = latest.change >= 0;
        changeEl.innerText = `${isPos ? '+' : ''}${this._formatCurrency(latest.change)} (${latest.change_percent || '--'})`;
        changeEl.className = `text-xs font-mono font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;
      } else {
        changeEl.innerText = 'Spot Fixed / Reference';
        changeEl.className = 'text-xs font-mono text-slate-400';
      }

      // Render KPIs
      document.getElementById('kpi-open').innerText = this._formatCurrency(latest.open);
      document.getElementById('kpi-high').innerText = this._formatCurrency(latest.high);
      document.getElementById('kpi-low').innerText = this._formatCurrency(latest.low);
      document.getElementById('kpi-close').innerText = this._formatCurrency(latest.close);
      document.getElementById('kpi-volume').innerText = this._formatVolume(latest.volume);
      document.getElementById('kpi-sharpe').innerText = risk.annualized_sharpe_ratio !== null ? risk.annualized_sharpe_ratio.toFixed(2) : 'N/A';
      document.getElementById('kpi-drawdown').innerText = risk.maximum_drawdown !== null ? `${(risk.maximum_drawdown * 100).toFixed(2)}%` : 'N/A';
      
      // Current Regime
      const primaryRegime = regimesSummary.summary && regimesSummary.summary[0] ? regimesSummary.summary[0].regime : 'UNKNOWN';
      const regimeEl = document.getElementById('kpi-regime');
      regimeEl.innerText = primaryRegime;
      regimeEl.className = `text-sm font-bold font-mono px-2 py-0.5 rounded ${this._getRegimeBadgeClass(primaryRegime)}`;

      // Data Hygiene Card
      document.getElementById('hygiene-total-records').innerText = `${summary.total_records} Bars`;
      document.getElementById('hygiene-valid-ohlc').innerText = `${summary.valid_ohlc_count} Valid`;
      document.getElementById('hygiene-source').innerText = summary.source || 'Twelve Data';

      this._hideSkeleton('overview-kpi-container');
    } catch (err) {
      console.error("Overview error:", err);
      this._showError('overview-error-container', err.message);
    }
  }

  async _updateTickerCards() {
    ['nvidia', 'bitcoin', 'gold'].forEach(async (id) => {
      try {
        const data = await this.api.getLatest(id);
        const priceEl = document.getElementById(`ticker-price-${id}`);
        const changeEl = document.getElementById(`ticker-change-${id}`);
        if (priceEl) priceEl.innerText = this._formatCurrency(data.price);
        if (changeEl && data.change !== null && data.change !== undefined) {
          const isPos = data.change >= 0;
          changeEl.innerText = `${isPos ? '+' : ''}${data.change_percent || '--'}`;
          changeEl.className = `text-[11px] font-mono ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;
        }
      } catch (e) {
        // Silently preserve placeholder
      }
    });
  }

  // ==========================================
  // VIEW 2: MARKET ANALYSIS
  // ==========================================
  async loadMarketAnalysis(refresh = false) {
    const asset = this.activeAsset;
    try {
      const [hist, indicators] = await Promise.all([
        this.api.getCleanData(asset, refresh),
        this.api.getIndicators(asset, 50, 20, refresh)
      ]);

      const dataPoints = hist.data || [];
      const labels = dataPoints.map(p => p.timestamp.split('T')[0]);
      const prices = dataPoints.map(p => p.close);

      // Indicators alignment map
      const indMap = new Map();
      (indicators.data || []).forEach(item => {
        indMap.set(item.timestamp.split('T')[0], item);
      });

      const sma = labels.map(l => indMap.get(l) ? indMap.get(l).sma : null);
      const ema = labels.map(l => indMap.get(l) ? indMap.get(l).ema : null);

      this.charts.renderPriceChart('market-price-chart', {
        labels,
        prices,
        sma,
        ema,
        assetName: ASSETS[asset].name
      });

      // Render Table Rows (newest first)
      const tbody = document.getElementById('market-historical-tbody');
      if (tbody) {
        const reversed = [...dataPoints].reverse().slice(0, 30);
        tbody.innerHTML = reversed.map(r => `
          <tr class="hover:bg-slate-800/40 transition-colors">
            <td class="py-2.5 px-4 font-medium text-slate-300">${r.timestamp.split('T')[0]}</td>
            <td class="py-2.5 px-4 text-right text-slate-300 font-mono">${this._formatCurrency(r.open)}</td>
            <td class="py-2.5 px-4 text-right text-emerald-400 font-mono">${this._formatCurrency(r.high)}</td>
            <td class="py-2.5 px-4 text-right text-rose-400 font-mono">${this._formatCurrency(r.low)}</td>
            <td class="py-2.5 px-4 text-right text-white font-semibold font-mono">${this._formatCurrency(r.close)}</td>
            <td class="py-2.5 px-4 text-right text-slate-400 font-mono">${this._formatVolume(r.volume)}</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error("Market Analysis Error:", err);
      this._showError('market-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 3: TECHNICAL INDICATORS
  // ==========================================
  async loadIndicators(refresh = false) {
    const asset = this.activeAsset;
    const smaPeriod = parseInt(document.getElementById('input-indicator-sma')?.value || '50', 10);
    const emaPeriod = parseInt(document.getElementById('input-indicator-ema')?.value || '20', 10);

    try {
      const resp = await this.api.getIndicators(asset, smaPeriod, emaPeriod, refresh);
      const points = resp.data || [];
      const labels = points.map(p => p.timestamp.split('T')[0]);
      const prices = points.map(p => p.close);
      const sma = points.map(p => p.sma);
      const ema = points.map(p => p.ema);

      this.charts.renderPriceChart('indicators-chart', {
        labels,
        prices,
        sma,
        ema,
        assetName: ASSETS[asset].name
      });

      // Latest indicator status
      const latest = points[points.length - 1];
      if (latest) {
        document.getElementById('ind-val-close').innerText = this._formatCurrency(latest.close);
        document.getElementById('ind-val-sma').innerText = latest.sma !== null ? this._formatCurrency(latest.sma) : 'Insufficient Data';
        document.getElementById('ind-val-ema').innerText = latest.ema !== null ? this._formatCurrency(latest.ema) : 'Insufficient Data';
        
        const spread = (latest.close !== null && latest.sma !== null) ? ((latest.close - latest.sma) / latest.sma * 100) : null;
        const spreadEl = document.getElementById('ind-val-spread');
        if (spread !== null) {
          spreadEl.innerText = `${spread >= 0 ? '+' : ''}${spread.toFixed(2)}% vs SMA`;
          spreadEl.className = `text-xs font-mono ${spread >= 0 ? 'text-emerald-400' : 'text-rose-400'}`;
        }
      }
    } catch (err) {
      console.error("Indicators error:", err);
      this._showError('indicators-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 4: RETURNS & RISK VOLATILITY
  // ==========================================
  async loadRiskMetrics(refresh = false) {
    const asset = this.activeAsset;
    try {
      const [riskMetrics, riskAnalysis] = await Promise.all([
        this.api.getRiskMetrics(asset, 20, refresh),
        this.api.getRiskAnalysis(asset, 0.0, 252, refresh)
      ]);

      const points = riskMetrics.data || [];
      const labels = points.map(p => p.timestamp.split('T')[0]);
      const returns = points.map(p => p.daily_return !== null ? p.daily_return * 100 : 0);
      const volatility = points.map(p => p.rolling_volatility !== null ? p.rolling_volatility * 100 : null);

      this.charts.renderReturnsChart('returns-bar-chart', { labels, returns });
      this.charts.renderVolatilityChart('volatility-line-chart', { labels, volatility });

      // Drawdown Chart
      const ddLabels = (riskAnalysis.drawdown_series || []).map(p => p.timestamp.split('T')[0]);
      const ddValues = (riskAnalysis.drawdown_series || []).map(p => p.drawdown_pct !== null ? p.drawdown_pct : 0);
      this.charts.renderDrawdownChart('risk-drawdown-chart', { labels: ddLabels, drawdowns: ddValues });

      // KPI metrics
      document.getElementById('risk-sharpe-val').innerText = riskAnalysis.annualized_sharpe_ratio !== null ? riskAnalysis.annualized_sharpe_ratio.toFixed(2) : 'N/A';
      document.getElementById('risk-max-dd-val').innerText = riskAnalysis.maximum_drawdown !== null ? `${(riskAnalysis.maximum_drawdown * 100).toFixed(2)}%` : 'N/A';
      document.getElementById('risk-trough-date').innerText = riskAnalysis.trough_date || 'N/A';
      document.getElementById('risk-peak-date').innerText = riskAnalysis.peak_date || 'N/A';
    } catch (err) {
      console.error("Risk metrics error:", err);
      this._showError('risk-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 5: CORRELATION MATRIX
  // ==========================================
  async loadCorrelation(refresh = false) {
    try {
      const corr = await this.api.getCorrelation(refresh);
      const matrix = corr.matrix || {};

      // Render Matrix Table
      const assets = ['nvidia', 'bitcoin', 'gold'];
      const tbody = document.getElementById('correlation-matrix-tbody');
      if (tbody) {
        tbody.innerHTML = assets.map(a1 => `
          <tr class="hover:bg-slate-800/30">
            <td class="py-3 px-4 font-semibold text-slate-200">${ASSETS[a1].symbol}</td>
            ${assets.map(a2 => {
              const val = matrix[a1] && matrix[a1][a2] !== undefined ? matrix[a1][a2] : 0;
              const bg = this._getCorrelationCellColor(val);
              return `
                <td class="py-3 px-4 text-center font-mono font-bold" style="background-color: ${bg}; color: #ffffff;">
                  ${val.toFixed(3)}
                </td>
              `;
            }).join('')}
          </tr>
        `).join('');
      }

      // Load Rolling Correlation
      const pair = document.getElementById('select-corr-pair')?.value || 'nvidia:bitcoin';
      const windowVal = parseInt(document.getElementById('select-corr-window')?.value || '30', 10);
      const [asset1, asset2] = pair.split(':');

      const rolling = await this.api.getRollingCorrelation(asset1, asset2, windowVal, refresh);
      const rollLabels = (rolling.series || []).map(p => p.timestamp.split('T')[0]);
      const rollValues = (rolling.series || []).map(p => p.correlation);

      this.charts.renderRollingCorrelationChart('rolling-corr-chart', {
        labels: rollLabels,
        series: rollValues,
        pairLabel: `${ASSETS[asset1].symbol} ↔ ${ASSETS[asset2].symbol}`,
        window: windowVal
      });
    } catch (err) {
      console.error("Correlation error:", err);
      this._showError('correlation-error-container', err.message);
    }
  }

  _getCorrelationCellColor(val) {
    if (val === 1.0) return 'rgba(59, 130, 246, 0.4)';
    if (val > 0.5) return 'rgba(16, 185, 129, 0.45)';
    if (val > 0.0) return 'rgba(16, 185, 129, 0.25)';
    if (val > -0.5) return 'rgba(244, 63, 94, 0.25)';
    return 'rgba(244, 63, 94, 0.45)';
  }

  // ==========================================
  // VIEW 6: STRATEGY LAB & SIGNALS
  // ==========================================
  async loadStrategies(refresh = false) {
    const asset = this.activeAsset;
    const strategies = [
      { id: 'sma_crossover', name: 'SMA Crossover', params: { fast_period: 10, slow_period: 30 } },
      { id: 'ema_trend', name: 'EMA Trend', params: { fast_period: 12, slow_period: 26 } },
      { id: 'momentum', name: 'Momentum', params: { lookback_period: 10, threshold: 0.0 } },
      { id: 'mean_reversion', name: 'Mean Reversion', params: { period: 20, num_std: 2.0 } }
    ];

    try {
      const results = await Promise.all(
        strategies.map(s => this.api.getStrategySignals(asset, s.id, s.params, refresh))
      );

      results.forEach((res, idx) => {
        const s = strategies[idx];
        const signals = res.signals || [];
        const latest = signals[signals.length - 1];

        const card = document.getElementById(`strategy-card-${s.id}`);
        if (card && latest) {
          const badge = document.getElementById(`signal-badge-${s.id}`);
          if (badge) {
            badge.innerText = latest.signal;
            badge.className = `px-3 py-1 rounded-lg text-xs font-bold font-mono ${this._getSignalBadgeClass(latest.signal)}`;
          }
          const reason = document.getElementById(`signal-reason-${s.id}`);
          if (reason) reason.innerText = latest.reason || 'Sufficient historical observations';
          const time = document.getElementById(`signal-time-${s.id}`);
          if (time) time.innerText = `Timestamp: ${latest.timestamp.split('T')[0]}`;
        }
      });
    } catch (err) {
      console.error("Strategy Lab Error:", err);
      this._showError('strategies-error-container', err.message);
    }
  }

  _getSignalBadgeClass(sig) {
    if (sig === 'BUY') return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40';
    if (sig === 'SELL') return 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
    return 'bg-slate-700/50 text-slate-300 border border-slate-600/50';
  }

  // ==========================================
  // VIEW 7: BACKTESTING STUDIO
  // ==========================================
  async loadBacktest(refresh = false) {
    const asset = this.activeAsset;
    const stratName = document.getElementById('backtest-strat-select')?.value || 'sma_crossover';
    const capital = parseFloat(document.getElementById('backtest-capital')?.value || '100000');
    const fee = parseFloat(document.getElementById('backtest-fee')?.value || '0.001');
    const allocation = parseFloat(document.getElementById('backtest-allocation')?.value || '1.0');

    // Default params per strategy
    let params = {};
    if (stratName === 'sma_crossover') params = { fast_period: 10, slow_period: 30 };
    else if (stratName === 'ema_trend') params = { fast_period: 12, slow_period: 26 };
    else if (stratName === 'momentum') params = { lookback_period: 10, threshold: 0.0 };
    else if (stratName === 'mean_reversion') params = { period: 20, num_std: 2.0 };

    const payload = {
      strategy_name: stratName,
      initial_capital: capital,
      transaction_cost_rate: fee,
      allocation_fraction: allocation,
      parameters: params
    };

    try {
      const result = await this.api.runBacktest(asset, payload, refresh);
      this.state.backtestResult = result;

      // Update KPI Cards
      document.getElementById('bt-final-val').innerText = this._formatCurrency(result.final_portfolio_value);
      
      const retEl = document.getElementById('bt-total-ret');
      const isPos = result.total_return >= 0;
      retEl.innerText = `${isPos ? '+' : ''}${result.total_return_pct.toFixed(2)}%`;
      retEl.className = `text-xl font-bold font-mono ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;

      document.getElementById('bt-max-dd').innerText = `${(result.maximum_drawdown * 100).toFixed(2)}%`;
      document.getElementById('bt-trades-count').innerText = `${result.number_of_trades} Trades`;
      document.getElementById('bt-benchmark-ret').innerText = `${result.benchmark_return_pct >= 0 ? '+' : ''}${result.benchmark_return_pct.toFixed(2)}%`;
      
      const excessEl = document.getElementById('bt-excess-ret');
      const excessPos = result.excess_return >= 0;
      excessEl.innerText = `${excessPos ? '+' : ''}${result.excess_return_pct.toFixed(2)}%`;
      excessEl.className = `text-xl font-bold font-mono ${excessPos ? 'text-emerald-400' : 'text-rose-400'}`;

      // Render Equity Curve Chart
      const curve = result.equity_curve || [];
      const labels = curve.map(p => p.timestamp.split('T')[0]);
      const strategyValues = curve.map(p => p.portfolio_value);
      const benchmarkValues = curve.map(p => p.benchmark_value);

      this.charts.renderEquityCurveChart('backtest-equity-chart', {
        labels,
        strategyValues,
        benchmarkValues,
        strategyName: result.strategy_name.toUpperCase()
      });

      // Render Trade History Table
      const trades = result.trade_history || [];
      const tbody = document.getElementById('bt-trades-tbody');
      if (tbody) {
        if (trades.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-500 font-sans">No trades triggered during historical window.</td></tr>`;
        } else {
          tbody.innerHTML = trades.slice(0, 50).map(t => `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 px-4 font-mono text-slate-300">${t.timestamp.split('T')[0]}</td>
              <td class="py-2.5 px-4 font-bold font-mono ${t.trade_type === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}">${t.trade_type}</td>
              <td class="py-2.5 px-4 text-right font-mono text-slate-200">${this._formatCurrency(t.price)}</td>
              <td class="py-2.5 px-4 text-right font-mono text-slate-300">${Number(t.shares).toFixed(4)}</td>
              <td class="py-2.5 px-4 text-right font-mono text-slate-400">${this._formatCurrency(t.cost)}</td>
              <td class="py-2.5 px-4 text-right font-mono text-slate-200">${this._formatCurrency(t.value)}</td>
              <td class="py-2.5 px-4 text-right font-mono font-semibold ${t.realized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                ${t.realized_pnl !== null && t.realized_pnl !== undefined ? (t.realized_pnl >= 0 ? '+' : '') + this._formatCurrency(t.realized_pnl) : '--'}
              </td>
            </tr>
          `).join('');
        }
      }
    } catch (err) {
      console.error("Backtest error:", err);
      this._showError('backtest-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 8: STRATEGY COMPARISON
  // ==========================================
  async loadComparison(refresh = false) {
    const asset = this.activeAsset;
    const payload = {
      initial_capital: 100000.0,
      transaction_cost_rate: 0.001,
      allocation_fraction: 1.0,
      sma_params: { fast_period: 10, slow_period: 30 },
      ema_params: { fast_period: 12, slow_period: 26 },
      mom_params: { lookback_period: 10, threshold: 0.0 },
      mr_params: { period: 20, num_std: 2.0 }
    };

    try {
      const comp = await this.api.compareStrategies(asset, payload, refresh);
      const strats = comp.strategies || [];

      // Render Comparison Cards
      const container = document.getElementById('comparison-cards-grid');
      if (container) {
        container.innerHTML = strats.map(s => `
          <div class="glass-card rounded-2xl p-5 border border-slate-700/40 flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between text-xs text-slate-400">
                <span class="font-bold text-slate-200 text-sm">${s.display_name}</span>
                <span class="font-mono px-2 py-0.5 rounded bg-slate-800/80 text-slate-400">${s.number_of_trades} trades</span>
              </div>
              <div class="my-3">
                <div class="text-2xl font-black font-mono text-white">${this._formatCurrency(s.final_portfolio_value)}</div>
                <div class="text-xs font-mono font-semibold ${s.total_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
                  Return: ${s.total_return >= 0 ? '+' : ''}${s.total_return_pct.toFixed(2)}%
                </div>
              </div>
            </div>
            <div class="pt-3 border-t border-slate-800 text-xs space-y-1 font-mono text-slate-400">
              <div class="flex justify-between">
                <span>Max Drawdown:</span>
                <span class="text-rose-400">${(s.maximum_drawdown * 100).toFixed(2)}%</span>
              </div>
              <div class="flex justify-between">
                <span>Excess vs B&H:</span>
                <span class="${s.excess_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${s.excess_return >= 0 ? '+' : ''}${s.excess_return_pct.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        `).join('');
      }

      // Comparison Table
      const tbody = document.getElementById('comparison-tbody');
      if (tbody) {
        tbody.innerHTML = strats.map(s => `
          <tr class="hover:bg-slate-800/40">
            <td class="py-3 px-4 font-bold text-slate-200">${s.display_name}</td>
            <td class="py-3 px-4 text-right font-mono font-bold text-white">${this._formatCurrency(s.final_portfolio_value)}</td>
            <td class="py-3 px-4 text-right font-mono font-bold ${s.total_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
              ${s.total_return >= 0 ? '+' : ''}${s.total_return_pct.toFixed(2)}%
            </td>
            <td class="py-3 px-4 text-right font-mono text-slate-300">${s.number_of_trades}</td>
            <td class="py-3 px-4 text-right font-mono text-rose-400">${(s.maximum_drawdown * 100).toFixed(2)}%</td>
            <td class="py-3 px-4 text-right font-mono text-slate-400">${comp.benchmark_return_pct.toFixed(2)}%</td>
            <td class="py-3 px-4 text-right font-mono font-semibold ${s.excess_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
              ${s.excess_return >= 0 ? '+' : ''}${s.excess_return_pct.toFixed(2)}%
            </td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error("Comparison error:", err);
      this._showError('comparison-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 9: ROBUSTNESS ANALYSIS
  // ==========================================
  async loadRobustness(refresh = false) {
    const asset = this.activeAsset;
    const strat = document.getElementById('robustness-strat-select')?.value || 'sma_crossover';

    let ranges = {};
    if (strat === 'sma_crossover') {
      ranges = { fast_period: [5, 10, 15], slow_period: [20, 30] };
    } else if (strat === 'ema_trend') {
      ranges = { fast_period: [8, 12], slow_period: [20, 26] };
    } else if (strat === 'momentum') {
      ranges = { lookback_period: [5, 10, 15], threshold: [0.0, 0.01] };
    } else if (strat === 'mean_reversion') {
      ranges = { period: [15, 20], num_std: [1.5, 2.0] };
    }

    const payload = {
      strategy_name: strat,
      initial_capital: 100000.0,
      transaction_cost_rate: 0.001,
      allocation_fraction: 1.0,
      parameter_ranges: ranges
    };

    try {
      const resp = await this.api.runRobustness(asset, payload, refresh);
      const results = resp.results || [];

      document.getElementById('robustness-total-combos').innerText = `${resp.total_combinations} Combinations Tested`;

      const tbody = document.getElementById('robustness-tbody');
      if (tbody) {
        tbody.innerHTML = results.map(r => `
          <tr class="hover:bg-slate-800/40">
            <td class="py-2.5 px-4 font-mono text-xs text-indigo-300">${JSON.stringify(r.parameters)}</td>
            <td class="py-2.5 px-4 text-right font-mono text-slate-200">${this._formatCurrency(r.final_portfolio_value)}</td>
            <td class="py-2.5 px-4 text-right font-mono font-bold ${r.total_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
              ${r.total_return >= 0 ? '+' : ''}${r.total_return_pct.toFixed(2)}%
            </td>
            <td class="py-2.5 px-4 text-right font-mono text-slate-300">${r.number_of_trades}</td>
            <td class="py-2.5 px-4 text-right font-mono text-rose-400">${(r.maximum_drawdown * 100).toFixed(2)}%</td>
            <td class="py-2.5 px-4 text-right font-mono font-semibold ${r.excess_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
              ${r.excess_return >= 0 ? '+' : ''}${r.excess_return_pct.toFixed(2)}%
            </td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error("Robustness error:", err);
      this._showError('robustness-error-container', err.message);
    }
  }

  // ==========================================
  // VIEW 10: MARKET REGIMES
  // ==========================================
  async loadRegimes(refresh = false) {
    const asset = this.activeAsset;
    try {
      const [regimes, summary, performance] = await Promise.all([
        this.api.getMarketRegimes(asset, 10, 5, null, 0.0, refresh),
        this.api.getMarketRegimesSummary(asset, 10, 5, null, 0.0, refresh),
        this.api.getStrategyRegimesPerformance(asset, 10, 5, null, 0.0, refresh)
      ]);

      // Summary Donut
      const items = summary.summary || [];
      const labels = items.map(i => i.regime);
      const counts = items.map(i => i.count);
      this.charts.renderRegimeDistributionChart('regime-donut-chart', { labels, counts });

      // Regime Summary Cards
      const container = document.getElementById('regime-summary-cards');
      if (container) {
        container.innerHTML = items.map(item => `
          <div class="glass-card rounded-2xl p-4 border border-slate-700/40">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded ${this._getRegimeBadgeClass(item.regime)}">${item.regime}</span>
            <div class="mt-3 flex items-baseline justify-between">
              <div class="text-2xl font-bold font-mono text-white">${item.count} <span class="text-xs font-normal text-slate-400">bars</span></div>
              <div class="text-sm font-mono text-slate-300 font-semibold">${item.percentage.toFixed(1)}%</div>
            </div>
            <div class="mt-2 text-[10px] text-slate-500 font-mono">Date Range: ${item.start_date || '--'} to ${item.end_date || '--'}</div>
          </div>
        `).join('');
      }

      // Performance by Regime Table
      const perfs = performance.performances || [];
      const perfTbody = document.getElementById('regime-performance-tbody');
      if (perfTbody) {
        perfTbody.innerHTML = perfs.map(p => `
          <tr class="hover:bg-slate-800/40">
            <td class="py-2.5 px-4 font-semibold text-slate-200">${p.strategy.toUpperCase()}</td>
            <td class="py-2.5 px-4 font-mono text-xs"><span class="px-2 py-0.5 rounded ${this._getRegimeBadgeClass(p.regime)}">${p.regime}</span></td>
            <td class="py-2.5 px-4 text-right font-mono text-slate-300">${p.observations}</td>
            <td class="py-2.5 px-4 text-right font-mono text-slate-300">${p.trades}</td>
            <td class="py-2.5 px-4 text-right font-mono font-bold ${p.total_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}">
              ${p.total_return >= 0 ? '+' : ''}${p.total_return_pct.toFixed(2)}%
            </td>
            <td class="py-2.5 px-4 text-right font-mono text-rose-400">${(p.maximum_drawdown * 100).toFixed(2)}%</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      console.error("Regimes error:", err);
      this._showError('regimes-error-container', err.message);
    }
  }

  _getRegimeBadgeClass(regime) {
    if (regime.includes('BULLISH_LOW_VOL')) return 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
    if (regime.includes('BULLISH_HIGH_VOL')) return 'bg-blue-500/20 text-blue-300 border border-blue-500/30';
    if (regime.includes('BEARISH_LOW_VOL')) return 'bg-amber-500/20 text-amber-300 border border-amber-500/30';
    if (regime.includes('BEARISH_HIGH_VOL')) return 'bg-rose-500/20 text-rose-300 border border-rose-500/30';
    return 'bg-slate-700/50 text-slate-300 border border-slate-600/50';
  }

  // ==========================================
  // VIEW 11: SYSTEM STATUS & HEALTH
  // ==========================================
  async loadSystemStatus(refresh = false) {
    try {
      const [health, assets] = await Promise.all([
        this.api.getHealth(),
        this.api.getAssets()
      ]);

      document.getElementById('sys-status').innerText = health.status.toUpperCase();
      document.getElementById('sys-primary-provider').innerText = health.primary_provider || 'Twelve Data';
      document.getElementById('sys-fallback-provider').innerText = health.fallback_provider || 'Alpha Vantage';
      document.getElementById('sys-active-provider').innerText = health.active_provider || 'Twelve Data';
      document.getElementById('sys-twelve-key').innerText = health.masked_twelve_data_key || 'Configured (Masked)';
      document.getElementById('sys-av-key').innerText = health.masked_alpha_vantage_key || 'Configured (Masked)';
      document.getElementById('sys-assets-count').innerText = `${assets.count} Supported Assets`;

      const stats = health.cache_stats || {};
      document.getElementById('sys-cache-hits').innerText = stats.historical_cache_hits || 0;
      document.getElementById('sys-cache-misses').innerText = stats.historical_cache_misses || 0;
    } catch (err) {
      console.error("System status error:", err);
      this._showError('system-error-container', err.message);
    }
  }

  // ==========================================
  // HELPERS & SKELETONS
  // ==========================================
  _formatCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return 'N/A';
    return '$' + Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  _formatVolume(val) {
    if (val === null || val === undefined || isNaN(val) || val === 0) return 'N/A (Spot)';
    return Number(val).toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  _showSkeleton(containerId) {
    const el = document.getElementById(containerId);
    if (el) el.classList.add('opacity-50');
  }

  _hideSkeleton(containerId) {
    const el = document.getElementById(containerId);
    if (el) el.classList.remove('opacity-50');
  }

  _showError(containerId, message) {
    const el = document.getElementById(containerId);
    if (el) {
      el.innerHTML = `
        <div class="glass-panel rounded-2xl p-4 border border-rose-500/30 bg-rose-950/30 flex items-center justify-between text-rose-300">
          <div class="flex items-center gap-3">
            <i data-lucide="alert-circle" class="w-5 h-5 text-rose-400"></i>
            <span class="text-xs font-mono">${message}</span>
          </div>
          <button onclick="window.quantexaApp.renderCurrentView(true)" class="px-3 py-1 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-semibold">
            Retry
          </button>
        </div>
      `;
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  }

  showToast(title, message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-5 right-5 glass-panel rounded-xl p-4 border border-indigo-500/30 bg-slate-900/90 text-white shadow-2xl flex items-center gap-3 z-50 animate-fade-in';
    toast.innerHTML = `
      <div class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></div>
      <div>
        <div class="text-xs font-bold text-indigo-300">${title}</div>
        <div class="text-[11px] text-slate-400">${message}</div>
      </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }

  // ==========================================================================
  // QUANTEXA AI Chatbot Engine
  // ==========================================================================
  openAiChat(initialMessage = null) {
    const drawer = document.getElementById('ai-chat-drawer');
    const overlay = document.getElementById('ai-drawer-overlay');
    if (drawer && overlay) {
      drawer.classList.remove('translate-x-full');
      drawer.classList.add('translate-x-0');
      overlay.classList.remove('hidden');
    }
    const input = document.getElementById('drawer-ai-chat-input') || document.getElementById('ai-chat-input');
    if (initialMessage && input) {
      input.value = initialMessage;
      this.sendChatMessage(initialMessage, 'drawer');
    } else if (input) {
      input.focus();
    }
    if (typeof lucide !== 'undefined') lucide.createIcons();
  }

  closeAiChat() {
    const drawer = document.getElementById('ai-chat-drawer');
    const overlay = document.getElementById('ai-drawer-overlay');
    if (drawer && overlay) {
      drawer.classList.remove('translate-x-0');
      drawer.classList.add('translate-x-full');
      overlay.classList.add('hidden');
    }
  }

  clearChat() {
    this.conversationId = null;
    const containers = [
      document.getElementById('drawer-ai-messages-container'),
      document.getElementById('page-ai-messages-container')
    ];
    const welcomeHtml = `
      <div class="flex items-start gap-3 animate-fade-in">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-pink-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-md">
          <i data-lucide="bot" class="w-4 h-4 text-white"></i>
        </div>
        <div class="chat-bubble-bot p-4 text-xs space-y-2 max-w-[85%]">
          <div class="font-bold text-white flex items-center gap-2">
            QUANTEXA Grounded Financial Intelligence
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300">Zero Hallucination</span>
          </div>
          <p class="text-slate-300 leading-relaxed">
            Conversation history cleared. All inquiries are mathematically grounded in platform quantitative calculations.
          </p>
          <p class="text-slate-400 text-[11px]">
            Ask a new question or select any suggested prompt above.
          </p>
        </div>
      </div>
    `;
    containers.forEach(c => {
      if (c) c.innerHTML = welcomeHtml;
    });
    if (typeof lucide !== 'undefined') lucide.createIcons();
    this.showToast('Conversation Cleared', 'Active AI session memory reset.');
  }

  async sendChatMessage(message, source = 'drawer') {
    if (!message || !message.trim() || this.isAiSending) return;
    const cleanMsg = message.trim();
    this.lastUserMessage = cleanMsg;
    this.isAiSending = true;

    // Clear inputs
    const drawerInput = document.getElementById('drawer-ai-chat-input');
    const pageInput = document.getElementById('page-ai-chat-input');
    if (drawerInput) drawerInput.value = '';
    if (pageInput) pageInput.value = '';

    // Render user message bubble in both containers
    this._appendChatBubble('user', cleanMsg);

    // Show typing indicators
    const drawerTyping = document.getElementById('drawer-ai-typing-indicator');
    const pageTyping = document.getElementById('page-ai-typing-indicator');
    if (drawerTyping) drawerTyping.classList.remove('hidden');
    if (pageTyping) pageTyping.classList.remove('hidden');

    this._scrollChatToBottom();

    try {
      const resp = await this.api.postChatMessage(cleanMsg, this.activeAsset, this.conversationId);
      if (resp && resp.conversation_id) {
        this.conversationId = resp.conversation_id;
      }
      this._appendChatBubble('bot', resp.answer, resp.data_references, resp.timestamp);
    } catch (err) {
      console.error('AI chat error:', err);
      this._appendChatBubble('error', err.message || 'Error communicating with AI assistant.', null, null, true);
    } finally {
      this.isAiSending = false;
      if (drawerTyping) drawerTyping.classList.add('hidden');
      if (pageTyping) pageTyping.classList.add('hidden');
      this._scrollChatToBottom();
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }
  }

  _appendChatBubble(type, content, dataReferences = null, timestamp = null, canRetry = false) {
    const containers = [
      document.getElementById('drawer-ai-messages-container'),
      document.getElementById('page-ai-messages-container')
    ];

    containers.forEach(container => {
      if (!container) return;

      const bubbleWrapper = document.createElement('div');
      bubbleWrapper.className = 'flex items-start gap-3 animate-fade-in';

      if (type === 'user') {
        bubbleWrapper.className = 'flex items-start justify-end gap-3 animate-fade-in';
        bubbleWrapper.innerHTML = `
          <div class="chat-bubble-user p-3.5 text-xs max-w-[85%] leading-relaxed font-sans shadow-md">
            ${this._escapeHtml(content)}
          </div>
          <div class="w-7 h-7 rounded-lg bg-indigo-700/60 border border-indigo-500/40 flex items-center justify-center shrink-0 text-white text-[11px] font-bold">
            U
          </div>
        `;
      } else if (type === 'bot') {
        let refsHtml = '';
        if (dataReferences && dataReferences.length > 0) {
          const pills = dataReferences.map(r => {
            const timePart = r.timestamp ? ` &bull; ${r.timestamp.split('T')[0]}` : '';
            return `<span class="data-reference-pill"><i data-lucide="database" class="w-3 h-3 text-indigo-400"></i> ${r.topic.toUpperCase()} (${r.asset || 'PLATFORM'}${timePart})</span>`;
          }).join(' ');
          refsHtml = `
            <div class="pt-2 border-t border-slate-700/60 mt-2 space-y-1">
              <div class="text-[10px] font-mono text-slate-400 uppercase tracking-wider flex items-center gap-1">
                <i data-lucide="check-circle-2" class="w-3 h-3 text-emerald-400"></i> Grounded Platform References:
              </div>
              <div class="flex flex-wrap gap-1.5 pt-0.5">
                ${pills}
              </div>
            </div>
          `;
        }

        bubbleWrapper.innerHTML = `
          <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-pink-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-md">
            <i data-lucide="bot" class="w-4 h-4 text-white"></i>
          </div>
          <div class="chat-bubble-bot p-4 text-xs space-y-2 max-w-[88%] leading-relaxed">
            <div class="prose prose-invert max-w-none text-slate-200">
              ${this._formatMarkdown(content)}
            </div>
            ${refsHtml}
            ${timestamp ? `<div class="text-[10px] text-slate-500 font-mono text-right pt-1">${new Date(timestamp).toLocaleTimeString()} UTC</div>` : ''}
          </div>
        `;
      } else if (type === 'error') {
        bubbleWrapper.innerHTML = `
          <div class="w-7 h-7 rounded-lg bg-rose-600/80 flex items-center justify-center shrink-0 shadow-md">
            <i data-lucide="alert-triangle" class="w-4 h-4 text-white"></i>
          </div>
          <div class="chat-bubble-bot p-4 text-xs space-y-2 max-w-[88%] border-rose-500/40 bg-rose-950/20 text-rose-200">
            <div class="font-bold flex items-center gap-2 text-rose-300">
              <i data-lucide="alert-circle" class="w-4 h-4"></i> Communication Notice
            </div>
            <p>${this._escapeHtml(content)}</p>
            ${canRetry ? `
              <button onclick="window.quantexaApp.retryLastMessage()" class="mt-2 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-semibold flex items-center gap-1.5 transition-all">
                <i data-lucide="rotate-ccw" class="w-3 h-3"></i> Retry Inquiry
              </button>
            ` : ''}
          </div>
        `;
      }

      container.appendChild(bubbleWrapper);
    });
  }

  retryLastMessage() {
    if (this.lastUserMessage) {
      this.sendChatMessage(this.lastUserMessage);
    }
  }

  _scrollChatToBottom() {
    ['drawer-ai-messages-container', 'page-ai-messages-container'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    });
  }

  _escapeHtml(text) {
    if (!text) return '';
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  _formatMarkdown(text) {
    if (!text) return '';
    let formatted = this._escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em class="text-slate-300">$1</em>');
    formatted = formatted.replace(/^&gt;\s?(.*)$/gm, '<blockquote class="border-l-2 border-indigo-500 pl-2 text-slate-400 italic text-[11px] my-1">$1</blockquote>');
    formatted = formatted.replace(/^•\s?(.*)$/gm, '<div class="flex items-start gap-1.5 my-0.5"><span class="text-indigo-400 font-bold">•</span><span>$1</span></div>');
    formatted = formatted.replace(/^\s+-\s?(.*)$/gm, '<div class="flex items-start gap-1.5 ml-3 my-0.5"><span class="text-slate-500">-</span><span>$1</span></div>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code class="font-mono px-1 py-0.5 rounded bg-slate-800 text-indigo-300 text-[11px]">$1</code>');
    formatted = formatted.replace(/\n\n/g, '<div class="h-2"></div>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
  }
}

// Global App Initialization
document.addEventListener('DOMContentLoaded', () => {
  if (typeof lucide !== 'undefined') lucide.createIcons();
  window.quantexaApp = new QuantexaApp();
  window.quantexaApp.init();
});
