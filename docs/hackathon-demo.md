# QUANTLAB Hackathon & Demonstration Guide

## 1. Demo Narrative

QUANTLAB demonstrates end-to-end quantitative financial engineering:
1. **Asset Selection**: Seamlessly toggle between Gold (Safe-Haven Commodity), Bitcoin (Digital Asset), and NVIDIA (High-Beta AI Leader).
2. **Quantitative Deep-Dive**: Examine moving averages, volatility clustering, rolling Sharpe ratios, and max drawdown profiles.
3. **Cross-Asset Correlation**: Discover macro regime shifts and decoupling events via dynamic correlation heatmaps and rolling correlation windows.
4. **Strategy Formulation**: Configure SMA crossover, EMA trend, momentum, and mean reversion rules.
5. **Rigorous Backtesting**: Execute realistic simulation incorporating transaction fees, analyzing equity curves, drawdown waterfalls, and trade logs.
6. **Robustness & Regimes**: Stress test parameters and observe strategy performance across Bullish, Bearish, and Sideways volatility regimes.
7. **Institutional Reporting**: Generate institutional tear sheets and executive research reports.

---

## 2. Key Differentiation Points

- **Zero Fake Data**: Computations are executed against real Kaggle historical datasets.
- **True Full-Stack Separation**: React UI presents data calculated by FastAPI/Pandas/NumPy/SciPy micro-engines.
- **Realistic Friction**: Incorporates slippage and trading fees to eliminate unrealistic backtest returns.
- **Institutional UI**: High-density, dark terminal aesthetic built with Apache ECharts.
