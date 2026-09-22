export interface User {
  id: string;
  username: string;
  name: string;
  email: string;
  role: string;
  tier: string;
}

export interface OHLCVBar {
  date: string;
  symbol: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number;
  volume: number;
  daily_return: number;
}

export interface AssetOverview {
  symbol: string;
  name: string;
  category: string;
  current_price: number;
  change_24h: number;
  volatility_30d: number;
  sharpe_1y: number;
  regime: string;
  volume_24h: number;
  high_52w: number;
  low_52w: number;
  sparkline: number[];
}

export interface IndicatorData {
  symbol: string;
  dates: string[];
  sma_20: (number | null)[];
  sma_50: (number | null)[];
  ema_9: (number | null)[];
  ema_21: (number | null)[];
  rsi: (number | null)[];
  bb_upper: (number | null)[];
  bb_middle: (number | null)[];
  bb_lower: (number | null)[];
  macd: (number | null)[];
  macd_signal: (number | null)[];
  macd_hist: (number | null)[];
  atr: (number | null)[];
}

export interface RiskMetrics {
  symbol: string;
  cagr: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_duration_days: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
  beta_to_sp500: number;
  alpha_annualized: number;
}

export interface CorrelationMatrixData {
  symbols: string[];
  raw_symbols: string[];
  matrix: number[][];
  method: string;
}

export interface RollingCorrelationPoint {
  date: string;
  correlation: number;
}

export interface StrategyParamDef {
  type: 'int' | 'float';
  default: number;
  min: number;
  max: number;
  label: string;
}

export interface StrategyInfo {
  id: string;
  name: string;
  category: string;
  description: string;
  parameters: Record<string, StrategyParamDef>;
}

export interface BacktestRequest {
  strategy_id: string;
  symbol: string;
  parameters: Record<string, any>;
  initial_capital: number;
  position_sizing: string;
  position_size_value: number;
  commission_bps: number;
  slippage_pct: number;
  start_date?: string;
  end_date?: string;
}

export interface EquityPoint {
  date: string;
  equity: number;
  benchmark_equity: number;
  drawdown_pct: number;
  cash: number;
  holdings_value: number;
}

export interface Trade {
  trade_id: string;
  symbol: string;
  side: string;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  quantity: number;
  pnl_usd: number;
  pnl_pct: number;
  commission: number;
  slippage: number;
  duration_days: number;
  exit_reason: string;
}

export interface BacktestResult {
  run_id: string;
  strategy_id: string;
  strategy_name: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_equity: number;
  total_return_pct: number;
  benchmark_return_pct: number;
  cagr: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_trade_pnl_pct: number;
  max_win_pct: number;
  max_loss_pct: number;
  equity_curve: EquityPoint[];
  trades: Trade[];
  parameters: Record<string, any>;
}

export interface MonteCarloResult {
  symbol: string;
  num_simulations: number;
  horizon_days: number;
  p5_equity_curve: number[];
  p50_equity_curve: number[];
  p95_equity_curve: number[];
  sample_trajectories: number[][];
  metrics: {
    terminal_wealth_p5: number;
    terminal_wealth_p50: number;
    terminal_wealth_p95: number;
    max_drawdown_p5: number;
    max_drawdown_p50: number;
    max_drawdown_p95: number;
    sharpe_p5: number;
    sharpe_p50: number;
    sharpe_p95: number;
  };
}

export interface RegimePoint {
  date: string;
  regime: string;
  volatility_rank: string;
  trend_direction: string;
  realized_volatility: number;
  confidence: number;
}

export interface RegimeDetectionResponse {
  symbol: string;
  current_regime: RegimePoint;
  distribution_pct: Record<string, number>;
  series: RegimePoint[];
}

export interface ResearchReportResponse {
  report_id: string;
  symbol: string;
  date_range: {
    start_date: string;
    end_date: string;
    total_bars: number;
  };
  price_summary: {
    latest_close: number;
    period_high: number;
    period_low: number;
    total_volume: number;
  };
  performance_metrics: {
    total_cumulative_return_pct: number;
    cagr_pct: number;
    annualized_volatility_pct: number;
    downside_volatility_pct: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
    max_drawdown_pct: number;
    max_drawdown_duration_days: number;
    var_95_pct: number;
    cvar_95_pct: number;
  };
  correlation_profile: Record<string, number>;
  current_market_regime: string;
  baseline_backtest: {
    strategy: string;
    total_return_pct: number;
    sharpe_ratio: number;
    max_drawdown_pct: number;
    total_trades: number;
    benchmark_return_pct: number;
    alpha_excess_return_pct: number;
  };
  generated_at: string;
}

export interface SensitivityResultItem {
  parameters: Record<string, any>;
  commission_bps: number;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  total_trades: number;
  profit_factor: number;
}

export interface SensitivityResponse {
  symbol: string;
  strategy_id: string;
  total_permutations: number;
  results: SensitivityResultItem[];
}

