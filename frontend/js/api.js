/**
 * Quantexa — Centralized API Client Layer
 * Handles communication strictly with Quantexa backend (port 8000).
 * Never communicates with external providers directly.
 */

class QuantexaApiClient {
  constructor() {
    const urlParam = new URLSearchParams(window.location.search).get('api');
    const storageUrl = localStorage.getItem('QUANTEXA_API_BASE');
    
    if (urlParam) {
      this.baseUrl = urlParam;
    } else if (storageUrl) {
      this.baseUrl = storageUrl;
    } else if (window.location.origin.includes('8000')) {
      this.baseUrl = window.location.origin;
    } else {
      this.baseUrl = 'https://fintech-bkpb.onrender.com';
    }

    // In-memory request deduplication and temporary response cache
    this._cache = new Map();
    this._inflight = new Map();
    this.cacheTtlMs = 60000; // 60s client cache
  }

  setBaseUrl(url) {
    this.baseUrl = url.replace(/\/+$/, '');
    localStorage.setItem('QUANTEXA_API_BASE', this.baseUrl);
    this._cache.clear();
  }

  async _request(endpoint, options = {}) {
    const method = options.method || 'GET';
    const isGet = method === 'GET';
    const cacheKey = `${method}:${endpoint}:${options.body ? JSON.stringify(options.body) : ''}`;

    // Return cached GET response if valid and not forcing refresh
    if (isGet && !options.skipCache && this._cache.has(cacheKey)) {
      const entry = this._cache.get(cacheKey);
      if (Date.now() - entry.timestamp < this.cacheTtlMs) {
        return entry.data;
      }
      this._cache.delete(cacheKey);
    }

    // Deduplicate concurrent inflight requests
    if (this._inflight.has(cacheKey)) {
      return this._inflight.get(cacheKey);
    }

    const fetchPromise = (async () => {
      try {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
          'Accept': 'application/json',
          ...(options.headers || {})
        };
        if (options.body && typeof options.body === 'object') {
          headers['Content-Type'] = 'application/json';
        }

        const res = await fetch(url, {
          ...options,
          headers,
          body: options.body && typeof options.body === 'object' ? JSON.stringify(options.body) : options.body
        });

        if (!res.ok) {
          let errorData = {};
          try {
            errorData = await res.json();
          } catch (e) {
            errorData = { message: res.statusText };
          }
          const err = new Error(errorData.message || errorData.detail || `Request failed with HTTP ${res.status}`);
          err.status = res.status;
          err.errorType = errorData.error || 'API_ERROR';
          err.details = errorData.details || null;
          throw err;
        }

        const data = await res.json();
        if (isGet) {
          this._cache.set(cacheKey, { data, timestamp: Date.now() });
        }
        return data;
      } finally {
        this._inflight.delete(cacheKey);
      }
    })();

    this._inflight.set(cacheKey, fetchPromise);
    return fetchPromise;
  }

  clearCache() {
    this._cache.clear();
  }

  // System & Meta
  async getHealth() {
    return this._request('/health', { skipCache: true });
  }

  async getAssets() {
    return this._request('/assets');
  }

  // Market Data
  async getLatest(asset, refresh = false) {
    return this._request(`/market/${asset}/latest?refresh=${refresh}`, { skipCache: refresh });
  }

  async getHistorical(asset, outputsize = 'compact', refresh = false) {
    return this._request(`/market/${asset}/historical?outputsize=${outputsize}&refresh=${refresh}`, { skipCache: refresh });
  }

  async getCleanData(asset, refresh = false) {
    return this._request(`/market/${asset}/data?refresh=${refresh}`, { skipCache: refresh });
  }

  async getDataSummary(asset, refresh = false) {
    return this._request(`/market/${asset}/data/summary?refresh=${refresh}`, { skipCache: refresh });
  }

  // Quantitative Indicators & Risk
  async getIndicators(asset, smaPeriod = 50, emaPeriod = 20, refresh = false) {
    return this._request(`/market/${asset}/indicators?sma_period=${smaPeriod}&ema_period=${emaPeriod}&refresh=${refresh}`, { skipCache: refresh });
  }

  async getRiskMetrics(asset, volatilityPeriod = 20, refresh = false) {
    return this._request(`/market/${asset}/risk-metrics?volatility_period=${volatilityPeriod}&refresh=${refresh}`, { skipCache: refresh });
  }

  async getRiskAnalysis(asset, rf = 0.0, annualizationFactor = 252, refresh = false) {
    return this._request(`/market/${asset}/risk-analysis?risk_free_rate=${rf}&annualization_factor=${annualizationFactor}&refresh=${refresh}`, { skipCache: refresh });
  }

  // Correlation
  async getCorrelation(refresh = false) {
    return this._request(`/market/correlation?refresh=${refresh}`, { skipCache: refresh });
  }

  async getRollingCorrelation(asset1, asset2, window = 30, refresh = false) {
    return this._request(`/market/correlation/rolling?asset1=${asset1}&asset2=${asset2}&window=${window}&refresh=${refresh}`, { skipCache: refresh });
  }

  // Strategy Lab & Signals
  async getStrategySignals(asset, strategyName, parameters, refresh = false) {
    return this._request(`/market/${asset}/strategy/signals?refresh=${refresh}`, {
      method: 'POST',
      body: {
        strategy: strategyName,
        strategy_name: strategyName,
        parameters: parameters || {}
      },
      skipCache: refresh
    });
  }

  // Backtesting
  async runBacktest(asset, payload, refresh = false) {
    return this._request(`/market/${asset}/strategy/backtest?refresh=${refresh}`, {
      method: 'POST',
      body: payload,
      skipCache: true
    });
  }

  // Strategy Comparison
  async compareStrategies(asset, payload, refresh = false) {
    return this._request(`/market/${asset}/strategy/compare?refresh=${refresh}`, {
      method: 'POST',
      body: payload,
      skipCache: refresh
    });
  }

  // Robustness Analysis
  async runRobustness(asset, payload, refresh = false) {
    return this._request(`/market/${asset}/strategy/robustness?refresh=${refresh}`, {
      method: 'POST',
      body: payload,
      skipCache: refresh
    });
  }

  // Market Regimes
  async getMarketRegimes(asset, trendPeriod = 50, volWindow = 20, volThreshold = null, trendThreshold = 0.0, refresh = false) {
    let url = `/market/${asset}/regimes?trend_period=${trendPeriod}&volatility_window=${volWindow}&trend_threshold=${trendThreshold}&refresh=${refresh}`;
    if (volThreshold !== null && volThreshold !== undefined && volThreshold !== '') {
      url += `&volatility_threshold=${volThreshold}`;
    }
    return this._request(url, { skipCache: refresh });
  }

  async getMarketRegimesSummary(asset, trendPeriod = 50, volWindow = 20, volThreshold = null, trendThreshold = 0.0, refresh = false) {
    let url = `/market/${asset}/regimes/summary?trend_period=${trendPeriod}&volatility_window=${volWindow}&trend_threshold=${trendThreshold}&refresh=${refresh}`;
    if (volThreshold !== null && volThreshold !== undefined && volThreshold !== '') {
      url += `&volatility_threshold=${volThreshold}`;
    }
    return this._request(url, { skipCache: refresh });
  }

  async getStrategyRegimesPerformance(asset, trendPeriod = 50, volWindow = 20, volThreshold = null, trendThreshold = 0.0, refresh = false) {
    let url = `/market/${asset}/regimes/performance?trend_period=${trendPeriod}&volatility_window=${volWindow}&trend_threshold=${trendThreshold}&refresh=${refresh}`;
    if (volThreshold !== null && volThreshold !== undefined && volThreshold !== '') {
      url += `&volatility_threshold=${volThreshold}`;
    }
    return this._request(url, { skipCache: refresh });
  }

  // Grounded AI Financial Intelligence Assistant
  async postChatMessage(message, asset = null, conversationId = null) {
    const payload = {
      message: (message || '').trim(),
      asset: asset || undefined,
      conversation_id: conversationId || undefined
    };
    return this._request('/ai/chat', {
      method: 'POST',
      body: payload,
      skipCache: true
    });
  }

  async getAIStatus() {
    return this._request('/ai/status', { skipCache: true });
  }
}

// Global singleton instance
window.quantexaApi = new QuantexaApiClient();
