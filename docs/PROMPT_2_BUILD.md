# TASK FOR GEMINI
# Read this entire file and implement exactly what is described.
# Output file : build_dashboard.py
# Save to     : current working directory (COM-QUANT/)
# Prerequisites: engine.py must have already run and produced multi_data.json
# Run test    : python build_dashboard.py  →  should produce/update index.html

---

## CONTEXT

COM-QUANT is a static commodities quantitative analysis dashboard served on GitHub Pages.
`engine.py` already runs and produces `multi_data.json` (a large JSON with analysis for
10 commodities × 5 time windows, plus cross-commodity spreads and correlations).

`build_dashboard.py` has ONE job: read `multi_data.json` and produce `index.html` — a
completely self-contained file with ALL data embedded as a JavaScript variable. No network
calls are made at runtime. The browser switches between pre-computed datasets in JS.

---

## IMPLEMENTATION

```python
import json, os, sys, datetime

def main():
    # --- 1. Load data ---
    if not os.path.exists("multi_data.json"):
        print("ERROR: multi_data.json not found. Run engine.py first.", file=sys.stderr)
        sys.exit(1)

    with open("multi_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- 2. Minify the JSON for embedding ---
    data_json_str = json.dumps(data, separators=(',', ':'))

    # --- 3. Generate full HTML ---
    html = generate_html(data, data_json_str)

    # --- 4. Write output ---
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"Built index.html ({size_kb} KB) — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


def generate_html(data, data_json_str):
    """
    Returns a complete, self-contained HTML string.
    The JSON data is injected via a <script> block at the top of <body>.

    Structure:
      <!DOCTYPE html>
      <html>
        <head>  ...CSS + Plotly CDN link... </head>
        <body>
          <script>
            const COMQUANT_DATA = {data_json_str};   ← embedded data
          </script>

          ...all HTML sections (header, cards, charts, etc.)...

          <script>
            ...all JS logic (rendering, event handlers)...
          </script>
        </body>
      </html>

    The CSS and JS logic live inside the HTML — no external .css or .js files.
    The only external resource is the Plotly.js CDN link in <head>.
    """

    # Read the spec from PROMPT_3_DASHBOARD.md for the full HTML/CSS/JS implementation.
    # The generate_html() function should return that complete HTML string
    # with the embedded JSON injected as shown above.

    # For this file (build_dashboard.py), the important contract is:
    #   - data_json_str is injected into a <script> block as:
    #       const COMQUANT_DATA = <data_json_str>;
    #   - This must appear BEFORE all other JS logic in the page
    #   - The rest of the page reads from window.COMQUANT_DATA

    pass  # ← Replace with actual HTML generation (see PROMPT_3_DASHBOARD.md)


if __name__ == "__main__":
    main()
```

---

## CONTRACT WITH index.html

The generated `index.html` must follow these rules:

### Data injection
```html
<script>
  const COMQUANT_DATA = {...minified JSON...};
</script>
```
This `<script>` block appears immediately after `<body>`, before any other `<script>` tags.

### Data access pattern in JS
```javascript
// Top-level state
let currentCategory  = "precious_metals";
let currentCommodity = "GOLD";
let currentWindow    = "1W";

// Helper
function getData() {
    return COMQUANT_DATA.data[currentCommodity][currentWindow];
}

// Category list
COMQUANT_DATA.categories.precious_metals  // ["GOLD","SILVER","PLATINUM","PALLADIUM"]
COMQUANT_DATA.categories.energy           // ["WTI","BRENT","NATGAS"]
COMQUANT_DATA.categories.agriculture      // ["WHEAT","CORN","SOYBEAN"]

// Spreads
COMQUANT_DATA.spreads.gold_silver_ratio   // {dates, values, current, mean_1y, z_score, interpretation}
COMQUANT_DATA.spreads.brent_wti_spread    // {dates, values, current, mean_1y, z_score}
COMQUANT_DATA.spreads.precious_energy_corr_3m  // float

// Correlations
COMQUANT_DATA.correlations.matrix         // {"GOLD": {"GOLD":1.0, "SILVER":0.82, ...}, ...}
COMQUANT_DATA.correlations.dxy_proxy      // {"GOLD": -0.65, ...}

// Metadata
COMQUANT_DATA.generated_at               // ISO timestamp string
```

### AnalysisObject keys accessed by the dashboard
```javascript
const d = getData();

d.meta.name               // "Gold"
d.meta.current_price      // 2050.30
d.meta.price_change_1d_pct // 0.45
d.meta.price_change_5d_pct // -0.82
d.meta.unit               // "USD/troy oz"

d.history.dates           // ["2024-01-01", ...]
d.history.close           // [2010.5, ...]

d.forecast.dates          // ["2024-02-01", ...]
d.forecast.arima          // [2052.0, ...]
d.forecast.holt_winters   // [2055.0, ...]
d.forecast.monte_carlo_p5  // [...]
d.forecast.monte_carlo_p50 // [...]
d.forecast.monte_carlo_p95 // [...]
d.forecast.ou_process      // [2048.0, ...]
d.forecast.ensemble        // [2053.5, ...]
d.forecast.arima_ci_lower  // [...]
d.forecast.arima_ci_upper  // [...]
d.forecast.optimal_date    // "2024-02-05"
d.forecast.optimal_price   // 2075.50
d.forecast.optimal_horizon_days  // 5
d.forecast.potential_gain_pct    // 1.23

d.indicators.rsi14, .macd, .macd_signal, .macd_hist
d.indicators.bollinger_pct_b, .stochastic_k, .williams_r
d.indicators.atr14, .cci20, .zscore20
d.indicators.composite_score     // 0-100
d.indicators.composite_signal    // "Neutral"

d.statistics.hurst, .hurst_regime
d.statistics.skewness, .kurtosis_excess
d.statistics.adf_pvalue, .adf_stationary
d.statistics.jarque_bera_pvalue
d.statistics.annualized_vol_10d, .annualized_vol_20d, .annualized_vol_30d

d.risk.var_95_pct, .var_99_pct, .cvar_95_pct
d.risk.max_drawdown_pct
d.risk.dca_5d_avg, .dca_10d_avg
d.risk.sharpe_ratio, .sortino_ratio

d.seasonality.day_of_week   // {"Monday": float, ...}
d.seasonality.monthly       // {"Jan": float, ...}
d.seasonality.quarterly     // {"Q1": float, ...}
d.seasonality.best_day, .worst_day, .best_month, .worst_month
d.seasonality.decomposition_trend, .decomposition_seasonal, .decomposition_residual

d.commodity_specific.inflation_hedge_score   // 0-1
d.commodity_specific.dxy_correlation_3m
d.commodity_specific.price_vs_1y_mean_pct
d.commodity_specific.price_vs_1y_mean_zscore
d.commodity_specific.contango_indicator       // "Normal" / "Slight Backwardation" / etc.
```

---

## IMPORTANT NOTES

1. The full HTML/CSS/JS specification is in `PROMPT_3_DASHBOARD.md`. Implement `generate_html()`
   according to that spec. `build_dashboard.py` is the glue that loads data and calls it.

2. `generate_html()` takes `data` (Python dict) and `data_json_str` (minified JSON string).
   It must return a single complete HTML string.

3. All chart rendering uses Plotly.js (loaded from CDN in `<head>`).

4. If `multi_data.json` has a commodity missing (download failed), the JS must handle
   `COMQUANT_DATA.data["PALLADIUM"]` being undefined — skip it silently, no JS errors.

5. Print file size to stdout after writing — useful for debugging during CI.

---

## EXPECTED OUTPUT

Running `python build_dashboard.py` from the COM-QUANT directory should:
1. Read `multi_data.json` (same directory)
2. Write `index.html` (same directory)
3. Print: `Built index.html (NNN KB) — 2024-01-15 02:31 UTC`
4. Return exit code 0
