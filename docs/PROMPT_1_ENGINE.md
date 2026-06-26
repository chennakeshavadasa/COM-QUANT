# TASK FOR GEMINI
# Read this entire file carefully and implement exactly what is described.
# Output file : engine.py
# Save to     : current working directory (COM-QUANT/)
# Run test    : python engine.py  →  should produce multi_data.json with no errors

---

## CONTEXT

You are building `engine.py` for COM-QUANT — a static commodities quantitative analysis
dashboard served on GitHub Pages (no server). This script downloads 10 commodity prices
from Yahoo Finance, runs 4 forecasting models + full quant analytics for each, and writes
everything to `multi_data.json`. A companion script (`build_dashboard.py`) will later read
that JSON and bake it into `index.html`. GitHub Actions runs this daily at 2 AM UTC.

---

## DEPENDENCIES

```
pip install yfinance numpy pandas scipy statsmodels scikit-learn
```
Import at top: `yfinance, numpy as np, pandas as pd, scipy, statsmodels, sklearn, json, sys, datetime, warnings, time`

---

## COMMODITY UNIVERSE

```python
COMMODITIES = {
    "GOLD":      {"ticker": "GC=F", "name": "Gold",          "unit": "USD/troy oz", "category": "precious_metals"},
    "SILVER":    {"ticker": "SI=F", "name": "Silver",        "unit": "USD/troy oz", "category": "precious_metals"},
    "PLATINUM":  {"ticker": "PL=F", "name": "Platinum",      "unit": "USD/troy oz", "category": "precious_metals"},
    "PALLADIUM": {"ticker": "PA=F", "name": "Palladium",     "unit": "USD/troy oz", "category": "precious_metals"},
    "WTI":       {"ticker": "CL=F", "name": "WTI Crude Oil", "unit": "USD/barrel",  "category": "energy"},
    "BRENT":     {"ticker": "BZ=F", "name": "Brent Crude",   "unit": "USD/barrel",  "category": "energy"},
    "NATGAS":    {"ticker": "NG=F", "name": "Natural Gas",   "unit": "USD/MMBtu",   "category": "energy"},
    "WHEAT":     {"ticker": "ZW=F", "name": "Wheat",         "unit": "USD/bushel",  "category": "agriculture"},
    "CORN":      {"ticker": "ZC=F", "name": "Corn",          "unit": "USD/bushel",  "category": "agriculture"},
    "SOYBEAN":   {"ticker": "ZS=F", "name": "Soybean",       "unit": "USD/bushel",  "category": "agriculture"},
}

CATEGORIES = {
    "precious_metals": ["GOLD", "SILVER", "PLATINUM", "PALLADIUM"],
    "energy":          ["WTI", "BRENT", "NATGAS"],
    "agriculture":     ["WHEAT", "CORN", "SOYBEAN"],
}

DXY_PROXY_TICKER = "EURUSD=X"  # invert sign: EUR/USD is ~inverse of DXY

MODEL_WEIGHTS = {"arima": 0.30, "holt_winters": 0.30, "monte_carlo": 0.25, "ou_process": 0.15}
```

---

## FORECAST WINDOWS

```python
WINDOWS = {
    "1W": {"forecast_days": 7,   "lookback_days": 180, "display_days": 7},
    "2W": {"forecast_days": 14,  "lookback_days": 365, "display_days": 14},
    "1M": {"forecast_days": 30,  "lookback_days": 365, "display_days": 30},
    "3M": {"forecast_days": 90,  "lookback_days": 730, "display_days": 90},
    "6M": {"forecast_days": 180, "lookback_days": 730, "display_days": 180},
}
```

---

## FUNCTIONS TO IMPLEMENT (in order)

### 1. `json_safe(obj)`
Recursively convert the entire output dict to JSON-serializable types before `json.dump`.
- `float('nan')`, `float('inf')`, `float('-inf')`, `np.nan` → `None`
- `np.float64`, `np.float32` → Python `float`
- `np.int64`, `np.int32` → Python `int`
- `np.ndarray` → `.tolist()`
- Recurse into `dict` and `list`

---

### 2. `download_data(ticker, lookback_days) → pd.DataFrame | None`
- Download via `yfinance.download(ticker, period=f"{lookback_days}d", auto_adjust=True)`
- Retry up to 3 times with 2s sleep between attempts on failure
- Flatten multi-level columns: `df.columns = df.columns.get_level_values(0)`
- Forward-fill all NaN (weekends, contract rollovers, holidays)
- Return DataFrame with DatetimeIndex and columns: `Open, High, Low, Close, Volume`
- Return `None` if all retries fail; print error to stderr
- **CRITICAL for grains**: ZW=F, ZC=F, ZS=F quote in cents/bushel. If `Close.iloc[-1] > 2000`,
  divide all price columns (Open, High, Low, Close) by 100 to get USD/bushel.

---

### 3. `fit_arima(prices, forecast_days) → dict`
**Math:**
```
φ(B)(1-B)^d ln(S_t) = θ(B)ε_t
```
- Work in log-price space
- Grid-search: `p ∈ {0,1,2,3}`, `d=1` always, `q ∈ {0,1,2,3}` → select min AIC
- Use `statsmodels.tsa.arima.model.ARIMA`; suppress all convergence warnings with `warnings.filterwarnings('ignore')`
- Forecast `forecast_days` steps, get 95% confidence intervals from `get_forecast().conf_int()`
- Back-transform with Jensen correction: `E[S] ≈ exp(μ_fc + σ²_fc / 2)`
- On any exception return: `{"forecast": [None]*n, "ci_lower": [None]*n, "ci_upper": [None]*n, "order": (1,1,1), "aic": None}`

**Return:**
```python
{"forecast": [...], "ci_lower": [...], "ci_upper": [...], "order": (p,1,q), "aic": float}
```

---

### 4. `fit_holt_winters(prices, forecast_days) → dict`
**Math:**
```
Level:    ℓ_t = α(y_t / s_{t-m}) + (1-α)(ℓ_{t-1} + b_{t-1})
Trend:    b_t = β(ℓ_t - ℓ_{t-1}) + (1-β)b_{t-1}
Seasonal: s_t = γ(y_t / ℓ_t) + (1-γ)s_{t-m}
Forecast: ŷ_{t+h} = (ℓ_t + h·b_t) · s_{t+h-m}
```
- Use `statsmodels.tsa.holtwinters.ExponentialSmoothing`
- `trend='add'`, `seasonal='add'`, `initialization_method='estimated'`
- `seasonal_periods = 5` if `forecast_days <= 14` else `22`
- If fitting fails, fall back to additive-trend-only (no seasonal)
- On total failure return: `{"forecast": [None]*n, "alpha": None, "beta": None, "gamma": None}`

**Return:**
```python
{"forecast": [...], "alpha": float, "beta": float, "gamma": float}
```

---

### 5. `fit_monte_carlo(prices, forecast_days, n_sims=5000) → dict`
**Math (Geometric Brownian Motion):**
```
r_t   = ln(S_t / S_{t-1})
σ     = std(r_t) × √252        [annualized volatility]
μ_ann = mean(r_t) × 252 + σ²/2 [annualized drift, Jensen-corrected]

Each daily step (Δt = 1/252):
S_{t+1} = S_t × exp[(μ_ann - σ²/2)/252  +  σ/√252 × Z],  Z ~ N(0,1)
```
- Run `n_sims` paths, each `forecast_days` steps
- At each future day compute: `p5, p25, p50, p75, p95` across all simulations

**Return:**
```python
{"p5": [...], "p25": [...], "p50": [...], "p75": [...], "p95": [...], "mu": float, "sigma": float}
```

---

### 6. `fit_ou_process(prices, forecast_days, n_sims=1000) → dict`
**This is NEW vs FOREX_QUANT. Commodities mean-revert to production costs.**

**Math (Ornstein-Uhlenbeck):**
```
Continuous SDE:  dS_t = θ(μ_eq - S_t)dt + σ dW_t

Parameter estimation via OLS on the discrete form:
  ΔS_t = α + β·S_{t-1} + ε_t
  → θ    = -β̂ / Δt    (Δt = 1/252)
  → μ_eq = -α̂ / β̂
  → σ    = std(OLS residuals) / √Δt

Discrete simulation (daily):
  S_{t+1} = S_t + θ(μ_eq - S_t)/252 + σ/√252 × ε,   ε ~ N(0,1)

half_life_days = ln(2) / θ × 252
```

**Bounds/clipping:**
- Clip `θ` to `[0.001, 50]`
- Clip `μ_eq` to `[0.1 × current_price, 10 × current_price]`
- Clip `σ` to `[1e-4, current_price × 0.5]`
- Clip each simulated value to `[0.001, 10 × current_price]`
- **NATGAS extra clip:** no simulated value > `5 × current_price`
- Forecast = median path across `n_sims` simulations at each future step

**On any exception return:**
```python
{"forecast": [None]*n, "theta": None, "mu_eq": None, "sigma": None, "half_life_days": None}
```

**Return:**
```python
{"forecast": [...], "theta": float, "mu_eq": float, "sigma": float, "half_life_days": float}
```

---

### 7. `compute_ensemble(arima_fc, hw_fc, mc_p50, ou_fc, weights) → list`
- Weighted average: `0.30×arima + 0.30×hw + 0.25×mc_p50 + 0.15×ou`
- At each step, if some values are `None`, average the non-None ones proportionally
- If all are `None` at a step, return `None`

---

### 8. `find_optimal_entry(ensemble, forecast_dates, current_price) → dict`
- Find the index with the lowest non-None ensemble value (best buy entry)
- Return dict:
```python
{
    "optimal_date": "YYYY-MM-DD",
    "optimal_price": float,
    "optimal_horizon_days": int,
    "potential_gain_pct": float  # abs(current - optimal) / current * 100
}
```

---

### 9. `compute_technical_indicators(close, high=None, low=None) → dict`
Run on full close array (not just display window).

**RSI(14):**
```
avg_gain_14 / avg_loss_14 → RSI = 100 - 100/(1 + ratio). Clip to [0, 100].
```

**MACD(12, 26, 9):**
```
EMA12 - EMA26 = MACD line
EMA9(MACD) = signal line
histogram = MACD - signal
```

**Bollinger(20, 2σ):**
```
SMA20 ± 2σ → upper, lower
%B = (close[-1] - lower) / (upper - lower). Clip to [-0.5, 1.5].
```

**Stochastic(14, 3):**
```
%K = (close[-1] - min14) / (max14 - min14) * 100
%D = SMA3(%K). Clip to [0, 100].
```

**Williams %R(14):**
```
(max14 - close[-1]) / (max14 - min14) * -100. Range [-100, 0].
```

**ATR(14):** If high/low available use true range; else use `|close[t] - close[t-1]|` as proxy.

**CCI(20):**
```
(close[-1] - SMA20) / (0.015 × mean_absolute_deviation_20)
```

**Z-Score(20d):**
```
(close[-1] - SMA20) / std20
```

**Composite score (0–100):** Average of these 7 indicator scores (exclude ATR from composite):
| Indicator | Score mapping |
|-----------|--------------|
| RSI | <30→85, 30-50→65, 50-70→35, >70→15 |
| MACD hist>0 AND MACD>signal | →75; MACD>signal only→55; else→30 |
| %B | <0.2→80, 0.2-0.4→65, 0.4-0.6→50, 0.6-0.8→35, >0.8→20 |
| Stoch %K | <20→80, 20-50→60, 50-80→40, >80→20 |
| Williams %R | <-80→80, -80to-50→60, -50to-20→40, >-20→20 |
| CCI | <-100→80, -100to0→60, 0to100→40, >100→20 |
| Z-Score | <-2→85, -2to-1→65, -1to1→50, 1to2→35, >2→15 |

**Signal labels:** <25→"Bearish", 25-40→"Mildly Bearish", 40-60→"Neutral", 60-75→"Mildly Bullish", >75→"Bullish"

**Return all values** as a flat dict with keys: `rsi14, macd, macd_signal, macd_hist, bollinger_upper, bollinger_lower, bollinger_pct_b, stochastic_k, stochastic_d, williams_r, atr14, cci20, zscore20, composite_score, composite_signal`

---

### 10. `compute_statistics(close) → dict`
**Log returns:** `r_t = ln(S_t / S_{t-1})`

**Hurst exponent (R/S analysis):**
```
For τ in [10, 20, 40, 80, 160] (only use τ where len(r) > τ):
  Divide r into non-overlapping blocks of length τ
  For each block:
    mean-adjust → cumulative deviation series
    R = max(cumdev) - min(cumdev)
    S = std(block)
    RS = R/S
  RS_τ = mean(RS) across blocks
Regress log(RS_τ) on log(τ) → slope = H
Clip H to [0.01, 0.99]
Regime: H<0.45→"Mean-Reverting", 0.45-0.55→"Random Walk", H>0.55→"Trending"
```

**Distribution stats:** `scipy.stats.skew(r)`, `scipy.stats.kurtosis(r)` (Fisher/excess kurtosis)

**ADF test:** `statsmodels.tsa.stattools.adfuller(r, maxlag=5)` → report statistic, p-value, `adf_stationary=(p<0.05)`

**Jarque-Bera:** `scipy.stats.jarque_bera(r)` → statistic, p-value

**Annualized volatility (%):** for n in [10, 20, 30]: `std(r[-n:]) × √252 × 100`

**Return dict with keys:** `hurst, hurst_regime, skewness, kurtosis_excess, adf_statistic, adf_pvalue, adf_stationary, jarque_bera_statistic, jarque_bera_pvalue, annualized_vol_10d, annualized_vol_20d, annualized_vol_30d, mean_daily_return_pct`

---

### 11. `compute_risk_metrics(close) → dict`
```python
r = np.diff(np.log(close))

var_95_pct  = -np.percentile(r, 5) * 100
var_99_pct  = -np.percentile(r, 1) * 100
cvar_95_pct = -np.mean(r[r < np.percentile(r, 5)]) * 100

peak           = np.maximum.accumulate(close)
drawdowns      = (peak - close) / peak
max_drawdown_pct = float(np.max(drawdowns) * 100)

dca_5d_avg  = float(np.mean(close[-5:]))
dca_10d_avg = float(np.mean(close[-10:]))

sharpe_ratio  = float(np.mean(r) / np.std(r) * np.sqrt(252))
downside      = r[r < 0]
sortino_ratio = float(np.mean(r) * 252 / (np.std(downside) * np.sqrt(252))) if len(downside) > 0 else None
```

**Return dict with keys:** `var_95_pct, var_99_pct, cvar_95_pct, max_drawdown_pct, dca_5d_avg, dca_10d_avg, sharpe_ratio, sortino_ratio`

---

### 12. `compute_seasonality(close_series, date_index) → dict`
- `close_series`: `pd.Series` with `DatetimeIndex`
- Compute log returns aligned to dates
- **Day-of-week:** mean log return for each weekday (Mon-Fri) → `{"Monday": float, ...}`
- **Monthly:** mean log return for each month → `{"Jan": float, ..., "Dec": float}`
- **Quarterly:** mean log return for Q1-Q4 → `{"Q1": float, "Q2": float, "Q3": float, "Q4": float}`
- `best_day`, `worst_day`, `best_month`, `worst_month`
- **Decomposition** (only if `len(close_series) >= 44`):
  Use `statsmodels.tsa.seasonal.seasonal_decompose(close_series, model='multiplicative', period=22, extrapolate_trend='freq')`
  Store `.trend.tolist()`, `.seasonal.tolist()`, `.resid.tolist()` — replace NaN with `None`
  If decomposition fails, set all three to `[]`

**Return keys:** `day_of_week, monthly, quarterly, best_day, worst_day, best_month, worst_month, decomposition_trend, decomposition_seasonal, decomposition_residual`

---

### 13. `compute_spreads(all_close_dict) → dict`
- Input: `{"GOLD": pd.Series, "SILVER": pd.Series, "WTI": pd.Series, "BRENT": pd.Series, ...}`
- Align all series to common dates via inner join; use last 180 common trading days

**Gold/Silver ratio:**
```
ratio    = gold / silver (element-wise)
mean_1y  = mean of last min(252, len(ratio)) values
std_1y   = std of same window
z_score  = (ratio[-1] - mean_1y) / std_1y
```
Store: `dates` (list of "YYYY-MM-DD"), `values` (list of float, 4dp), `current`, `mean_1y`, `z_score`
Interpretation: `z>1→"Silver cheap vs gold"`, `z<-1→"Gold cheap vs silver"`, else `"Near historical mean"`

**Brent-WTI spread:** Same structure. `spread = brent - wti`

**Precious-Energy correlation (63-day Pearson):**
```
gold_r = log returns of gold (last 63 days)
wti_r  = log returns of WTI (last 63 days, aligned)
corr   = scipy.stats.pearsonr(gold_r, wti_r)[0]
```

**Return:**
```python
{
    "gold_silver_ratio": {"dates":[...], "values":[...], "current":float, "mean_1y":float, "z_score":float, "interpretation":str},
    "brent_wti_spread":  {"dates":[...], "values":[...], "current":float, "mean_1y":float, "z_score":float},
    "precious_energy_corr_3m": float
}
```
If SILVER or BRENT missing from dict, set those sections to `null`.

---

### 14. `compute_correlations(all_close_dict, dxy_series) → dict`
- Align all 10 commodity series to common dates (inner join, last 63 trading days)
- **Correlation matrix:** for each pair `(i, j)`: `pearsonr(log_returns_i[-63:], log_returns_j[-63:])[0]`
  Store as nested dict: `{"GOLD": {"GOLD": 1.0, "SILVER": 0.82, ...}, ...}`
- **DXY proxy:** `dxy_r = -np.diff(np.log(dxy_series))` (negative = invert EUR/USD → DXY direction)
  For each commodity `i`: `corr = pearsonr(r_i[-63:], dxy_r[-63:])[0]`
  Store as: `{"GOLD": float, "SILVER": float, ...}`

Skip missing commodities gracefully.

---

### 15. `compute_commodity_specific(close, dates, commodity_id, gold_close, dxy_corr) → dict`
**Inflation hedge score:**
```
if commodity_id == "GOLD": score = 1.0
else:
    r_comm = log_returns(close[-64:])[-63:]
    r_gold = log_returns(gold_close[-64:])[-63:]
    corr = pearsonr(r_comm, r_gold)[0]
    score = max(0.0, min(1.0, corr))
```

**Price vs 1Y mean:**
```
n       = min(252, len(close))
mean_1y = np.mean(close[-n:])
std_1y  = np.std(close[-n:])
price_vs_1y_mean_pct    = (close[-1] - mean_1y) / mean_1y * 100
price_vs_1y_mean_zscore = (close[-1] - mean_1y) / std_1y  (if std_1y > 0 else 0)
```

**Contango indicator (proxy):**
```
z = price_vs_1y_mean_zscore
if category == "agriculture": "N/A"
elif z > 1.5:  "Backwardation Likely"
elif z > 0.5:  "Slight Backwardation"
elif z < -1.5: "Contango Likely"
elif z < -0.5: "Slight Contango"
else:          "Normal"
```

**Quarterly seasonality:** Only for agriculture; compute same as in `compute_seasonality` but return only quarterly dict. Set to `null` for other categories.

**Return keys:** `inflation_hedge_score, dxy_correlation_3m, price_vs_1y_mean_pct, price_vs_1y_mean_zscore, contango_indicator, quarterly_seasonality`

---

## MAIN FUNCTION

```python
def main():
    import time
    start = time.time()
    print("COM-QUANT Engine — starting...")

    # 1. Download all commodity data (max 730 days)
    raw_data = {}
    for cid, info in COMMODITIES.items():
        df = download_data(info["ticker"], 730)
        if df is not None and len(df) >= 60:
            raw_data[cid] = df
            print(f"  ✓ {cid}: {len(df)} rows")
        else:
            print(f"  ✗ {cid}: failed or insufficient data", file=sys.stderr)

    # 2. DXY proxy
    dxy_df = download_data(DXY_PROXY_TICKER, 730)
    dxy_series = dxy_df["Close"] if dxy_df is not None else None

    # 3. Spreads + correlations (once, not per window)
    all_close = {cid: raw_data[cid]["Close"] for cid in raw_data}
    spreads      = compute_spreads(all_close)
    correlations = compute_correlations(all_close, dxy_series)

    # 4. Per-commodity, per-window analysis
    data_out = {}
    gold_close_full = raw_data.get("GOLD", list(raw_data.values())[0])["Close"].values

    for cid, info in COMMODITIES.items():
        if cid not in raw_data:
            continue
        df_full = raw_data[cid]
        data_out[cid] = {}

        for win_id, wp in WINDOWS.items():
            df = df_full.iloc[-wp["lookback_days"]:]
            if len(df) < 60:
                continue

            close = df["Close"].values
            high  = df["High"].values  if "High"  in df.columns else None
            low   = df["Low"].values   if "Low"   in df.columns else None
            disp  = wp["display_days"]

            current_price = float(close[-1])
            change_1d = (close[-1]/close[-2] - 1)*100 if len(close)>=2 else 0.0
            change_5d = (close[-1]/close[-6] - 1)*100 if len(close)>=6 else 0.0

            # Forecast dates (business days only)
            last_date = df.index[-1]
            forecast_dates = []
            d = last_date + pd.Timedelta(days=1)
            while len(forecast_dates) < wp["forecast_days"]:
                if d.weekday() < 5:
                    forecast_dates.append(d.strftime("%Y-%m-%d"))
                d += pd.Timedelta(days=1)

            n = wp["forecast_days"]
            arima_r  = fit_arima(close, n)
            hw_r     = fit_holt_winters(close, n)
            mc_r     = fit_monte_carlo(close, n)
            ou_r     = fit_ou_process(close, n)
            ensemble = compute_ensemble(arima_r["forecast"], hw_r["forecast"], mc_r["p50"], ou_r["forecast"], MODEL_WEIGHTS)
            optimal  = find_optimal_entry(ensemble, forecast_dates, current_price)

            indicators  = compute_technical_indicators(close, high, low)
            statistics  = compute_statistics(close)
            risk        = compute_risk_metrics(close)
            close_s     = pd.Series(close, index=df.index)
            seasonality = compute_seasonality(close_s, df.index)

            dxy_corr = correlations["dxy_proxy"].get(cid, 0.0) if correlations else 0.0
            gold_arr = gold_close_full[-len(close):]
            if len(gold_arr) < len(close):
                gold_arr = np.concatenate([np.full(len(close)-len(gold_arr), gold_arr[0]), gold_arr])
            commodity_specific = compute_commodity_specific(close, df.index, cid, gold_arr, dxy_corr)

            data_out[cid][win_id] = {
                "meta": {
                    "id": cid, "name": info["name"], "ticker": info["ticker"],
                    "unit": info["unit"], "category": info["category"],
                    "current_price": round(current_price, 4),
                    "price_change_1d_pct": round(change_1d, 3),
                    "price_change_5d_pct": round(change_5d, 3),
                },
                "history": {
                    "dates": [d.strftime("%Y-%m-%d") for d in df.index[-disp:]],
                    "close":  [round(float(x),4) for x in close[-disp:]],
                    "open":   [round(float(x),4) for x in df["Open"].values[-disp:]],
                    "high":   [round(float(x),4) for x in df["High"].values[-disp:]] if "High" in df.columns else [],
                    "low":    [round(float(x),4) for x in df["Low"].values[-disp:]]  if "Low"  in df.columns else [],
                    "volume": [int(x) for x in df["Volume"].values[-disp:]]           if "Volume" in df.columns else [],
                },
                "forecast": {
                    "dates": forecast_dates,
                    "arima":            arima_r["forecast"],
                    "holt_winters":     hw_r["forecast"],
                    "monte_carlo_p5":   mc_r["p5"],
                    "monte_carlo_p25":  mc_r["p25"],
                    "monte_carlo_p50":  mc_r["p50"],
                    "monte_carlo_p75":  mc_r["p75"],
                    "monte_carlo_p95":  mc_r["p95"],
                    "ou_process":       ou_r["forecast"],
                    "ensemble":         ensemble,
                    "arima_ci_lower":   arima_r["ci_lower"],
                    "arima_ci_upper":   arima_r["ci_upper"],
                    **optimal,
                    "model_weights": MODEL_WEIGHTS,
                },
                "indicators":         indicators,
                "statistics":         statistics,
                "risk":               risk,
                "seasonality":        seasonality,
                "commodity_specific": commodity_specific,
            }
            print(f"  ✓ {cid}/{win_id}")

    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "categories":   CATEGORIES,
        "data":         data_out,
        "spreads":      spreads,
        "correlations": correlations,
    }

    with open("multi_data.json", "w") as f:
        json.dump(json_safe(output), f, indent=2)

    print(f"\nDone in {time.time()-start:.1f}s → multi_data.json written.")

if __name__ == "__main__":
    main()
```

---

## EDGE CASES

1. **Natural Gas** (NG=F): very volatile. Clip all OU simulated values to `[0.01, 5 × current_price]`.
2. **Palladium** (PA=F): may have data gaps. Forward-fill aggressively; if < 60 rows, skip.
3. **Grain prices**: ZW=F, ZC=F, ZS=F quote in cents. If `close[-1] > 2000`, divide OHLC by 100.
4. **yfinance multi-level columns**: flatten with `df.columns = df.columns.get_level_values(0)`.
5. **json_safe**: must handle `float('nan')`, `np.nan`, `np.float64`, `np.ndarray`. Call on entire output dict before writing.
6. **Minimum data guard**: if `len(close) < 30` for a window, `continue` (skip silently).
7. **OLS regression in OU**: if regression produces degenerate `β >= 0` (non-mean-reverting), force `θ = 0.1` and `μ_eq = current_price`.
