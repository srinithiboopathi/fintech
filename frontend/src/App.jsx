import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [asset, setAsset] = useState("nvidia");
  const [strategy, setStrategy] = useState("sma");
  const [initialCapital, setInitialCapital] = useState(100000);
  const [transactionCost, setTransactionCost] = useState(0.001);

  const [marketOverview, setMarketOverview] = useState(null);
  const [marketLoading, setMarketLoading] = useState(false);
  const [marketError, setMarketError] = useState("");

  const [priceData, setPriceData] = useState(null);
  const [priceLoading, setPriceLoading] = useState(false);
  const [priceError, setPriceError] = useState("");

  const [correlation, setCorrelation] = useState(null);
  const [correlationLoading, setCorrelationLoading] = useState(false);
  const [correlationError, setCorrelationError] = useState("");

  const [comparison, setComparison] = useState(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState("");

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadMarketOverview();
  }, []);

  useEffect(() => {
    loadPriceData();
  }, [asset]);

  const loadMarketOverview = async () => {
    setMarketLoading(true);
    setMarketError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/market/overview"
      );

      if (!response.ok) {
        throw new Error("Market overview request failed");
      }

      const data = await response.json();
      setMarketOverview(data);
    } catch (err) {
      setMarketError("Could not load market overview.");
    } finally {
      setMarketLoading(false);
    }
  };

  const loadPriceData = async () => {
    setPriceLoading(true);
    setPriceError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/market/${asset}?limit=200`
      );

      if (!response.ok) {
        throw new Error("Price data request failed");
      }

      const data = await response.json();
      setPriceData(data);
    } catch (err) {
      setPriceError("Could not load historical price data.");
    } finally {
      setPriceLoading(false);
    }
  };

  const loadCorrelation = async () => {
    setCorrelationLoading(true);
    setCorrelationError("");

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/market/correlation"
      );

      if (!response.ok) {
        throw new Error("Correlation request failed");
      }

      const data = await response.json();
      setCorrelation(data);
    } catch (err) {
      setCorrelationError("Could not load correlation data.");
    } finally {
      setCorrelationLoading(false);
    }
  };

  const compareStrategies = async () => {
    setComparisonLoading(true);
    setComparisonError("");
    setComparison(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/backtest/compare",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            asset,
            initial_capital: Number(initialCapital),
            transaction_cost: Number(transactionCost),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Strategy comparison request failed");
      }

      const data = await response.json();
      setComparison(data);
    } catch (err) {
      setComparisonError(
        "Could not compare strategies."
      );
    } finally {
      setComparisonLoading(false);
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/backtest/run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            asset,
            strategy,
            initial_capital: Number(initialCapital),
            transaction_cost: Number(transactionCost),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Backtest request failed");
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(
        "Could not connect to backend. Make sure the FastAPI server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const getPricePoints = () => {
    if (!priceData?.data) {
      return [];
    }

    return priceData.data
      .map((item) => ({
        date: item.Date,
        price: Number(item.Close),
      }))
      .filter(
        (item) =>
          item.date &&
          Number.isFinite(item.price)
      );
  };

  const renderPriceChart = () => {
    const points = getPricePoints();

    if (points.length < 2) {
      return (
        <div className="chart-empty">
          Historical price data unavailable.
        </div>
      );
    }

    const values = points.map((point) => point.price);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    const chartWidth = 1000;
    const chartHeight = 350;
    const paddingX = 20;
    const paddingTop = 25;
    const paddingBottom = 30;

    const usableWidth = chartWidth - paddingX * 2;
    const usableHeight =
      chartHeight - paddingTop - paddingBottom;

    const coordinates = points
      .map((point, index) => {
        const x =
          paddingX +
          (index / (points.length - 1)) *
            usableWidth;

        const y =
          paddingTop +
          (1 - (point.price - min) / range) *
            usableHeight;

        return `${x},${y}`;
      })
      .join(" ");

    const firstDate = new Date(points[0].date);
    const lastDate = new Date(
      points[points.length - 1].date
    );

    return (
      <>
        <div className="price-chart-info">
          <div>
            <span>Period</span>
            <strong>
              {firstDate.toLocaleDateString()} —{" "}
              {lastDate.toLocaleDateString()}
            </strong>
          </div>

          <div>
            <span>Latest</span>
            <strong>
              $
              {points[
                points.length - 1
              ].price.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </strong>
          </div>
        </div>

        <div className="chart">
          <svg
            viewBox="0 0 1000 350"
            preserveAspectRatio="none"
            className="equity-svg"
          >
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              points={coordinates}
            />
          </svg>
        </div>
      </>
    );
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>QuantLab</h1>
          <p>
            Quantitative Multi-Asset Financial Intelligence Platform
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          System Ready
        </div>
      </header>

      <main className="dashboard">
        <section className="market-section">
          <div className="section-heading">
            <div>
              <h2>Market Overview</h2>
              <p>
                Latest prices from the historical market datasets.
              </p>
            </div>

            <button
              className="refresh-button"
              onClick={loadMarketOverview}
              disabled={marketLoading}
            >
              {marketLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {marketError && (
            <div className="error">{marketError}</div>
          )}

          {marketOverview && (
            <div className="market-grid">
              {marketOverview.assets.map((item) => {
                const isPositive = item.daily_change >= 0;

                return (
                  <div
                    className="market-card"
                    key={item.asset}
                  >
                    <div className="market-card-top">
                      <span className="market-asset">
                        {item.asset}
                      </span>

                      <span
                        className={
                          isPositive
                            ? "market-change positive"
                            : "market-change negative"
                        }
                      >
                        {isPositive ? "+" : ""}
                        {(
                          item.daily_change * 100
                        ).toFixed(2)}
                        %
                      </span>
                    </div>

                    <div className="market-price">
                      $
                      {item.latest_price.toLocaleString(
                        undefined,
                        {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        }
                      )}
                    </div>

                    <div className="market-meta">
                      <span>Previous</span>
                      <strong>
                        $
                        {item.previous_price.toLocaleString(
                          undefined,
                          {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          }
                        )}
                      </strong>
                    </div>

                    <div className="market-meta">
                      <span>Data date</span>
                      <strong>{item.date}</strong>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="price-card">
          <div className="price-header">
            <div>
              <h2>
                {asset.toUpperCase()} Historical Price
              </h2>

              <p>
                Real historical closing prices from the
                selected dataset.
              </p>
            </div>

            <button
              className="refresh-button"
              onClick={loadPriceData}
              disabled={priceLoading}
            >
              {priceLoading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {priceError && (
            <div className="error">{priceError}</div>
          )}

          {priceLoading && !priceData && (
            <div className="chart-empty">
              Loading historical price data...
            </div>
          )}

          {priceData && renderPriceChart()}
        </section>

        <section className="hero-card">
          <h2>Backtest Your Strategy</h2>

          <p>
            Test quantitative trading strategies using real
            historical market data.
          </p>

          <div className="controls">
            <div className="control">
              <label>Asset</label>

              <select
                value={asset}
                onChange={(e) =>
                  setAsset(e.target.value)
                }
              >
                <option value="nvidia">NVIDIA</option>
                <option value="bitcoin">Bitcoin</option>
                <option value="gold">Gold</option>
              </select>
            </div>

            <div className="control">
              <label>Strategy</label>

              <select
                value={strategy}
                onChange={(e) =>
                  setStrategy(e.target.value)
                }
              >
                <option value="sma">
                  SMA Crossover
                </option>
                <option value="ema">
                  EMA Trend
                </option>
              </select>
            </div>

            <div className="control">
              <label>Initial Capital</label>

              <select
                value={initialCapital}
                onChange={(e) =>
                  setInitialCapital(
                    Number(e.target.value)
                  )
                }
              >
                <option value={50000}>$50,000</option>
                <option value={100000}>$100,000</option>
                <option value={250000}>$250,000</option>
                <option value={500000}>$500,000</option>
              </select>
            </div>

            <div className="control">
              <label>Transaction Cost</label>

              <select
                value={transactionCost}
                onChange={(e) =>
                  setTransactionCost(
                    Number(e.target.value)
                  )
                }
              >
                <option value={0}>0.00%</option>
                <option value={0.0005}>0.05%</option>
                <option value={0.001}>0.10%</option>
                <option value={0.0025}>0.25%</option>
                <option value={0.005}>0.50%</option>
              </select>
            </div>

            <button
              onClick={runBacktest}
              disabled={loading}
            >
              {loading ? "Running..." : "Run Backtest"}
            </button>
          </div>
        </section>

        <section className="comparison-card">
          <div className="comparison-header">
            <div>
              <h2>Strategy Comparison</h2>
              <p>
                Compare SMA and EMA using the same asset,
                capital, and transaction cost.
              </p>
            </div>

            <button
              className="comparison-button"
              onClick={compareStrategies}
              disabled={comparisonLoading}
            >
              {comparisonLoading
                ? "Comparing..."
                : "Compare Strategies"}
            </button>
          </div>

          {comparisonError && (
            <div className="error">
              {comparisonError}
            </div>
          )}

          {comparison && (
            <div className="comparison-table-wrapper">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>SMA</th>
                    <th>EMA</th>
                  </tr>
                </thead>

                <tbody>
                  <tr>
                    <th>Final Portfolio</th>
                    <td>
                      $
                      {comparison.strategies[0].final_portfolio_value.toFixed(
                        2
                      )}
                    </td>
                    <td>
                      $
                      {comparison.strategies[1].final_portfolio_value.toFixed(
                        2
                      )}
                    </td>
                  </tr>

                  <tr>
                    <th>Total Return</th>
                    <td>
                      {(
                        comparison.strategies[0]
                          .total_return * 100
                      ).toFixed(2)}
                      %
                    </td>
                    <td>
                      {(
                        comparison.strategies[1]
                          .total_return * 100
                      ).toFixed(2)}
                      %
                    </td>
                  </tr>

                  <tr>
                    <th>Max Drawdown</th>
                    <td>
                      {(
                        comparison.strategies[0]
                          .maximum_drawdown * 100
                      ).toFixed(2)}
                      %
                    </td>
                    <td>
                      {(
                        comparison.strategies[1]
                          .maximum_drawdown * 100
                      ).toFixed(2)}
                      %
                    </td>
                  </tr>

                  <tr>
                    <th>Volatility</th>
                    <td>
                      {(
                        comparison.strategies[0]
                          .annualized_volatility * 100
                      ).toFixed(2)}
                      %
                    </td>
                    <td>
                      {(
                        comparison.strategies[1]
                          .annualized_volatility * 100
                      ).toFixed(2)}
                      %
                    </td>
                  </tr>

                  <tr>
                    <th>Sharpe Ratio</th>
                    <td>
                      {comparison.strategies[0].sharpe_ratio.toFixed(
                        2
                      )}
                    </td>
                    <td>
                      {comparison.strategies[1].sharpe_ratio.toFixed(
                        2
                      )}
                    </td>
                  </tr>

                  <tr>
                    <th>Trades</th>
                    <td>
                      {comparison.strategies[0].trade_count}
                    </td>
                    <td>
                      {comparison.strategies[1].trade_count}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="correlation-card">
          <div className="correlation-header">
            <div>
              <h2>Cross-Asset Correlation</h2>

              <p>
                Measure how Gold, Bitcoin, and NVIDIA move
                relative to each other.
              </p>
            </div>

            <button
              className="correlation-button"
              onClick={loadCorrelation}
              disabled={correlationLoading}
            >
              {correlationLoading
                ? "Loading..."
                : "Load Correlation"}
            </button>
          </div>

          {correlationError && (
            <div className="error">
              {correlationError}
            </div>
          )}

          {correlation && (
            <div className="correlation-table-wrapper">
              <table className="correlation-table">
                <thead>
                  <tr>
                    <th>Asset</th>

                    {correlation.assets.map(
                      (assetName) => (
                        <th key={assetName}>
                          {assetName}
                        </th>
                      )
                    )}
                  </tr>
                </thead>

                <tbody>
                  {correlation.matrix.map((row) => (
                    <tr key={row.asset}>
                      <th>{row.asset}</th>

                      {correlation.assets.map(
                        (assetName) => {
                          const value =
                            row[assetName];

                          return (
                            <td
                              key={assetName}
                              className={
                                value === null
                                  ? ""
                                  : value > 0.5
                                    ? "correlation-positive"
                                    : value < -0.5
                                      ? "correlation-negative"
                                      : "correlation-neutral"
                              }
                            >
                              {value === null
                                ? "N/A"
                                : value.toFixed(2)}
                            </td>
                          );
                        }
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!correlation &&
            !correlationLoading &&
            !correlationError && (
              <div className="correlation-empty">
                Click "Load Correlation" to calculate the
                matrix from the real historical datasets.
              </div>
            )}
        </section>

        {error && (
          <div className="error">{error}</div>
        )}

        {results && (
          <>
            <section className="metrics-grid">
              <div className="metric-card">
                <span>Final Portfolio</span>
                <strong>
                  $
                  {results.final_portfolio_value?.toFixed(
                    2
                  )}
                </strong>
              </div>

              <div className="metric-card">
                <span>Total Return</span>
                <strong>
                  {(
                    results.total_return * 100
                  )?.toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric-card">
                <span>Max Drawdown</span>
                <strong>
                  {(
                    results.maximum_drawdown * 100
                  )?.toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric-card">
                <span>Sharpe Ratio</span>
                <strong>
                  {results.sharpe_ratio?.toFixed(2)}
                </strong>
              </div>

              <div className="metric-card">
                <span>Annual Volatility</span>
                <strong>
                  {(
                    results.annualized_volatility *
                    100
                  )?.toFixed(2)}
                  %
                </strong>
              </div>

              <div className="metric-card">
                <span>Trades</span>
                <strong>
                  {results.trade_count}
                </strong>
              </div>
            </section>

            <section className="chart-card">
              <div className="chart-header">
                <div>
                  <h2>Equity Curve</h2>
                  <p>
                    Portfolio value throughout the
                    backtest
                  </p>
                </div>

                <div className="chart-value">
                  $
                  {results.final_portfolio_value?.toFixed(
                    0
                  )}
                </div>
              </div>

              <div className="chart">
                {results.equity_curve?.length > 1 && (
                  <svg
                    viewBox="0 0 1000 350"
                    preserveAspectRatio="none"
                    className="equity-svg"
                  >
                    <polyline
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      points={results.equity_curve
                        .map((point, index) => {
                          const values =
                            results.equity_curve.map(
                              (item) => item.value
                            );

                          const min =
                            Math.min(...values);
                          const max =
                            Math.max(...values);

                          const x =
                            (index /
                              (results.equity_curve
                                .length -
                                1)) *
                            1000;

                          const range =
                            max - min || 1;

                          const y =
                            320 -
                            ((point.value - min) /
                              range) *
                              280;

                          return `${x},${y}`;
                        })
                        .join(" ")}
                    />
                  </svg>
                )}

                {(!results.equity_curve ||
                  results.equity_curve.length <=
                    1) && (
                  <div className="chart-empty">
                    Equity curve data unavailable.
                  </div>
                )}
              </div>
            </section>

            <section className="result-card">
              <h2>Backtest Summary</h2>

              <div className="summary-row">
                <span>Asset</span>
                <strong>
                  {results.asset.toUpperCase()}
                </strong>
              </div>

              <div className="summary-row">
                <span>Strategy</span>
                <strong>{results.strategy}</strong>
              </div>

              <div className="summary-row">
                <span>Initial Capital</span>
                <strong>
                  $
                  {results.initial_capital?.toFixed(
                    2
                  )}
                </strong>
              </div>

              <div className="summary-row">
                <span>Transaction Cost</span>
                <strong>
                  {(transactionCost * 100).toFixed(
                    2
                  )}
                  %
                </strong>
              </div>

              <div className="summary-row">
                <span>Number of Trades</span>
                <strong>
                  {results.trade_count}
                </strong>
              </div>
            </section>

            <section className="trades-card">
              <div className="trades-header">
                <div>
                  <h2>Trade History</h2>
                  <p>
                    Transactions generated by the
                    strategy
                  </p>
                </div>

                <span className="trade-count">
                  {results.trades?.length || 0} trades
                </span>
              </div>

              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Action</th>
                      <th>Price</th>
                      <th>Quantity</th>
                      <th>Transaction Cost</th>
                      <th>Portfolio Value</th>
                    </tr>
                  </thead>

                  <tbody>
                    {results.trades?.map(
                      (trade, index) => (
                        <tr key={index}>
                          <td>
                            {new Date(
                              trade.date
                            ).toLocaleDateString()}
                          </td>

                          <td>
                            <span
                              className={
                                trade.action
                                  ?.toLowerCase()
                                  .includes("buy")
                                  ? "buy"
                                  : "sell"
                              }
                            >
                              {trade.action}
                            </span>
                          </td>

                          <td>
                            $
                            {trade.price?.toFixed(
                              2
                            )}
                          </td>

                          <td>
                            {trade.quantity?.toFixed(
                              4
                            )}
                          </td>

                          <td>
                            $
                            {trade.transaction_cost?.toFixed(
                              2
                            )}
                          </td>

                          <td>
                            $
                            {trade.portfolio_value?.toFixed(
                              2
                            )}
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;