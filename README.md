# COM-QUANT: Commodities Quantitative Analysis Dashboard

COM-QUANT is a fully automated, serverless quantitative analysis platform designed for global commodities. The system operates on a daily schedule, autonomously fetching market data, executing a suite of quantitative forecasting models, calculating comprehensive risk metrics, and generating a highly interactive, static web dashboard. 

The application is hosted entirely on GitHub Pages, utilizing GitHub Actions as a compute engine to perform data engineering and modeling processes without the need for dedicated backend infrastructure.

**[https://chennakeshavadasa.github.io/COM-QUANT/](https://chennakeshavadasa.github.io/COM-QUANT/)**

---

## 1. System Architecture

The architecture of COM-QUANT is designed around a decoupled, serverless pipeline. The entire system is contained within the repository and runs on an automated daily cron schedule.

### 1.1. Data Pipeline
1. **Data Acquisition:** At 02:00 UTC daily, the Python engine (`src/engine.py`) initializes. It utilizes the `yfinance` library to download historical daily price data for ten major global commodities across three sectors: Precious Metals, Energy, and Agriculture.
2. **Quantitative Processing:** The engine applies a battery of statistical tests, technical indicators, and four distinct forecasting models to the historical data. 
3. **Serialization:** The resulting predictions, metrics, and metadata are serialized into a highly optimized JSON file (`multi_data.json`).
4. **Static Generation:** A second script (`src/build_dashboard.py`) parses the JSON output and injects it into a unified, standalone HTML document. This document leverages Plotly.js for client-side rendering.

### 1.2. CI/CD Infrastructure
The entire pipeline is orchestrated via GitHub Actions (`.github/workflows/update.yml`). The workflow provisions an Ubuntu environment, installs necessary scientific computing dependencies (`numpy`, `pandas`, `scipy`, `statsmodels`), executes the python scripts, and subsequently commits the mutated files back to the `main` branch. GitHub Pages detects this commit and automatically publishes the updated HTML document.

---

## 2. Quantitative Forecasting Models

The core of COM-QUANT is its ensemble forecasting engine. Because financial markets exhibit non-stationary, stochastic behavior, relying on a single deterministic model is sub-optimal. COM-QUANT generates forecasts using four distinct methodologies, subsequently blending them into an ensemble projection.

### 2.1. ARIMA (Auto-Regressive Integrated Moving Average)
**Conceptual Overview:** ARIMA models the future behavior of a time series based strictly on its own past values. It assumes that past patterns—specifically the correlation between current and past values—will persist.

**Mathematical Formulation:**
The model operates on the natural logarithm of the price to stabilize variance. An ARIMA(p,d,q) model is defined as:

```math
\phi_p(L)(1-L)^d \ln(S_t) = c + \theta_q(L)\varepsilon_t
```

Where:
* $S_t$ is the asset price at time $t$.
* $L$ is the lag operator ($L S_t = S_{t-1}$).
* $d$ is the degree of differencing required to achieve stationarity (COM-QUANT uses $d=1$, modeling daily returns).
* $\phi_p(L)$ is the autoregressive polynomial of order $p$.
* $\theta_q(L)$ is the moving average polynomial of order $q$.
* $\varepsilon_t$ is white noise error.

The algorithm performs a grid search across multiple $(p, d, q)$ combinations, selecting the model that minimizes the Akaike Information Criterion (AIC). Forecasts are transformed back to absolute price levels using the Jensen inequality correction.

### 2.2. Holt-Winters Exponential Smoothing
**Conceptual Overview:** Unlike ARIMA, Holt-Winters specifically isolates and models seasonality. It decomposes the time series into three distinct components: the baseline level, the overarching trend, and repeating seasonal cycles. This is particularly crucial for commodities, which are heavily influenced by seasonal physical supply and demand cycles (e.g., agricultural harvesting seasons).

**Mathematical Formulation:**
COM-QUANT utilizes the additive variant of the Holt-Winters method:

```math
\begin{align*}
\text{Level: } & L_t = \alpha(Y_t - S_{t-m}) + (1-\alpha)(L_{t-1} + T_{t-1}) \\
\text{Trend: } & T_t = \beta(L_t - L_{t-1}) + (1-\beta)T_{t-1} \\
\text{Seasonal: } & S_t = \gamma(Y_t - L_{t-1} - T_{t-1}) + (1-\gamma)S_{t-m}
\end{align*}
```

The forecast for $h$ periods ahead is calculated as:
```math
\hat{Y}_{t+h} = L_t + h T_t + S_{t+h-m}
```
Where $\alpha$, $\beta$, and $\gamma$ are smoothing parameters optimized via bounded minimization.

### 2.3. Monte Carlo Simulation (Geometric Brownian Motion)
**Conceptual Overview:** Monte Carlo simulation approaches forecasting through stochastic probability. Rather than calculating a single deterministic path, the engine simulates thousands of distinct, random future price trajectories based on the asset's historical drift (average return) and volatility. The median of these thousands of paths forms the baseline forecast, while the outer bounds form confidence intervals.

**Mathematical Formulation:**
The asset price is modeled using Geometric Brownian Motion (GBM):

```math
dS_t = \mu S_t dt + \sigma S_t dW_t
```

Discretized for daily simulation steps, the price at $t+1$ is calculated as:
```math
S_{t+1} = S_t \exp\left( \left(\mu - \frac{\sigma^2}{2}\right)\Delta t + \sigma \sqrt{\Delta t} Z \right)
```
Where:
* $\mu$ is the annualized expected return (drift).
* $\sigma$ is the annualized volatility.
* $\Delta t$ is the time step ($1/252$ for daily trading).
* $Z$ is a random variable drawn from a standard normal distribution $\mathcal{N}(0,1)$.

COM-QUANT simulates 5,000 independent paths. The reported forecast represents the 50th percentile (median) of the terminal distribution.

### 2.4. Ornstein-Uhlenbeck (OU) Process
**Conceptual Overview:** The Ornstein-Uhlenbeck process mathematically models mean reversion. Commodities fundamentally differ from equities; they cannot grow to infinity and are bounded by the physical costs of production and extraction. When prices deviate significantly from historical norms, economic forces generally pull them back. The OU process quantifies this "rubber band" effect.

**Mathematical Formulation:**
The continuous-time stochastic differential equation is defined as:

```math
dS_t = \theta(\mu_{eq} - S_t)dt + \sigma dW_t
```
Where:
* $\mu_{eq}$ is the long-term equilibrium mean.
* $\theta$ represents the rate of mean reversion (the velocity at which the price returns to the mean).
* $\sigma dW_t$ represents Brownian market noise.

COM-QUANT calculates the half-life of mean reversion as:
```math
t_{1/2} = \frac{\ln(2)}{\theta}
```
This metric explicitly defines the expected number of days required for the commodity to revert halfway back to its historical mean.

### 2.5. Ensemble Methodology
No single model is omnipotent. COM-QUANT calculates an ensemble forecast by taking a weighted average of the individual model outputs. The base weighting schema is:
* ARIMA: 30% (Trend focus)
* Holt-Winters: 30% (Seasonality focus)
* Monte Carlo Median: 25% (Stochastic focus)
* Ornstein-Uhlenbeck: 15% (Mean-reversion focus)

This unified ensemble provides the basis for the "Best Entry Window" and potential gain calculations featured on the dashboard.

---

## 3. Technical Analysis & Composite Scoring

In addition to pure mathematical forecasting, the engine computes an array of standard momentum and oscillator indicators:
* **Relative Strength Index (RSI):** Measures the velocity and magnitude of directional price movements.
* **MACD (Moving Average Convergence Divergence):** Identifies shifts in momentum via exponential moving average crossovers.
* **Bollinger Bands (%B):** Quantifies price relative to standard deviation bands.
* **Stochastic Oscillator & Williams %R:** Momentum indicators comparing closing prices to historical ranges.
* **Commodity Channel Index (CCI):** Measures deviation from the statistical mean.

These specific indicators are algorithmically normalized and aggregated into a proprietary 0-100 **Composite Score**, yielding a directional signal ranging from "Strong Bearish" to "Strong Bullish".

---

## 4. Risk Metrics & Statistical Analysis

Professional quantitative analysis requires rigorous risk assessment. COM-QUANT computes:

* **Value at Risk (VaR):** Uses historical simulation to define the maximum expected loss over a specific timeframe at 95% and 99% confidence intervals.
* **Conditional VaR (CVaR):** Calculates the expected shortfall (the average loss expected if the VaR threshold is breached).
* **Maximum Drawdown:** Identifies the largest historical peak-to-trough drop in value.
* **Hurst Exponent:** Determines the autocorrelation of the time series. A Hurst exponent of 0.5 indicates a random walk, $H > 0.5$ indicates a trending market, and $H < 0.5$ indicates a mean-reverting market.
* **Augmented Dickey-Fuller (ADF) Test:** A formal statistical test for stationarity.

---

## 5. Repository Structure

* `src/engine.py`: The quantitative analytics engine. Handles data ingestion, mathematical modeling, indicator calculation, and JSON serialization.
* `src/build_dashboard.py`: The static site generator. Parses the JSON output and dynamically constructs the HTML/CSS/JS frontend.
* `docs/`: Contains the original architectural prompts and documentation used to design the system.
* `.github/workflows/update.yml`: The GitHub Actions CI/CD configuration file controlling the scheduled automation.
* `multi_data.json`: The raw serialized output of the quantitative engine (generated dynamically).
* `index.html`: The final, distributable frontend dashboard (generated dynamically).

---

## 6. Deployment Guide

The repository is designed to be forked and deployed with zero configuration changes.

1. **Enable GitHub Pages:**
   * Navigate to the forked repository's **Settings > Pages**.
   * Under "Source", select **Deploy from a branch**.
   * Select the `main` branch and the `/ (root)` folder. Save the configuration.
2. **Initialize the Automated Pipeline:**
   * Navigate to the **Actions** tab.
   * Enable workflows if prompted by the GitHub interface.
   * Select the **Daily COM-QUANT Update** workflow from the left sidebar.
   * Click the **Run workflow** button to execute the initial build.
3. **Verification:**
   * Upon successful execution of the workflow, GitHub Pages will automatically publish the static site.
   * The live dashboard will be accessible at `https://<your-username>.github.io/COM-QUANT/`.
