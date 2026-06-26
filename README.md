# COM-QUANT: Commodities Quantitative Analysis Dashboard

COM-QUANT is a fully automated, serverless dashboard for quantitative analysis of global commodities. Every single day, the system fetches fresh market data, runs complex forecasting models, generates technical signals, and builds a comprehensive visual dashboard—all powered automatically by GitHub Actions and GitHub Pages.

**[View the Live Dashboard Here](https://chennakeshavadasa.github.io/COM-QUANT/)**

---

## 🎯 What Does This Project Do?

For anyone trading or following commodities (like Gold, Oil, or Wheat), making informed decisions requires analyzing a lot of data. COM-QUANT acts as an automated quantitative researcher. 

Every day before the markets open, it:
1. **Downloads** the latest historical price data for 10 major commodities.
2. **Analyzes** the data using statistical tests, technical indicators, and risk metrics.
3. **Forecasts** future price movements across different time horizons (1 week to 6 months) using an ensemble of four advanced mathematical models.
4. **Builds** a static, lightning-fast website so you can view the results from anywhere.

The best part? **There is no server.** The entire system is driven by a free GitHub Actions workflow that runs a Python script, bakes the results into a single HTML file, and hosts it for free on GitHub Pages.

---

## 🧠 The Forecasting Models (Simple & Math Explanations)

COM-QUANT uses an "Ensemble" approach. This means it doesn't rely on just one model to predict the future; it runs four different models and averages them together (with specific weights) to create a more robust "Best Entry" prediction.

### 1. ARIMA (Auto-Regressive Integrated Moving Average) - *30% Weight*
**The Simple Explanation:** 
ARIMA looks at the asset's past behavior and assumes that past patterns will continue. It asks: "Based on the recent trend and how prices have bounced around that trend, where is the price likely to go next?"

**The Mathematical Explanation:**
ARIMA(p,d,q) models a time series linearly. COM-QUANT works in log-price space to stabilize variance.
$$ \phi(B)(1-B)^d \ln(S_t) = \theta(B)\varepsilon_t $$
- **p (Auto-Regressive):** How many past days influence today ($ \phi $).
- **d (Integrated):** Differencing to make the series stationary (we use $ d=1 $, meaning we model daily returns).
- **q (Moving Average):** How past forecasting errors influence today ($ \theta $).
*We grid-search the best parameters minimizing the Akaike Information Criterion (AIC). Forecasts are back-transformed using the Jensen inequality correction:* $ E[S] \approx \exp(\mu_{fc} + \sigma^2_{fc} / 2) $.

### 2. Holt-Winters Exponential Smoothing - *30% Weight*
**The Simple Explanation:**
While ARIMA is great at raw trends, Holt-Winters is the master of **seasonality**. It breaks the price down into three components: the base price (level), the direction it's moving (trend), and repeating cycles (seasonality). For example, natural gas often spikes in winter; this model captures that.

**The Mathematical Explanation:**
We use Additive Trend and Additive Seasonality.
- **Level ($ \ell_t $):** $ \alpha(y_t - s_{t-m}) + (1-\alpha)(\ell_{t-1} + b_{t-1}) $
- **Trend ($ b_t $):** $ \beta(\ell_t - \ell_{t-1}) + (1-\beta)b_{t-1} $
- **Seasonal ($ s_t $):** $ \gamma(y_t - \ell_{t-1} - b_{t-1}) + (1-\gamma)s_{t-m} $
- **Forecast:** $ \hat{y}_{t+h} = \ell_t + h b_t + s_{t+h-m} $

### 3. Monte Carlo Simulations - *25% Weight*
**The Simple Explanation:**
Instead of drawing one line into the future, Monte Carlo explores thousands of alternate universes. It takes the commodity's average daily return and its typical volatility, and rolls a pair of dice thousands of times to simulate 5,000 possible future price paths. We take the median (the middle) of these 5,000 paths as the forecast.

**The Mathematical Explanation:**
Prices are simulated using Geometric Brownian Motion (GBM):
$$ S_{t+1} = S_t \exp\left( \left(\mu - \frac{\sigma^2}{2}\right)\Delta t + \sigma \sqrt{\Delta t} Z \right) $$
Where $ \mu $ is the annualized drift, $ \sigma $ is the annualized volatility, $ \Delta t = 1/252 $ (one trading day), and $ Z \sim N(0,1) $ is a random draw from a standard normal distribution.

### 4. Ornstein-Uhlenbeck (OU) Process - *15% Weight*
**The Simple Explanation:**
This model captures the concept of **Mean Reversion**. Unlike stocks, which can grow infinitely, commodities are tied to the physical world (cost of mining gold, cost of pumping oil). If oil gets too expensive, drillers pump more, and the price drops. If it gets too cheap, they stop pumping, and the price rises. The OU process mathematically pulls the forecast back toward its historical average.

**The Mathematical Explanation:**
The OU process is defined by the stochastic differential equation:
$$ dS_t = \theta(\mu_{eq} - S_t)dt + \sigma dW_t $$
Where:
- $ \mu_{eq} $: The long-term equilibrium mean.
- $ \theta $: The speed of mean reversion (how fast the rubber band snaps back).
- $ \sigma dW_t $: The random market noise (Brownian motion).
*Parameters are estimated using Ordinary Least Squares (OLS) regression on the discrete daily price changes.*

---

## 📊 Technical Indicators & Risk Metrics

COM-QUANT computes an array of metrics to gauge market health:
- **RSI, MACD, Bollinger Bands, Stochastic, Williams %R, CCI:** Standard technical indicators rolled into a unified 0-100 **Composite Score** (Bearish to Bullish).
- **Hurst Exponent:** Determines the market regime (Is the market trending, mean-reverting, or random walking?).
- **Value at Risk (VaR) & Conditional VaR (CVaR):** The maximum expected loss on a worst-case day.
- **Sharpe & Sortino Ratios:** Measures risk-adjusted returns (how much reward you get for the volatility you endure).
- **Cross-Commodity Spreads:** Tracks macro relationships like the Gold/Silver ratio and the Brent/WTI oil spread.

---

## 🛠️ Repository Structure

* `src/engine.py` — The heavy lifter. Downloads data from Yahoo Finance, runs all mathematical models, and outputs `multi_data.json`.
* `src/build_dashboard.py` — The builder. Reads the JSON data and injects it into a highly styled, standalone `index.html` file using Plotly for charts.
* `docs/` — Contains the prompt files used to define the system's architecture and logic.
* `.github/workflows/update.yml` — The automation script that wakes up daily, runs the Python scripts, and saves the new data.

---

## 🚀 Setup for Forking

If you fork this repository, you can get your own automated dashboard running in 2 minutes:

1. **Enable GitHub Pages:**
   * Go to your repository **Settings > Pages**.
   * Under Source, select **Deploy from a branch**.
   * Select the `main` branch and the `/ (root)` folder. Save.
2. **Trigger the First Run:**
   * Go to the **Actions** tab in your repository.
   * Click the green "I understand my workflows, go ahead and enable them" button.
   * Click **Daily COM-QUANT Update** on the left menu.
   * Click **Run workflow** on the right.
3. Wait ~2 minutes. Your dashboard will be live at `https://<your-username>.github.io/COM-QUANT/`!