/**
 * TypeScript Data Models for QUANTLAB Backend APIs (Phases 3-8).
 */

// ==========================================
// 1. Market Data Types
// ==========================================

export interface AssetItem {
  symbol: string;
  name: string;
  category: string;
}

export interface AssetListResponse {
  assets: AssetItem[];
}

export interface AssetMetadataResponse {
  asset: string;
  start_date: string;
  end_date: string;
  records: number;
  frequency: string;
}

export interface DateRangeInfo {
  start_date: string;
  end_date: string;
  records: number;
}

export interface MultiAssetDateRangeResponse {
  ranges: Record<string, DateRangeInfo>;
}

export interface MarketDataPoint {
  date: string;
  asset: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HistoricalDataResponse {
  asset: string;
  count: number;
  total: number;
  data: MarketDataPoint[];
}

export interface MultiAssetHistoricalDataResponse {
  assets: string[];
  count: number;
  total: number;
  data: MarketDataPoint[];
}

// ==========================================
// 2. Quantitative Indicators Types
// ==========================================

export interface IndicatorDataPoint {
  date: string;
  close: number;
  sma: number | null;
  ema: number | null;
}

export interface IndicatorResponse {
  asset: string;
  frequency: string;
  sma_period: number;
  ema_period: number;
  count: number;
  data: IndicatorDataPoint[];
}

export interface ReturnDataPoint {
  date: string;
  close: number;
  daily_return: number | null;
  cumulative_return: number | null;
}

export interface ReturnsResponse {
  asset: string;
  frequency: string;
  count: number;
  data: ReturnDataPoint[];
}

export interface VolatilityDataPoint {
  date: string;
  rolling_volatility: number | null;
  annualized_volatility: number | null;
}

export interface VolatilityResponse {
  asset: string;
  window: number;
  annualization_factor: number;
  count: number;
  data: VolatilityDataPoint[];
}

export interface RiskMetricsResponse {
  asset: string;
  start_date: string;
  end_date: string;
  records: number;
  risk_free_rate: number;
  annualization_factor: number;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
}

export interface RollingPerformancePoint {
  date: string;
  rolling_return: number | null;
  rolling_volatility: number | null;
  rolling_sharpe: number | null;
  drawdown: number | null;
}

export interface RollingPerformanceResponse {
  asset: string;
  window: number;
  count: number;
  data: RollingPerformancePoint[];
}

export interface ReturnStatistics {
  mean: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  positive_days: number;
  negative_days: number;
}

export interface AssetQuantSummaryResponse {
  asset: string;
  start_date: string;
  end_date: string;
  records: number;
  latest_close: number;
  cumulative_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
  return_statistics: ReturnStatistics;
}

// ==========================================
// 3. Correlation & Comparison Types
// ==========================================

export interface CorrelationMatrixResponse {
  assets: string[];
  matrix: Record<string, Record<string, number | null>>;
  observations: number;
  start_date: string;
  end_date: string;
}

export interface PairCorrelationResponse {
  asset_a: string;
  asset_b: string;
  correlation: number | null;
  covariance: number | null;
  observations: number;
  start_date: string;
  end_date: string;
}

export interface RollingCorrelationPoint {
  date: string;
  correlation: number | null;
}

export interface RollingCorrelationResponse {
  asset_a: string;
  asset_b: string;
  window: number;
  count: number;
  data: RollingCorrelationPoint[];
}

export interface AssetComparisonMetrics {
  asset: string;
  total_return: number | null;
  annualized_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
  observations: number;
}

export interface AssetComparisonResponse {
  start_date: string;
  end_date: string;
  assets: AssetComparisonMetrics[];
}

// ==========================================
// 4. Strategy Engine Types
// ==========================

export interface StrategySignalPoint {
  date: string;
  close: number;
  signal: number; // 1 = BUY, -1 = SELL, 0 = HOLD
  position: number;
  indicators: Record<string, number | null>;
}

export interface SignalCounts {
  buy: number;
  sell: number;
  hold: number;
}

export interface StrategyResponse {
  asset: string;
  strategy: string;
  parameters: Record<string, any>;
  count: number;
  signal_counts: SignalCounts;
  data: StrategySignalPoint[];
}

// ==========================================
// 5. Backtesting Engine Types
// ==========================================

export interface BacktestRequest {
  asset: string;
  strategy: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  position_size?: number;
  transaction_cost?: number;
  risk_free_rate?: number;
  strategy_parameters?: Record<string, any>;
}

export interface BacktestPerformance {
  initial_capital: number;
  final_portfolio_value: number;
  net_profit: number;
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  maximum_drawdown: number;
  number_of_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  gross_profit: number;
  gross_loss: number;
  total_fees_paid: number;
  average_trade_return: number | null;
}

export interface BenchmarkPerformance {
  initial_capital: number;
  final_portfolio_value: number;
  net_profit: number;
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  maximum_drawdown: number;
}

export interface BacktestComparison {
  return_difference: number;
  sharpe_difference: number;
  mdd_difference: number;
}

export interface EquityCurvePoint {
  date: string;
  portfolio_value: number;
  cash: number;
  position_value: number;
  daily_return: number | null;
  cumulative_return: number;
  drawdown: number;
  benchmark_value: number;
  benchmark_return: number;
  benchmark_drawdown: number;
}

export interface TradeRecord {
  trade_id: number;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  entry_notional: number;
  exit_notional: number;
  entry_cost: number;
  exit_cost: number;
  gross_pnl: number;
  net_pnl: number;
  return_pct: number;
  holding_period_days: number;
}

export interface OpenPosition {
  entry_date: string;
  entry_price: number;
  quantity: number;
  entry_notional: number;
  entry_cost: number;
  current_price: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_return_pct: number;
  holding_period_days: number;
}

export interface BacktestResponse {
  backtest: {
    asset: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    position_size: number;
    transaction_cost: number;
    risk_free_rate: number;
    trading_days: number;
  };
  strategy: {
    name: string;
    display_name: string;
    parameters: Record<string, any>;
  };
  performance: BacktestPerformance;
  benchmark: BenchmarkPerformance;
  comparison: BacktestComparison;
  equity_curve: EquityCurvePoint[];
  trades: TradeRecord[];
  open_position: OpenPosition | null;
}

export interface StrategyInfo {
  name: string;
  display_name: string;
  description: string;
  default_parameters: Record<string, any>;
}

export interface StrategyInfoListResponse {
  strategies: StrategyInfo[];
}

// ==========================================
// 6. Strategy Robustness Lab Types
// ==========================================

export interface RobustnessPeriod {
  start_date?: string;
  end_date?: string;
}

export interface RobustnessRequest {
  asset: string;
  strategy: string;
  start_date?: string;
  end_date?: string;
  periods?: RobustnessPeriod[];
  initial_capital?: number;
  position_size?: number;
  transaction_costs?: number[];
  risk_free_rate?: number;
  strategy_parameter_grid?: Record<string, any[]>;
  max_configurations?: number;
}

export interface RobustnessConfigResult {
  parameters: Record<string, any>;
  transaction_cost: number;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_portfolio_value: number;
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  maximum_drawdown: number;
  number_of_trades: number;
  win_rate: number;
}

export interface MetricMinMax {
  min: number;
  max: number;
}

export interface TradesMinMax {
  min: number;
  max: number;
}

export interface RobustnessMetricRanges {
  return_range: MetricMinMax;
  sharpe_range: MetricMinMax;
  drawdown_range: MetricMinMax;
  trades_range: TradesMinMax;
  win_rate_range: MetricMinMax;
}

export interface RobustnessSummary {
  total_configurations: number;
  parameter_ranges: Record<string, any>;
  transaction_costs: number[];
  periods_tested: Array<{ start_date?: string; end_date?: string }>;
  metrics_ranges: RobustnessMetricRanges;
}

export interface RobustnessResponse {
  asset: string;
  strategy: string;
  summary: RobustnessSummary;
  results: RobustnessConfigResult[];
}

// ==========================================
// 7. Market Regime Analysis Types
// ==========================================

export type MarketRegimeType = 'BULL' | 'BEAR';
export type VolatilityStateType = 'HIGH_VOLATILITY' | 'LOW_VOLATILITY';
export type ThresholdModeType = 'historical_descriptive' | 'expanding_threshold';

export interface RegimeDataPoint {
  date: string;
  asset: string;
  close: number;
  trend_value: number | null;
  trend_window: number;
  rolling_volatility: number | null;
  volatility_window: number;
  volatility_threshold: number | null;
  regime: MarketRegimeType | null;
  volatility_state: VolatilityStateType | null;
}

export interface RegimeMetrics {
  observation_count: number;
  percentage: number;
  start_date: string | null;
  end_date: string | null;
  average_daily_return: number | null;
  cumulative_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  maximum_drawdown: number | null;
}

export interface TransitionEvent {
  date: string;
  transition_type: string;
  from_state: string;
  to_state: string;
}

export interface RegimeSummaryStatistics {
  bull: RegimeMetrics;
  bear: RegimeMetrics;
  high_volatility: RegimeMetrics;
  low_volatility: RegimeMetrics;
  total_observations: number;
  classified_trend_observations: number;
  classified_volatility_observations: number;
}

export interface RegimeResponse {
  asset: string;
  trend_window: number;
  volatility_window: number;
  threshold_mode: ThresholdModeType | string;
  start_date: string | null;
  end_date: string | null;
  summary_statistics: RegimeSummaryStatistics;
  transitions: TransitionEvent[];
  data: RegimeDataPoint[];
}

// ==========================================
// 8. Authentication Types
// ==========================================

export interface User {
  id: number;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface MessageResponse {
  message: string;
}

// ==========================================
// 9. Portfolio Analytics Types (Phase 11)
// ==========================================

export interface PortfolioAnalysisRequest {
  weights: Record<string, number>;
  start_date?: string | null;
  end_date?: string | null;
  initial_capital?: number;
  risk_free_rate?: number;
}

export interface AssetPerformanceContribution {
  asset: string;
  weight: number;
  total_return: number;
  weighted_contribution: number;
  contribution_percentage: number | null;
}

export interface AssetRiskContribution {
  asset: string;
  weight: number;
  annualized_volatility: number;
  marginal_risk_contribution: number;
  component_risk_contribution: number;
  percentage_risk_contribution: number;
}

export interface PortfolioSummaryMetrics {
  initial_capital: number;
  final_value: number;
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  sharpe_ratio: number;
  maximum_drawdown: number;
  observations: number;
  start_date: string;
  end_date: string;
}

export interface PortfolioDataPoint {
  date: string;
  portfolio_return: number;
  cumulative_return: number;
  portfolio_value: number;
  drawdown: number;
}

export interface PortfolioComparisonPoint {
  date: string;
  portfolio: number;
  assets: Record<string, number>;
}

export interface PortfolioAnalysisResponse {
  weights: Record<string, number>;
  summary: PortfolioSummaryMetrics;
  performance_contributions: AssetPerformanceContribution[];
  risk_contributions: AssetRiskContribution[];
  covariance_matrix: Record<string, Record<string, number>>;
  data: PortfolioDataPoint[];
  comparison: PortfolioComparisonPoint[];
}

