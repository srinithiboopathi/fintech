# QUANTLAB Cross-Asset Correlation & Alignment Methodology

This document details the mathematical framework, date synchronization algorithms, statistical definitions, and look-ahead bias prevention specifications used in the QUANTLAB Correlation Engine (Phase 5).

---

## 1. Return-Based Correlation Philosophy

In institutional quantitative finance, correlation must **never** be computed on raw nominal price levels because non-stationary price series with upward/downward trends generate spurious correlations.

QUANTLAB strictly computes correlation on **daily arithmetic return series**:

$$R_{A,t} = \frac{P_{A,t} - P_{A,t-1}}{P_{A,t-1}}, \quad R_{B,t} = \frac{P_{B,t} - P_{B,t-1}}{P_{B,t-1}}$$

---

## 2. Multi-Market Date Alignment Algorithm

### Heterogeneous Trading Calendars
- **Equities & Commodities (NVIDIA, Gold)**: Trade on NYSE and CME trading days (excluding weekends, federal holidays, and market closures; ~252 sessions/year).
- **Cryptocurrencies (Bitcoin)**: Trade continuously 24 hours a day, 7 days a week, 365 days/year.

### Alignment Methodology
1. **Independent Return Generation**: Daily returns for each asset are calculated on its native sorted chronological price series.
2. **Calendar Intersection**: Return series are joined on normalized ISO-8601 calendar date (`YYYY-MM-DD`).
3. **No Synthetic Forward-Filling**: Days where traditional markets are closed (e.g. weekends/holidays) are not artificially forward-filled with zero return or flat price; rather, correlation is evaluated on the exact overlapping trading days where both assets actively traded.
4. **Observation Count Audit**: Every pairwise and matrix endpoint reports the exact count of overlapping trading dates ($N_{\text{aligned}}$).

---

## 3. Pearson Correlation Formulation

Sample Pearson correlation coefficient between aligned return series $X$ and $Y$ over $N$ overlapping sessions:

$$r_{X,Y} = \frac{\sum_{i=1}^N (X_i - \bar{X})(Y_i - \bar{Y})}{\sqrt{\sum_{i=1}^N (X_i - \bar{X})^2 \sum_{i=1}^N (Y_i - \bar{Y})^2}} = \frac{\text{Cov}(X, Y)}{\sigma_X \sigma_Y}$$

### Matrix & Edge Cases:
- **Diagonal**: $r_{X,X} = 1.0$ (for $N \ge 2, \sigma_X > 0$).
- **Symmetry**: $r_{X,Y} = r_{Y,X}$.
- **Zero / Near-Zero Volatility**: If $\sigma_X \le 10^{-12}$ or $\sigma_Y \le 10^{-12}$, returns $\text{null}$ without division-by-zero or infinity.
- **Bounding**: Results are clipped to $[-1.0, 1.0]$.

---

## 4. Rolling Correlation Engine

Measures time-varying dependency and co-movement regimes over lookback windows ($w \in [20, 30, 60, 90, \dots]$):

$$r_{X,Y}(t) = \frac{\text{Cov}_{w,t}(X, Y)}{\sigma_{X,w,t} \cdot \sigma_{Y,w,t}}$$

- **Warm-Up Period**: For $t < w-1$, rolling correlation returns $\text{null}$.
- **Look-Ahead Bias Prevention**: Enforces `center=False`. Future prices or returns are never accessible to rolling windows at time $t$.

---

## 5. Comparative Performance Statistics

Composes Phase 4 quantitative metrics to provide synchronized multi-asset comparisons:
- **Total Compounded Return**: $\prod_{t=1}^T (1 + R_t) - 1$
- **Compound Annual Growth Rate (CAGR)**: $(1 + \text{Total Return})^{365.25 / \text{Days}} - 1$
- **Annualized Volatility**: $\text{std}(R_{\text{daily}}, \text{ddof}=1) \times \sqrt{N_{\text{ann}}}$ ($N_{\text{ann}}=365$ for Bitcoin, $252$ for Gold/NVIDIA)
- **Sharpe Ratio**: $\frac{\bar{R}_{\text{daily}}}{\sigma_{\text{daily}}} \times \sqrt{N_{\text{ann}}}$
- **Maximum Drawdown (MDD)**: $\min_t (\frac{P_t}{\text{Peak}_t} - 1)$
