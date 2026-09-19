# Portfolio Optimization & Markowitz Efficient Frontier Methodology

## 1. Executive Summary & Theoretical Framework

**Phase 12: Portfolio Optimization** integrates classical **Markowitz Modern Portfolio Theory (MPT)** into QuantLab's multi-asset analytics suite. By modeling the trade-off between expected return ($\mu$) and variance ($\sigma^2$), the optimization engine solves for mathematical allocations that either minimize portfolio volatility or maximize risk-adjusted return (Sharpe ratio) under linear equality and bound constraints on the portfolio simplex.

```
       Expected Return (mu)
             ^
             |                      * Maximum Sharpe Portfolio (Tangency)
             |                   . '  
             |             . - '      ====================== Efficient Frontier
             |       . - '            . . . . . . . . . .
             |    * GMV Portfolio    . .  Random Feasible .
             |   /                  . . .  Portfolios  . .
             |  /                    . . . . . . . . . . .
             | /                      . . . . . . . . . .
         rf -+---------------------------------------------> Volatility (sigma)
```

---

## 2. Mathematical Formulations

### 2.1 Asset Returns and Covariance Matrix
Let $\mathcal{A} = \{A_1, A_2, \dots, A_N\}$ represent a multi-asset universe of $N \ge 2$ synchronized assets with $T$ common trading days:
$$\mathbf{R} = [r_{t,i}] \in \mathbb{R}^{T \times N}$$

1. **Annualized Expected Return Vector**:
   $$\mu_i = 252 \times \frac{1}{T} \sum_{t=1}^T r_{t,i}, \quad \mathbf{\mu} = (\mu_1, \dots, \mu_N)^T$$

2. **Sample Daily Covariance Matrix** (degrees of freedom $\text{ddof} = 1$):
   $$\mathbf{\Sigma}_{\text{daily}} = \frac{1}{T-1} (\mathbf{R} - \bar{\mathbf{R}})^T (\mathbf{R} - \bar{\mathbf{R}})$$

3. **Annualized Covariance Matrix**:
   $$\mathbf{\Sigma} = 252 \times \mathbf{\Sigma}_{\text{daily}}$$

---

### 2.2 Portfolio Statistics
Given a portfolio weight vector $\mathbf{w} = (w_1, \dots, w_N)^T$:

- **Expected Annual Return**:
  $$\mu_p = \mathbf{w}^T \mathbf{\mu} = \sum_{i=1}^N w_i \mu_i$$

- **Annualized Portfolio Variance**:
  $$\sigma_p^2 = \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} = \sum_{i=1}^N \sum_{j=1}^N w_i w_j \Sigma_{ij}$$

- **Annualized Portfolio Volatility (Risk)**:
  $$\sigma_p = \sqrt{\max(0, \mathbf{w}^T \mathbf{\Sigma} \mathbf{w})}$$

- **Risk-Adjusted Sharpe Ratio**:
  $$\text{Sharpe} = \begin{cases} \frac{\mu_p - r_f}{\sigma_p}, & \text{if } \sigma_p > 10^{-12} \\ 0, & \text{otherwise} \end{cases}$$
  where $r_f$ is the user-configured annualized risk-free rate.

---

## 3. Optimization Problems & Constrained Solvers

All optimizations are solved using **Sequential Least Squares Programming (SLSQP)** via `scipy.optimize.minimize`.

### 3.1 Weight Constraints & Simplex Feasibility
1. **Full Capital Investment**:
   $$\sum_{i=1}^N w_i = 1.0$$
2. **Individual Weight Bounds**:
   $$w_{\min} \le w_i \le w_{\max}, \quad \forall i \in \{1, \dots, N\}$$
   where $0.0 \le w_{\min} \le w_{\max} \le 1.0$.
3. **Simplex Feasibility Conditions**:
   - **Minimum Weight Sum**: $N \times w_{\min} \le 1.0$ (otherwise sum of minimum weights exceeds 100%).
   - **Maximum Weight Sum**: $N \times w_{\max} \ge 1.0$ (otherwise weights cannot reach 100%).

---

### 3.2 Global Minimum Variance (GMV) Portfolio
Finds the allocation vector $\mathbf{w}_{\text{GMV}}$ that minimizes total portfolio risk:
$$\min_{\mathbf{w}} \mathbf{w}^T \mathbf{\Sigma} \mathbf{w}$$
$$\text{subject to } \sum_{i=1}^N w_i = 1, \quad w_{\min} \le w_i \le w_{\max}$$

---

### 3.3 Maximum Sharpe Ratio (Tangency) Portfolio
Finds the allocation vector $\mathbf{w}_{\text{MaxSharpe}}$ that maximizes excess return per unit of volatility:
$$\max_{\mathbf{w}} \frac{\mathbf{w}^T \mathbf{\mu} - r_f}{\sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}}}$$
$$\text{Equivalent to: } \min_{\mathbf{w}} - \frac{\mathbf{w}^T \mathbf{\mu} - r_f}{\sqrt{\mathbf{w}^T \mathbf{\Sigma} \mathbf{w}} + \epsilon}$$
$$\text{subject to } \sum_{i=1}^N w_i = 1, \quad w_{\min} \le w_i \le w_{\max}$$

---

### 3.4 Equal-Weight Benchmark ($1/N$)
Allocates equal capital weight across all $N$ assets:
$$w_i = \frac{1}{N}, \quad \forall i$$
- **Validation**: Enforces $w_{\min} \le \frac{1}{N} \le w_{\max}$. If violated, an explicit `HTTP 422 Unprocessable Content` exception is returned rather than silently modifying weights.

---

## 4. Markowitz Efficient Frontier Construction

The **Efficient Frontier** represents the set of optimal portfolios that offer the highest expected return for a defined level of risk, or the lowest risk for a given level of expected return.

```
Frontier Algorithm:
1. Solve for GMV portfolio return: mu_GMV
2. Determine maximum feasible expected return: mu_max = max_{w in Simplex} (w^T mu)
3. Discretize target return range into P points: mu_target in linspace(mu_GMV, mu_max, P)
4. For each target return mu_target:
     minimize w^T Sigma w
     subject to:
       sum(w) = 1
       w^T mu = mu_target
       w_min <= w_i <= w_max
5. If solver converges, record (sigma_p, mu_p, Sharpe, w).
6. Filter out unconverged or infeasible points without fabricating data.
```

---

## 5. Feasible Random Portfolio Sampling

To provide visual context of the feasible investment opportunity set, the engine samples $K$ random portfolios (default 5,000; maximum 10,000) using a deterministic random seed (`seed = 42`):
- **Sampling Mechanism**: Uniform random sampling on the constrained simplex $[w_{\min}, w_{\max}]^N \cap \{\sum w_i = 1\}$ using Dirichlet and shifted simplex rejection sampling.
- **Strict Adherence**: Every generated portfolio satisfies $\sum w_i = 1.0$ and $w_{\min} \le w_i \le w_{\max}$.
- **Vectorized Evaluation**: Rapid computation of expected returns, volatilities, and Sharpe ratios across the entire matrix.

---

## 6. Institutional Disclosures & Guardrails

> [!IMPORTANT]
> **1. Non-Prediction Guarantee**:
> - Random feasible portfolios and optimization points represent historical descriptive mathematics derived from the selected historical sample.
> - They do **not** forecast future returns, cash flows, or economic conditions.

> [!NOTE]
> **2. Non-Ranking Principle**:
> - QuantLab presents optimal portfolios (Maximum Sharpe, Minimum Volatility, Equal Weight, User Portfolio) side-by-side for comparative study.
> - No portfolio is labeled "best", awarded an investment grade, or presented as financial advice.

> [!WARNING]
> **3. Overfitting & Covariance Sensitivity**:
> - Mean-variance optimizers are highly sensitive to estimation error in sample mean returns and covariance estimates.
> - Historical parameter optimizations should be analyzed in conjunction with Phase 8 Robustness testing and market regimes.

> [!CAUTION]
> **4. Bitcoin Calendar Alignment**:
> - Bitcoin processed data is available for calendar year 2017. Including Bitcoin in the universe automatically restricts common-date inner alignment to 2017 to avoid look-ahead bias or synthetic data fabrication.
