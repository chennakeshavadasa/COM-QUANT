# TASK FOR GEMINI
# Read this entire file and implement exactly what is described.
# Output: the generate_html() function body inside build_dashboard.py
#         (or the full index.html if building standalone)
# This spec covers: all HTML sections, CSS design system, JS architecture, Plotly config.

---

## CONTEXT

COM-QUANT is a static commodities quant dashboard. The data is pre-embedded in the page
as `const COMQUANT_DATA = {...};` (injected by build_dashboard.py). The dashboard has NO
backend. All switching between commodities, windows, and categories happens in JavaScript
by reading from COMQUANT_DATA. Charting is done exclusively with Plotly.js.

---

## TECHNICAL STACK

- **HTML5** — semantic structure
- **CSS** — custom variables, CSS Grid, Flexbox — no framework
- **JavaScript (ES6)** — no framework, vanilla JS
- **Plotly.js 2.26.0** from CDN: `https://cdn.plot.ly/plotly-2.26.0.min.js`
- Single self-contained file. No external CSS, no other JS files.

---

## CSS DESIGN SYSTEM

```css
:root {
  --bg:       #0f1117;
  --surface:  #1a1d2e;
  --surface2: #242740;
  --border:   #2a2d4a;
  --text:     #e8eaf6;
  --text2:    #9ba3c9;
  --accent:   #7c83fd;
  --green:    #4caf7d;
  --red:      #f06969;
  --gold:     #ffd166;
  --orange:   #ff9f43;
  --teal:     #48dbfb;
  --radius:   8px;
  --max-width: 1400px;
}

[data-theme="light"] {
  --bg:      #f0f2f8;
  --surface: #ffffff;
  --surface2:#eef0f8;
  --border:  #d0d4e8;
  --text:    #1a1d2e;
  --text2:   #4a5070;
}

/* Global */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; font-size: 14px; line-height: 1.5; }
.container { max-width: var(--max-width); margin: 0 auto; padding: 0 20px; }
.section { padding: 24px 0; border-bottom: 1px solid var(--border); }
.section-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text2); margin-bottom: 16px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge-bull  { background: rgba(76,175,125,0.15); color: var(--green); }
.badge-bear  { background: rgba(240,105,105,0.15); color: var(--red); }
.badge-neut  { background: rgba(124,131,253,0.15); color: var(--accent); }
.badge-gold  { background: rgba(255,209,102,0.15); color: var(--gold); }
.up   { color: var(--green); }
.down { color: var(--red); }

/* Tabs */
.tab-group { display: flex; gap: 4px; }
.tab { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: transparent; color: var(--text2); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.tab:hover { border-color: var(--accent); color: var(--text); }
.tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }

/* Grid layouts */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 900px)  { .grid-4 { grid-template-columns: repeat(2, 1fr); } .grid-3 { grid-template-columns: 1fr 1fr; } }
@media (max-width: 600px)  { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }

/* Commodity card */
.com-card { cursor: pointer; transition: border-color 0.15s; }
.com-card:hover { border-color: var(--accent); }
.com-card.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.com-card .com-name { font-weight: 600; font-size: 14px; }
.com-card .com-ticker { font-size: 11px; color: var(--text2); }
.com-card .com-price { font-size: 20px; font-weight: 700; margin: 6px 0 4px; }
.com-card .com-unit { font-size: 10px; color: var(--text2); }

/* Stat row */
.stat-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: var(--text2); }
.stat-value { font-weight: 600; }

/* Indicator bar */
.ind-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }
.ind-label { width: 90px; color: var(--text2); flex-shrink: 0; }
.ind-bar-wrap { flex: 1; height: 4px; background: var(--border); border-radius: 2px; }
.ind-bar { height: 4px; border-radius: 2px; }
.ind-val { width: 60px; text-align: right; font-weight: 600; }

/* Gauge */
.gauge-wrap { text-align: center; padding: 12px 0; }
.gauge-score { font-size: 36px; font-weight: 700; color: var(--accent); }
.gauge-label { font-size: 13px; font-weight: 600; margin-top: 4px; }

/* Plotly override for transparency */
.plotly-container { width: 100%; }
```

---

## PLOTLY DEFAULTS (use for ALL charts)

```javascript
function plotLayout(overrides = {}) {
    return Object.assign({
        paper_bgcolor: "transparent",
        plot_bgcolor:  "transparent",
        font: { color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || "#e8eaf6",
                family: "system-ui, -apple-system, sans-serif", size: 12 },
        xaxis: { gridcolor: "#2a2d4a", linecolor: "#3a3d5a", zerolinecolor: "#3a3d5a" },
        yaxis: { gridcolor: "#2a2d4a", linecolor: "#3a3d5a", zerolinecolor: "#3a3d5a" },
        margin: { t: 40, r: 20, b: 40, l: 60 },
        legend: { bgcolor: "transparent", bordercolor: "#2a2d4a" },
        hovermode: "x unified",
    }, overrides);
}
const PLOT_CONFIG = { displayModeBar: false, responsive: true };
```
Use `Plotly.react(divId, traces, layout, config)` for ALL chart updates (not `newPlot`).
Initialize with `Plotly.newPlot` on first render only, then use `Plotly.react` on updates.

---

## PAGE STRUCTURE (top to bottom)

### `<head>`
```html
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM-QUANT — Commodities Quant Analysis</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
  /* Full CSS from the section above */
</style>
```

---

### SECTION 1 — HEADER

```html
<header>
  <div class="container" style="display:flex; justify-content:space-between; align-items:center; padding:16px 20px; border-bottom:1px solid var(--border);">
    <div>
      <span style="font-size:22px; font-weight:800; color:var(--accent);">COM-QUANT</span>
      <span style="font-size:13px; color:var(--text2); margin-left:12px;">Commodities Quant Analysis</span>
    </div>
    <div style="display:flex; align-items:center; gap:12px;">
      <span id="updated-ts" style="font-size:11px; color:var(--text2);"></span>
      <button onclick="toggleTheme()" style="padding:4px 10px; border-radius:6px; border:1px solid var(--border); background:transparent; color:var(--text2); cursor:pointer; font-size:12px;" id="theme-btn">☀ Light</button>
    </div>
  </div>
  <div class="container" style="padding:10px 20px 0; display:flex; justify-content:space-between; align-items:center;">
    <div class="tab-group" id="category-tabs">
      <button class="tab active" onclick="setCategory('precious_metals')">✦ Precious Metals</button>
      <button class="tab"        onclick="setCategory('energy')">⚡ Energy</button>
      <button class="tab"        onclick="setCategory('agriculture')">⬡ Agriculture</button>
    </div>
    <div class="tab-group" id="window-tabs">
      <button class="tab active" onclick="setWindow('1W')">1W</button>
      <button class="tab"        onclick="setWindow('2W')">2W</button>
      <button class="tab"        onclick="setWindow('1M')">1M</button>
      <button class="tab"        onclick="setWindow('3M')">3M</button>
      <button class="tab"        onclick="setWindow('6M')">6M</button>
    </div>
  </div>
</header>
```

---

### SECTION 2 — COMMODITY OVERVIEW CARDS

HTML id: `overview-cards`
Container: `<div class="section"><div class="container"><div class="grid-4" id="overview-cards"></div></div></div>`

JS: `renderOverviewCards()` — called when category or window changes.
For each commodity in `COMQUANT_DATA.categories[currentCategory]`:

```javascript
function renderOverviewCards() {
    const cat = COMQUANT_DATA.categories[currentCategory];
    const container = document.getElementById("overview-cards");
    container.innerHTML = "";
    cat.forEach(cid => {
        const d = COMQUANT_DATA.data[cid]?.[currentWindow];
        if (!d) return;
        const change1d = d.meta.price_change_1d_pct;
        const chgClass = change1d >= 0 ? "up" : "down";
        const chgArrow = change1d >= 0 ? "▲" : "▼";
        const signal = d.indicators.composite_signal;
        const badgeCls = signal.includes("Bull") ? "badge-bull" : signal.includes("Bear") ? "badge-bear" : "badge-neut";
        const isActive = cid === currentCommodity ? "active" : "";
        container.innerHTML += `
          <div class="card com-card ${isActive}" onclick="setCommodity('${cid}')">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div>
                <div class="com-name">${d.meta.name}</div>
                <div class="com-ticker">${d.meta.ticker}</div>
              </div>
              <span class="badge ${badgeCls}">${signal}</span>
            </div>
            <div class="com-price">${formatPrice(d.meta.current_price)}</div>
            <div class="com-unit">${d.meta.unit}</div>
            <div style="display:flex;gap:12px;margin-top:6px;font-size:12px;">
              <span class="${chgClass}">${chgArrow} ${Math.abs(change1d).toFixed(2)}% 1D</span>
              <span class="${d.meta.price_change_5d_pct >= 0 ? 'up' : 'down'}">
                ${d.meta.price_change_5d_pct >= 0 ? "▲" : "▼"} ${Math.abs(d.meta.price_change_5d_pct).toFixed(2)}% 5D
              </span>
            </div>
          </div>`;
    });
}
```

---

### SECTION 3 — DEEP ANALYSIS

Layout:
```html
<div class="section">
  <div class="container">
    <div class="section-title">Deep Analysis — <span id="deep-title">Gold</span></div>

    <!-- 3A: Forecast Chart -->
    <div class="card" style="margin-bottom:16px;">
      <div id="forecast-chart" style="height:380px;"></div>
    </div>

    <!-- 3B + 3C side by side -->
    <div class="grid-2">
      <!-- 3B: Optimal Entry -->
      <div class="card" id="optimal-panel"></div>

      <!-- 3C: Technical Indicators -->
      <div class="card" id="indicators-panel"></div>
    </div>
  </div>
</div>
```

#### `renderForecastChart()` — Plotly line chart

Build these Plotly traces:
1. **Historical close** — `{x: hist_dates, y: hist_close, mode:'lines', name:'Historical', line:{color:'#9ba3c9', width:1.5}}`
2. **Vertical "Today" line** — use a shape in layout: `{type:'line', x0:last_hist_date, x1:last_hist_date, y0:0, y1:1, yref:'paper', line:{color:'#2a2d4a', dash:'dot', width:1}}`
3. **ARIMA CI band** — fill between ci_lower and ci_upper: `fillcolor:'rgba(124,131,253,0.1)'`, `line:{width:0}`, `fill:'tonexty'`
4. **ARIMA forecast** — `{x: fc_dates, y: arima, mode:'lines', name:'ARIMA (30%)', line:{color:'#7c83fd', dash:'dash', width:1.5}}`
5. **Holt-Winters** — `{..., name:'Holt-Winters (30%)', line:{color:'#ff9f43', dash:'dash', width:1.5}}`
6. **MC fan** — fill between p5 and p95: `fillcolor:'rgba(72,219,251,0.08)'`, then MC P50: `{name:'MC Median (25%)', line:{color:'#48dbfb', dash:'dot', width:1}}`
7. **OU Process** — `{name:'Ornstein-Uhlenbeck (15%)', line:{color:'#4caf7d', dash:'dash', width:1.5}}`
8. **Ensemble** — `{name:'Ensemble', line:{color:'#ffd166', width:2.5}}` (boldest line)
9. **Optimal entry marker** — `{x:[optimal_date], y:[optimal_price], mode:'markers', marker:{color:'#4caf7d', size:10, symbol:'circle'}, name:'Best Entry', hoverinfo:'x+y'}`

Filter out `null` values from arrays before plotting (replace null-containing arrays with filtered version using non-null indexes).

Layout title: `"${d.meta.name} — ${currentWindow} Forecast (${d.meta.unit})"`

#### `renderOptimalEntry()` — fills `#optimal-panel`

```html
<div style="padding:8px 0;">
  <div class="section-title">Best Entry Window</div>
  <div style="font-size:28px; font-weight:800; color:var(--green); margin:8px 0;">{optimal_date}</div>
  <div class="stat-row"><span class="stat-label">Price target</span><span class="stat-value">{formatPrice(optimal_price)} {unit}</span></div>
  <div class="stat-row"><span class="stat-label">Days from today</span><span class="stat-value">{optimal_horizon_days}</span></div>
  <div class="stat-row"><span class="stat-label">Potential move</span><span class="stat-value up">↑ {potential_gain_pct.toFixed(2)}%</span></div>
  <div class="stat-row"><span class="stat-label">Current price</span><span class="stat-value">{formatPrice(current_price)}</span></div>
  <div style="font-size:11px; color:var(--text2); margin-top:12px;">Ensemble model. Not financial advice.</div>
</div>
```

#### `renderIndicators()` — fills `#indicators-panel`

```html
<div class="section-title">Technical Signals</div>
<div class="gauge-wrap">
  <div class="gauge-score">{composite_score.toFixed(0)}</div>
  <div class="gauge-label" style="color:{signalColor}">{composite_signal}</div>
  <div style="font-size:11px; color:var(--text2);">Composite 0–100</div>
</div>
<!-- Indicator rows -->
<div class="ind-row"><span class="ind-label">RSI (14)</span><div class="ind-bar-wrap"><div class="ind-bar" style="width:{rsi}%;background:{barColor(rsi,30,70)}"></div></div><span class="ind-val">{rsi.toFixed(1)}</span></div>
<!-- repeat for MACD signal (use macd_hist), %B, Stoch %K, Williams %R, CCI, Z-Score -->
```
Color the bar red if overbought, green if oversold, gray if neutral.
`signalColor`: Bearish→var(--red), Bear→#ff7675, Neutral→var(--text2), Bull→#74b9ff, Bullish→var(--green)

---

### SECTION 4 — SPREAD ANALYTICS

Always visible, not linked to currentCommodity.

```html
<div class="section">
  <div class="container">
    <div class="section-title">Cross-Commodity Spreads</div>
    <div class="grid-2">
      <div class="card">
        <div id="spread-gold-silver" style="height:240px;"></div>
        <div id="gold-silver-info" style="margin-top:8px; font-size:12px; color:var(--text2);"></div>
      </div>
      <div class="card">
        <div id="spread-brent-wti" style="height:240px;"></div>
        <div id="brent-wti-info" style="margin-top:8px; font-size:12px; color:var(--text2);"></div>
      </div>
    </div>
  </div>
</div>
```

`renderSpreads()` — called ONCE on init.

**Gold/Silver ratio chart:**
- Traces: ratio values line (gold color) + horizontal dashed line at mean_1y (gray)
- Layout title: `"Gold/Silver Ratio"`
- Below chart: `"Current: {current} | 1Y Mean: {mean_1y} | Z-Score: {z_score} | {interpretation}"`

**Brent-WTI spread chart:**
- Same structure. Color: coral.
- Below chart: `"Current: ${current}/bbl | 1Y Mean: ${mean_1y} | Z-Score: {z_score}"`

If spread data is null (missing SILVER or BRENT), show `"Data unavailable"` in the panel.

---

### SECTION 5 — CORRELATION MATRIX

Always visible.

```html
<div class="section">
  <div class="container">
    <div class="section-title">Commodity Correlations (3-Month)</div>
    <div style="display:grid; grid-template-columns:2fr 1fr; gap:16px;">
      <div class="card"><div id="corr-heatmap" style="height:380px;"></div></div>
      <div class="card"><div id="dxy-chart"    style="height:380px;"></div></div>
    </div>
  </div>
</div>
```

`renderCorrelationMatrix()` — called ONCE on init.

**Heatmap:**
```javascript
const ids    = Object.keys(COMQUANT_DATA.correlations.matrix);
const labels = ids.map(id => COMQUANT_DATA.data[id]?.["1W"]?.meta?.name || id);
const z      = ids.map(ri => ids.map(ci => COMQUANT_DATA.correlations.matrix[ri]?.[ci] ?? 0));

const trace = {
    type: 'heatmap', z, x: labels, y: labels,
    colorscale: [[-1,'#f06969'],[0,'#2a2d4a'],[1,'#4caf7d']],  // but Plotly needs [[0,col],[0.5,col],[1,col]]
    // correct Plotly format:
    colorscale: [[0,'#f06969'],[0.5,'#2a2d4a'],[1,'#4caf7d']],
    zmin: -1, zmax: 1,
    text: z.map(row => row.map(v => v.toFixed(2))),
    texttemplate: '%{text}', textfont: {size: 10},
    hoverongaps: false
};
```
Layout: title "Correlation Matrix", margins adjusted for labels.

**DXY Impact chart (horizontal bar):**
```javascript
const dxy    = COMQUANT_DATA.correlations.dxy_proxy;
const dxyIds = Object.keys(dxy).filter(id => COMQUANT_DATA.data[id]?.["1W"]);
const names  = dxyIds.map(id => COMQUANT_DATA.data[id]["1W"].meta.name);
const vals   = dxyIds.map(id => dxy[id]);
const colors = vals.map(v => v < 0 ? "#4caf7d" : "#f06969");  // negative=green(safe haven)
const trace  = { type:'bar', orientation:'h', x: vals, y: names, marker:{color:colors}, name:'DXY Corr' };
```
Layout: title "DXY Sensitivity", xaxis title "Correlation with USD Index", xaxis range [-1,1], add zero line.

---

### SECTION 6 — RISK & STATISTICS

Updates with `currentCommodity` and `currentWindow`.

```html
<div class="section">
  <div class="container">
    <div class="section-title">Risk & Statistical Analysis</div>
    <div class="grid-2">
      <div class="card" id="risk-panel"></div>
      <div class="card" id="stats-panel"></div>
    </div>
  </div>
</div>
```

`renderRiskStats()` — fills both panels with stat rows.

**Risk panel:**
| Label | Value |
|-------|-------|
| VaR 95% | `{var_95_pct.toFixed(3)}%` (red) |
| VaR 99% | `{var_99_pct.toFixed(3)}%` (red) |
| CVaR 95% | `{cvar_95_pct.toFixed(3)}%` (red) |
| Max Drawdown | `{max_drawdown_pct.toFixed(2)}%` (red) |
| Sharpe Ratio | `{sharpe_ratio.toFixed(2)}` (green if >1, orange if >0, red if <0) |
| Sortino Ratio | `{sortino_ratio?.toFixed(2) ?? 'N/A'}` |
| DCA 5-day avg | `{formatPrice(dca_5d_avg)}` |
| DCA 10-day avg | `{formatPrice(dca_10d_avg)}` |

**Statistics panel:**
| Label | Value |
|-------|-------|
| Hurst Exponent | `{hurst.toFixed(3)} — {hurst_regime}` |
| Skewness | `{skewness.toFixed(3)}` |
| Excess Kurtosis | `{kurtosis_excess.toFixed(3)}` |
| ADF p-value | `{adf_pvalue?.toFixed(4)} (${adf_stationary ? '✓ Stationary' : '✗ Non-stationary'})` |
| Jarque-Bera p | `{jarque_bera_pvalue?.toFixed(4)}` |
| Ann. Vol (10d) | `{annualized_vol_10d.toFixed(2)}%` |
| Ann. Vol (20d) | `{annualized_vol_20d.toFixed(2)}%` |
| Ann. Vol (30d) | `{annualized_vol_30d.toFixed(2)}%` |
| Mean Daily Ret | `{mean_daily_return_pct.toFixed(4)}%` |

---

### SECTION 7 — SEASONALITY

Updates with `currentCommodity`.

```html
<div class="section">
  <div class="container">
    <div class="section-title">Seasonality Analysis — <span id="seas-title"></span></div>
    <div class="grid-3">
      <div class="card"><div id="seas-dow"  style="height:220px;"></div></div>
      <div class="card"><div id="seas-mon"  style="height:220px;"></div></div>
      <div class="card"><div id="seas-qtr"  style="height:220px;"></div></div>
    </div>
    <div style="margin-top:10px; font-size:12px; color:var(--text2);" id="seas-summary"></div>
  </div>
</div>
```

`renderSeasonality()`:

**Day-of-week bar chart:** x = ["Mon","Tue","Wed","Thu","Fri"], y = values × 100 (convert to %)
Colors: `v >= 0 ? "#4caf7d" : "#f06969"`

**Monthly bar chart:** x = ["Jan","Feb",...,"Dec"], y = values × 100, same coloring

**Quarterly bar chart:**
- If category == "agriculture" AND `quarterly_seasonality` is not null:
  x = ["Q1","Q2","Q3","Q4"], y = values × 100
- Else: show text "Quarterly seasonality data available for agricultural commodities"

**Summary line:** `"Historically best day: {best_day} • Best month: {best_month} | Historical averages, not guarantees"`

---

### SECTION 8 — RANKINGS

Always visible. Shows all available commodities ranked.

```html
<div class="section">
  <div class="container">
    <div class="section-title">Commodity Rankings</div>
    <div class="grid-2">
      <div class="card">
        <div class="section-title">Inflation Hedge Score (vs Gold benchmark)</div>
        <div id="inflation-chart" style="height:280px;"></div>
      </div>
      <div class="card">
        <div class="section-title">DXY Sensitivity (correlation with USD)</div>
        <div id="dxy-rank-chart" style="height:280px;"></div>
      </div>
    </div>
  </div>
</div>
```

`renderRankings()` — called ONCE on init. Loops over all available commodities (all 10).

**Inflation hedge chart (horizontal bar):**
- Get `inflation_hedge_score` from `COMQUANT_DATA.data[cid]["1W"].commodity_specific.inflation_hedge_score`
- Sort descending by score
- Color: gold for GOLD, green-gradient for others
- xaxis: 0–1

**DXY rank chart:** same format, values from `correlations.dxy_proxy`

---

### SECTION 9 — COMMODITY-SPECIFIC PANEL

Updates with `currentCommodity`. Hidden for GOLD (shown for all others).

```html
<div class="section" id="comspec-section">
  <div class="container">
    <div class="section-title">Commodity Intelligence — <span id="comspec-title"></span></div>
    <div class="grid-2">
      <div class="card" id="comspec-panel"></div>
      <div class="card" id="comspec-chart" style="min-height:160px;"></div>
    </div>
  </div>
</div>
```

`renderCommoditySpecific()`:

**Left panel stat rows:**
| Label | Value |
|-------|-------|
| Inflation Hedge Score | bar (0–1) + score |
| DXY Correlation | `{dxy_correlation_3m.toFixed(3)}` |
| Price vs 1Y Mean | `{price_vs_1y_mean_pct.toFixed(2)}%  ({price_vs_1y_mean_zscore.toFixed(2)} σ)` |
| Contango Indicator | colored badge: "Backwardation Likely"→green, "Contango Likely"→red, "Normal"→gray |
| OU Half-Life | `{ou_result.half_life_days.toFixed(1)} days to revert 50% of deviation` (from `forecast.model_weights` section — need to store half_life_days in forecast or commodity_specific) |

**Right panel:** mini Plotly gauge or bar showing price vs 1Y mean visually.

If commodity is GOLD, hide this entire section.

---

### FOOTER

```html
<footer style="padding:20px; text-align:center; border-top:1px solid var(--border); margin-top:32px;">
  <p style="color:var(--text2); font-size:12px;">
    COM-QUANT &nbsp;•&nbsp; Data from Yahoo Finance &nbsp;•&nbsp; For educational purposes only &nbsp;•&nbsp; Not financial advice
  </p>
  <p style="color:var(--text2); font-size:11px; margin-top:4px;">
    Updated daily via GitHub Actions &nbsp;•&nbsp; Built with ARIMA, Holt-Winters, Monte Carlo & Ornstein-Uhlenbeck models
  </p>
</footer>
```

---

## JAVASCRIPT ARCHITECTURE

```javascript
// ── State ─────────────────────────────────────────────────────
let currentCategory  = "precious_metals";
let currentCommodity = "GOLD";
let currentWindow    = "1W";
let chartsInitialized = false;

// ── Helpers ───────────────────────────────────────────────────
function getData() { return COMQUANT_DATA.data[currentCommodity]?.[currentWindow]; }

function formatPrice(p) {
    if (p === null || p === undefined) return "N/A";
    if (p >= 1000)  return p.toLocaleString("en-US", {minimumFractionDigits:2, maximumFractionDigits:2});
    if (p >= 10)    return p.toFixed(3);
    return p.toFixed(4);
}

function filterNulls(dates, values) {
    // Returns [filteredDates, filteredValues] removing positions where value is null/undefined
    const fd=[], fv=[];
    dates.forEach((d,i) => { if (values[i] != null) { fd.push(d); fv.push(values[i]); } });
    return [fd, fv];
}

// ── State setters ─────────────────────────────────────────────
function setCategory(cat) {
    currentCategory = cat;
    currentCommodity = COMQUANT_DATA.categories[cat][0];
    document.querySelectorAll('#category-tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderAll();
}

function setCommodity(id) {
    currentCommodity = id;
    renderOverviewCards();
    renderForecastChart();
    renderOptimalEntry();
    renderIndicators();
    renderRiskStats();
    renderSeasonality();
    renderCommoditySpecific();
    document.getElementById("deep-title").textContent = getData()?.meta?.name || id;
}

function setWindow(win) {
    currentWindow = win;
    document.querySelectorAll('#window-tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderOverviewCards();
    renderForecastChart();
    renderOptimalEntry();
    renderIndicators();
    renderRiskStats();
}

function toggleTheme() {
    const html = document.documentElement;
    const isLight = html.getAttribute('data-theme') === 'light';
    html.setAttribute('data-theme', isLight ? 'dark' : 'light');
    document.getElementById('theme-btn').textContent = isLight ? '☀ Light' : '☽ Dark';
    // Re-render all Plotly charts to pick up new colors
    renderAll();
}

// ── Render all ────────────────────────────────────────────────
function renderAll() {
    renderOverviewCards();
    renderForecastChart();
    renderOptimalEntry();
    renderIndicators();
    renderRiskStats();
    renderSeasonality();
    renderCommoditySpecific();
    if (!chartsInitialized) {
        renderSpreads();
        renderCorrelationMatrix();
        renderRankings();
        chartsInitialized = true;
    }
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Set timestamp
    const ts = new Date(COMQUANT_DATA.generated_at);
    document.getElementById("updated-ts").textContent =
        "Updated: " + ts.toUTCString().replace(" GMT","") + " UTC";

    // First render
    renderAll();
});
```

---

## IMPORTANT IMPLEMENTATION NOTES

1. **Null safety everywhere.** `COMQUANT_DATA.data["PALLADIUM"]?.["1W"]` may be undefined
   if that download failed. Check before accessing any property. Skip silently.

2. **filterNulls()** must be called before every Plotly trace that uses forecast arrays.
   Some model arrays may contain `null` where the model failed.

3. **Plotly.react vs Plotly.newPlot:**
   - First time a div is rendered: use `Plotly.newPlot(divId, traces, layout, config)`
   - On update (window/commodity change): use `Plotly.react(divId, traces, layout, config)`
   - Track initialization with a `Set` of initialized div IDs

4. **Correlation heatmap colorscale** must be in Plotly format (0→1 range, not -1→1):
   `[[0,'#f06969'],[0.5,'#2a2d4a'],[1,'#4caf7d']]`

5. **"Today" divider line** in forecast chart: use `layout.shapes` array with a vertical
   line at `x = last history date`. Use `xref:'x'`, `yref:'paper'`.

6. **MC fan:** To fill between P5 and P95, use two traces:
   - Trace A: x=fc_dates, y=p5, fill=null, line={width:0}, showlegend:false
   - Trace B: x=fc_dates, y=p95, fill='tonexty', fillcolor='rgba(72,219,251,0.08)', line={width:0}, name='MC Range'

7. **Responsive layout:** All Plotly charts use `{responsive:true}` in config.

8. **Agriculture quarterly section:** Check `d.commodity_specific.quarterly_seasonality !== null`
   before rendering the Q1-Q4 chart. If null, show the descriptive message instead.
