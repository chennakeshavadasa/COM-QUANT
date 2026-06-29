# COM-QUANT — Full Upgrade Instructions for Gemini Pro

You are an expert Python and frontend developer. Your task is to upgrade the `COM-QUANT`
repository completely. Follow every instruction below exactly. Do not skip any item.
Do not introduce any feature not listed. Do not break any existing functionality.

The repo structure you are working with:
```
COM-QUANT/
├── src/
│   ├── engine.py          ← Python analytics engine
│   └── build_dashboard.py ← HTML generator (reads JSON → writes index.html)
├── .github/
│   └── workflows/
│       └── update.yml     ← GitHub Actions CI/CD
├── multi_data.json        ← generated daily (do not hand-edit)
├── index.html             ← generated daily (do not hand-edit)
├── .nojekyll
└── README.md
```

---

## PART 1 — ENGINE FIXES (src/engine.py)

### Fix 1 · Remove the fixed random seed

Find and delete this line at module level:
```python
np.random.seed(42)
```
Do NOT add it back anywhere in the file. The Monte Carlo simulation must be
non-deterministic so each daily run produces genuinely different stochastic paths.

---

### Fix 2 · Vectorize the Monte Carlo simulation

Find the function `mc_forecast` and replace it entirely with the version below.
The old implementation used a sequential Python for-loop which is slow and still
produced a scalar `prev` reference that is incorrect when used in a NumPy context.
The new version uses `np.cumprod` which is both correct and 20–50× faster.

```python
def mc_forecast(series, n, n_sims=MC_SIMS):
    """
    Geometric Brownian Motion Monte Carlo forecast.
    Fully vectorized via np.cumprod — no Python loops over time steps.
    """
    lr  = np.log(series / series.shift(1)).dropna()
    mu  = float(lr.mean())
    sig = float(lr.std())
    S0  = float(series.iloc[-1])

    # Shape (n, n_sims): each column is one simulated price path
    shocks = np.exp(
        (mu - 0.5 * sig ** 2)
        + sig * np.random.standard_normal((n, n_sims))
    )
    sims = S0 * np.cumprod(shocks, axis=0)   # (n, n_sims)

    pcts       = np.percentile(sims, [5, 25, 50, 75, 95], axis=1)
    prob_below = (sims < S0).mean(axis=1)

    best_idx = int(np.argmin(pcts[2]))        # day where median is lowest
    return {
        "S0":                    round(S0, 4),
        "mu_daily":              mu,
        "sigma_daily":           sig,
        "p5":                    [round(float(v), 4) for v in pcts[0]],
        "p25":                   [round(float(v), 4) for v in pcts[1]],
        "p50":                   [round(float(v), 4) for v in pcts[2]],
        "p75":                   [round(float(v), 4) for v in pcts[3]],
        "p95":                   [round(float(v), 4) for v in pcts[4]],
        "prob_below_current":    [round(float(p), 4) for p in prob_below],
        "best_entry_day_idx":    best_idx,
        "best_entry_date_offset": best_idx,   # caller resolves to actual date
    }
```

---

### Fix 3 · Stop computing Jarque-Bera twice

In the `statistics()` function (or however your engine computes statistical
metrics), find these two lines:

```python
"jb_stat": float(stats.jarque_bera(r)[0]),
"jb_p":    float(stats.jarque_bera(r)[1]),
```

Replace them with:
```python
_jb = stats.jarque_bera(r)
"jb_stat": float(_jb[0]),
"jb_p":    float(_jb[1]),
```

---

### Fix 4 · Add pipeline metadata to JSON output

In `main()`, after computing all commodity data but before writing to disk,
inject a top-level `_meta` key. Track which commodities succeeded and failed.

```python
# ── inside main(), replace the existing loop + write logic with this ──────────

failed   = []
output   = {}

for commodity_key in ALL_COMMODITIES:            # use whatever your loop variable is
    try:
        output[commodity_key] = run_commodity(commodity_key)   # your existing call
    except Exception as exc:
        print(f"  ✗ {commodity_key} failed: {exc}")
        import traceback; traceback.print_exc()
        failed.append(commodity_key)

output["_meta"] = {
    "generated_at":       datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    "commodities_ok":     [k for k in output if k != "_meta"],
    "commodities_failed": failed,
    "engine_version":     "2.0.0",
    "update_interval_h":  6,
}

out_path = "multi_data.json"
with open(out_path, "w") as fh:
    json.dump(output, fh, separators=(",", ":"), default=str)

size_kb = os.path.getsize(out_path) / 1024
print(f"\n✅  Saved → {out_path}  ({size_kb:.1f} KB)")
```

Add `import os` at the top of the file if not already present.

---

### Fix 5 · Trim historical arrays to cap JSON size

In your `run_commodity()` (or equivalent) function, after building the `history`
dict that holds OHLCV arrays, cap every array to the last **365 entries** maximum.
Replace:
```python
H_chart = df.tail(forecast_days).copy()
```
with:
```python
H_chart = df.tail(min(365, len(df))).copy()
```

This alone typically cuts `multi_data.json` size by 40–60 %.

---

### Fix 6 · Pin requirements.txt

Create or completely replace `requirements.txt` in the repo root with:
```
yfinance==0.2.54
numpy==1.26.4
pandas==2.2.2
scipy==1.13.1
statsmodels==0.14.2
ta==0.11.0
plotly==5.22.0
```

---

## PART 2 — WORKFLOW FIX (.github/workflows/update.yml)

Replace the entire `update.yml` file with the following. Key changes:
- Cron runs every 6 hours on **weekdays only** (Mon–Fri)
- Commit step is **conditional**: it only commits when `multi_data.json`
  or `index.html` actually changed. Weekend runs and holiday runs where
  yfinance returns identical forward-filled data will produce zero commits.

```yaml
name: Daily COM-QUANT Update

on:
  schedule:
    # 02:00, 08:00, 14:00, 20:00 UTC — Monday through Friday only
    - cron: '0 2,8,14,20 * * 1-5'
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run engine
        run: python src/engine.py

      - name: Build dashboard
        run: python src/build_dashboard.py

      - name: Commit if data changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add multi_data.json index.html
          if git diff --cached --quiet; then
            echo "::notice::No data change detected — skipping commit."
          else
            git commit -m "auto-update: $(date -u '+%Y-%m-%d %H:%M UTC')"
            git push
          fi
```

---

## PART 3 — COMPLETE UI OVERHAUL (src/build_dashboard.py)

Rewrite `build_dashboard.py` entirely. The current dashboard is visually
poor. The replacement must look like a professional institutional terminal.

The script reads `multi_data.json` and writes `index.html`.
Every style, chart, and behavior described below must be implemented.

---

### 3.1 Design System (inject as CSS custom properties)

```css
:root {
  /* Backgrounds */
  --bg-primary:    #080B14;
  --bg-secondary:  #0D1421;
  --bg-card:       rgba(255, 255, 255, 0.04);
  --bg-card-hover: rgba(255, 255, 255, 0.07);

  /* Borders */
  --border:        rgba(255, 255, 255, 0.07);
  --border-bright: rgba(255, 255, 255, 0.14);

  /* Text */
  --text-primary:  #E8EDF5;
  --text-secondary:#8B95A3;
  --text-muted:    #4A5568;

  /* Sector accents */
  --sector-metals: #F5A623;   /* gold/silver */
  --sector-energy: #FF6B35;   /* crude/gas/brent */
  --sector-agri:   #4CAF50;   /* corn/wheat/soy/coffee/sugar */

  /* Signal colours */
  --signal-strong-buy:  #00D084;
  --signal-buy:         #4A9EFF;
  --signal-neutral:     #8B95A3;
  --signal-sell:        #FF9F43;
  --signal-strong-sell: #FF4757;

  /* Chart model colours */
  --chart-arima:    #4A9EFF;
  --chart-hw:       #A78BFA;
  --chart-mc:       #FF6B35;
  --chart-ou:       #F5A623;
  --chart-ensemble: #FFFFFF;

  /* Misc */
  --positive: #00D084;
  --negative: #FF4757;
  --radius:   12px;
  --radius-sm: 8px;
  --shadow:   0 4px 24px rgba(0, 0, 0, 0.45);
  --transition: 180ms ease;
}
```

---

### 3.2 Typography

Add these two Google Fonts imports in `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

Rules:
- `font-family: 'Inter', system-ui, sans-serif` on `body` — all prose text.
- `font-family: 'JetBrains Mono', monospace` on every element that shows a **number,
  price, percentage, metric value, or date**. Apply via a utility class `.mono`.

---

### 3.3 Global Reset + Body

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; scroll-behavior: smooth; }
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.5;
  min-height: 100vh;
}
.mono { font-family: 'JetBrains Mono', monospace; }
```

---

### 3.4 Header

Fixed top bar, full width, height 64 px.

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [📊 COM-QUANT]  Commodities Quantitative Analysis   [10 markets live]     │
│                                               Last: 2024-01-15 08:03 UTC  │
│                                               Next update in 5h 57m       │
└────────────────────────────────────────────────────────────────────────────┘
```

CSS:
```css
.app-header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 64px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(135deg, #0D1B2A 0%, #080B14 100%);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
}
.header-left   { display: flex; align-items: center; gap: 12px; }
.header-logo   { font-size: 20px; font-weight: 700; letter-spacing: -0.5px;
                 background: linear-gradient(135deg, #4A9EFF, #A78BFA);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-sub    { font-size: 12px; color: var(--text-secondary); }
.header-right  { text-align: right; }
.header-ts     { font-size: 11px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }
.header-countdown { font-size: 12px; color: var(--signal-buy); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }
```

The countdown timer is a `<span id="countdown">` updated by JavaScript every second.
The staleness warning (if data > 25 h old) is a full-width yellow banner just below
the header with text `⚠ Data may be stale — last updated X hours ago`.

---

### 3.5 Filter + Sort Bar

Sticky below the header.

```
[ALL]  [PRECIOUS METALS]  [ENERGY]  [AGRICULTURE]           🔍 [search...] Sort: [▼]
```

```css
.filter-bar {
  position: sticky; top: 64px; z-index: 90;
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 10px 24px;
  background: rgba(8, 11, 20, 0.92);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(8px);
}
.filter-btn {
  padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 500;
  border: 1px solid var(--border); background: transparent;
  color: var(--text-secondary); cursor: pointer; transition: var(--transition);
}
.filter-btn:hover, .filter-btn.active {
  border-color: var(--signal-buy); color: var(--signal-buy);
  background: rgba(74, 158, 255, 0.10);
}
.search-box {
  margin-left: auto; padding: 5px 12px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--bg-secondary);
  color: var(--text-primary); font-size: 13px; outline: none; width: 180px;
}
.sort-select {
  padding: 5px 10px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--bg-secondary);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
}
```

---

### 3.6 Commodity Card Grid

Main content starts at `top: 64px + filter-bar-height`. Use CSS Grid:

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding: 20px 24px 40px;
  margin-top: 64px;    /* header height — adjust dynamically in JS if needed */
}
```

---

### 3.7 Commodity Card Anatomy

Each card must be structured exactly as described. Use a Python helper
`render_card(key, data)` that returns an HTML string.

```
┌──[sector-color border 3px left]────────────────────────────────┐
│  GOLD  ·  XAU/USD                      [🟢 STRONG BUY] badge   │
│  Precious Metals                                                │
│  ─────────────────────────────────────────────────────────── │
│  $2,345.60           +$28.70   +1.24%  ▲                       │
│  ─────────────────────────────────────────────────────────── │
│  [SVG sparkline — last 30 bars of close price — 70px tall]     │
│  ─────────────────────────────────────────────────────────── │
│  Ensemble 30d forecast: $2,401.20 (+2.37%)  ↗                 │
│  ─────────────────────────────────────────────────────────── │
│  RSI   67.3  [████████░░░]  │  Hurst   0.58  Trending          │
│  VaR95 −1.2%               │  Vol     14.3% ann                │
│  MaxDD −8.4%               │  Sharpe  1.42                     │
│  ─────────────────────────────────────────────────────────── │
│  [View Full Analysis →]                                        │
└────────────────────────────────────────────────────────────────┘
```

CSS:
```css
.commodity-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 18px 14px;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition),
              border-color var(--transition);
  position: relative;
  overflow: hidden;
}
.commodity-card::before {
  content: '';
  position: absolute; top: 0; left: 0; bottom: 0;
  width: 3px;
  background: var(--sector-color);   /* set inline per card */
  border-radius: 3px 0 0 3px;
}
.commodity-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
  border-color: var(--border-bright);
  background: var(--bg-card-hover);
}
```

Sector color is injected as an inline style variable on the card element:
```html
<div class="commodity-card" style="--sector-color: #F5A623" data-sector="metals" ...>
```

**Signal badge** (top-right of card header):
```css
.signal-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
  letter-spacing: 0.3px;
}
.signal-strong-buy  { background: rgba(0,208,132,0.15); color: #00D084; border: 1px solid rgba(0,208,132,0.3); }
.signal-buy         { background: rgba(74,158,255,0.15); color: #4A9EFF; border: 1px solid rgba(74,158,255,0.3); }
.signal-neutral     { background: rgba(139,149,163,0.15); color: #8B95A3; border: 1px solid rgba(139,149,163,0.3); }
.signal-sell        { background: rgba(255,159,67,0.15); color: #FF9F43; border: 1px solid rgba(255,159,67,0.3); }
.signal-strong-sell { background: rgba(255,71,87,0.15); color: #FF4757; border: 1px solid rgba(255,71,87,0.3); }
```

Signal threshold logic (Python side, before rendering):
```python
def score_to_signal(score):
    if   score >= 70: return "strong-buy",  "STRONG BUY",  "🟢"
    elif score >= 55: return "buy",          "BUY",         "🔵"
    elif score >= 40: return "neutral",      "NEUTRAL",     "⚪"
    elif score >= 25: return "sell",         "SELL",        "🟠"
    else:             return "strong-sell",  "STRONG SELL", "🔴"
```

**Price change display**:
- Positive change: color `var(--positive)`, arrow `▲`
- Negative change: color `var(--negative)`, arrow `▼`
- Zero: color `var(--text-secondary)`, `—`

**Sparkline** — pure inline SVG polyline, no library:

```python
def sparkline_svg(prices, sector_color, width=280, height=70):
    prices = [p for p in prices if p is not None]
    if len(prices) < 2:
        return "<svg></svg>"
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1
    xs = [i / (len(prices) - 1) * width for i in range(len(prices))]
    ys = [height - (p - mn) / rng * height for p in prices]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    # Close path for the gradient fill
    fill_pts = f"0,{height} " + pts + f" {width},{height}"
    return f"""
<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:{height}px;display:block">
  <defs>
    <linearGradient id="sg_{sector_color[1:]}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{sector_color}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="{sector_color}" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <polygon points="{fill_pts}" fill="url(#sg_{sector_color[1:]})" />
  <polyline points="{pts}" fill="none" stroke="{sector_color}"
            stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
</svg>"""
```

**RSI bar**:
```python
def rsi_bar_html(rsi_val):
    pct  = min(max(rsi_val or 50, 0), 100)
    if   pct < 30: color = "var(--positive)"
    elif pct > 70: color = "var(--negative)"
    else:          color = "var(--text-secondary)"
    return f"""
<div style="display:flex;align-items:center;gap:8px">
  <span class="mono" style="font-size:12px;color:{color}">{pct:.1f}</span>
  <div style="flex:1;height:4px;background:rgba(255,255,255,0.1);border-radius:2px">
    <div style="width:{pct}%;height:100%;background:{color};border-radius:2px;
                transition:width 0.6s ease"></div>
  </div>
</div>"""
```

**Metrics grid** (2-column layout below sparkline):
```html
<div class="metrics-grid">
  <div class="metric-item">
    <span class="metric-label">RSI</span>
    {rsi_bar_html}
  </div>
  <div class="metric-item">
    <span class="metric-label">Hurst</span>
    <span class="metric-val mono">{hurst:.2f} <span class="metric-sub">{hurst_label}</span></span>
  </div>
  <div class="metric-item">
    <span class="metric-label">VaR 95%</span>
    <span class="metric-val mono negative">{var95:.2f}%</span>
  </div>
  <div class="metric-item">
    <span class="metric-label">Ann. Vol</span>
    <span class="metric-val mono">{vol:.1f}%</span>
  </div>
  <div class="metric-item">
    <span class="metric-label">Max DD</span>
    <span class="metric-val mono negative">{maxdd:.1f}%</span>
  </div>
  <div class="metric-item">
    <span class="metric-label">Sharpe</span>
    <span class="metric-val mono">{sharpe:.2f}</span>
  </div>
</div>
```

```css
.metrics-grid      { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; margin-top: 12px; }
.metric-item       { display: flex; flex-direction: column; gap: 3px; }
.metric-label      { font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); }
.metric-val        { font-size: 13px; color: var(--text-primary); }
.metric-val.positive { color: var(--positive); }
.metric-val.negative { color: var(--negative); }
.metric-sub        { font-size: 10px; color: var(--text-secondary); }
```

Hurst label:
- H < 0.45 → "Mean-Rev."
- 0.45 ≤ H ≤ 0.55 → "Random"
- H > 0.55 → "Trending"

---

### 3.8 Detail Modal (Plotly Charts)

When a card is clicked, a full-screen modal overlays the page.

```css
.modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 200;
  background: rgba(8, 11, 20, 0.97);
  backdrop-filter: blur(6px);
  overflow-y: auto;
  padding: 24px;
}
.modal-overlay.open { display: block; }
.modal-inner {
  max-width: 1200px; margin: 0 auto;
  background: var(--bg-secondary);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius);
  padding: 28px;
}
.modal-close {
  float: right; font-size: 22px; cursor: pointer;
  color: var(--text-secondary); background: none; border: none;
  line-height: 1;
}
```

The modal contains **4 Plotly chart divs**. The chart data is embedded as
JavaScript objects and rendered via `Plotly.newPlot()` on modal open.

Use this Plotly base layout for all charts:
```python
PLOTLY_DARK = {
    "paper_bgcolor": "#0D1421",
    "plot_bgcolor":  "#0D1421",
    "font":          {"family": "Inter, sans-serif", "color": "#8B95A3", "size": 12},
    "title_font":    {"family": "Inter, sans-serif", "color": "#E8EDF5", "size": 14},
    "xaxis": {
        "gridcolor":      "rgba(255,255,255,0.05)",
        "zerolinecolor":  "rgba(255,255,255,0.08)",
        "tickfont":       {"family": "JetBrains Mono, monospace", "color": "#8B95A3", "size": 10},
        "linecolor":      "rgba(255,255,255,0.08)",
    },
    "yaxis": {
        "gridcolor":      "rgba(255,255,255,0.05)",
        "zerolinecolor":  "rgba(255,255,255,0.08)",
        "tickfont":       {"family": "JetBrains Mono, monospace", "color": "#8B95A3", "size": 10},
        "linecolor":      "rgba(255,255,255,0.08)",
    },
    "legend": {
        "bgcolor":     "rgba(255,255,255,0.05)",
        "bordercolor": "rgba(255,255,255,0.10)",
        "borderwidth": 1,
        "font":        {"size": 11},
    },
    "margin": {"l": 55, "r": 20, "t": 45, "b": 40},
    "hovermode": "x unified",
}
```

**Chart 1 — Price + All Model Forecasts**:
- Historical close: solid white line, name="Price"
- ARIMA forecast: dashed `#4A9EFF` line + shaded 95% CI band (opacity 0.1)
- Holt-Winters forecast: dashed `#A78BFA` line
- Monte Carlo P50: dashed `#FF6B35` line + P5–P95 band (opacity 0.08)
- OU forecast: dashed `#F5A623` line (if present in data)
- Ensemble forecast: solid `#FFFFFF` thick (width=2.5) line — the star
- Vertical dashed line at today separating history from forecast
- Title: `"Price & Ensemble Forecast — {commodity_name}"`

**Chart 2 — RSI + MACD**:
- Two subplots stacked (use `make_subplots(rows=2, cols=1, shared_xaxes=True)`)
- Row 1: RSI line in `#4A9EFF`, horizontal dashed lines at 30 and 70
- Row 2: MACD histogram (bars, green if positive / red if negative), MACD line, signal line
- Title: `"Momentum Indicators"`

**Chart 3 — Monte Carlo Fan**:
- Plot 15 random sample paths as thin translucent lines (`opacity=0.15`, colour=#FF6B35)
- Overlay P5, P50, P95 as solid lines with different weights
- Shaded region between P5 and P95
- Title: `"Monte Carlo Simulation ({MC_SIMS:,} paths) — {forecast_label} Horizon"`

**Chart 4 — Seasonality**:
- Bar chart of day-of-week average returns
- Bars green if positive, red if negative
- Title: `"Day-of-Week Seasonality (Historical)"`

Embed all chart specs as a JSON literal in `<script>`:
```javascript
const CHARTS = {
  "GOLD":   { traces1: [...], layout1: {...}, traces2: [...], ... },
  "SILVER": { ... },
  ...
};
```

On card click:
```javascript
function openModal(key) {
  const c = CHARTS[key];
  Plotly.newPlot('chart1', c.traces1, c.layout1, {responsive: true, displayModeBar: false});
  Plotly.newPlot('chart2', c.traces2, c.layout2, {responsive: true, displayModeBar: false});
  Plotly.newPlot('chart3', c.traces3, c.layout3, {responsive: true, displayModeBar: false});
  Plotly.newPlot('chart4', c.traces4, c.layout4, {responsive: true, displayModeBar: false});
  document.getElementById('detail-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  document.getElementById('detail-modal').classList.remove('open');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => e.key === 'Escape' && closeModal());
```

---

### 3.9 JavaScript Behaviours

All JavaScript is inline in `<script>` at the bottom of `<body>`.

**1 — Countdown timer**:
```javascript
(function() {
  const genAt  = new Date("{{ GENERATED_AT_UTC }}Z");   // injected by Python
  const updateH = 6;
  function tick() {
    const now   = new Date();
    const nextUp = new Date(genAt.getTime() + updateH * 3600 * 1000);
    const diff   = nextUp - now;
    if (diff <= 0) {
      document.getElementById('countdown').textContent = 'Update overdue — refresh';
      return;
    }
    const hh = Math.floor(diff / 3600000);
    const mm = Math.floor((diff % 3600000) / 60000);
    const ss = Math.floor((diff % 60000) / 1000);
    document.getElementById('countdown').textContent =
      `Next update in ${hh}h ${mm.toString().padStart(2,'0')}m ${ss.toString().padStart(2,'0')}s`;
  }
  tick(); setInterval(tick, 1000);
})();
```

**2 — Staleness warning**:
```javascript
(function() {
  const genAt = new Date("{{ GENERATED_AT_UTC }}Z");
  const ageH  = (Date.now() - genAt) / 3600000;
  if (ageH > 25) {
    const banner = document.getElementById('stale-banner');
    banner.textContent = `⚠  Data may be stale — last updated ${Math.floor(ageH)} hours ago`;
    banner.style.display = 'block';
  }
})();
```

**3 — Sector filter**:
```javascript
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const sector = btn.dataset.sector || 'all';
    document.querySelectorAll('.commodity-card').forEach(card => {
      const show = sector === 'all' || card.dataset.sector === sector;
      card.style.display = show ? '' : 'none';
    });
  });
});
```

**4 — Search filter**:
```javascript
document.getElementById('search-box').addEventListener('input', function() {
  const q = this.value.toLowerCase();
  document.querySelectorAll('.commodity-card').forEach(card => {
    const match = card.dataset.name.toLowerCase().includes(q)
                || card.dataset.ticker.toLowerCase().includes(q);
    card.style.display = match ? '' : 'none';
  });
});
```

**5 — Sort**:
```javascript
document.getElementById('sort-select').addEventListener('change', function() {
  const grid = document.querySelector('.dashboard-grid');
  const cards = [...grid.querySelectorAll('.commodity-card')];
  cards.sort((a, b) => +b.dataset[this.value] - +a.dataset[this.value]);
  cards.forEach(c => grid.appendChild(c));
});
```

Each card must carry `data-` attributes for all sortable fields:
```html
<div class="commodity-card"
     data-sector="metals"
     data-name="Gold"
     data-ticker="GC=F"
     data-score="72.4"
     data-rsi="67.3"
     data-vol="14.3"
     data-sharpe="1.42"
     data-ensemble-pct="2.37"
     ...>
```

Sort options in the `<select>`:
```html
<select id="sort-select">
  <option value="score">Composite Score</option>
  <option value="ensemble-pct">Ensemble Forecast %</option>
  <option value="rsi">RSI</option>
  <option value="sharpe">Sharpe Ratio</option>
  <option value="vol" selected>Volatility ↓</option>
</select>
```

---

### 3.10 Footer

```html
<footer class="app-footer">
  COM-QUANT · Automated commodities analysis · Data via Yahoo Finance ·
  For educational purposes only · Not financial advice
</footer>
```
```css
.app-footer {
  text-align: center; padding: 20px; font-size: 11px;
  color: var(--text-muted); border-top: 1px solid var(--border);
  margin-top: 40px;
}
```

---

### 3.11 Plotly CDN Import

In `<head>`:
```html
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
```

---

## DO NOT CHANGE

- The list of commodities (tickers and sector assignments) in `engine.py`
- The `ARIMA`, `HW`, and `OU` model fitting logic (only fix the 3 bugs listed)
- The `safe_list()` utility function
- The `.nojekyll` file
- The `docs/` directory contents
- The GitHub Pages deployment mechanism (index.html must remain at repo root)

---

## SUCCESS CRITERIA

After your changes, the following must be true:

- [ ] Running `python src/engine.py` twice in succession produces **different** MC `p50`
      values (verify non-determinism restored)
- [ ] `multi_data.json` is smaller than the original by ≥ 30 % (history trimmed)
- [ ] The cron in `update.yml` only fires Mon–Fri
- [ ] The commit step in `update.yml` produces **zero** commits on a run with
      unchanged input data
- [ ] `index.html` loads in < 2 s on a standard connection
- [ ] All commodity cards render with the correct 3 px left border in sector colour
- [ ] Sector filter buttons correctly show/hide cards
- [ ] Detail modal opens on card click and renders all 4 Plotly charts
- [ ] The countdown timer ticks every second in the header
- [ ] Stale-data warning appears when `generated_at` is > 25 h ago
- [ ] Mobile layout collapses to single-column (test at 375 px viewport width)
- [ ] No JavaScript errors in the browser console
