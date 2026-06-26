import json, os, sys, datetime

def main():
    if not os.path.exists("multi_data.json"):
        print("ERROR: multi_data.json not found. Run engine.py first.", file=sys.stderr)
        sys.exit(1)

    with open("multi_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    data_json_str = json.dumps(data, separators=(',', ':'))
    html = generate_html(data, data_json_str)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = len(html) // 1024
    print(f"Built index.html ({size_kb} KB) — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

def generate_html(data, data_json_str):
    return f"""<!DOCTYPE html>
<html data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM-QUANT — Commodities Quant Analysis</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<style>
:root {{
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
}}

[data-theme="light"] {{
  --bg:      #f0f2f8;
  --surface: #ffffff;
  --surface2:#eef0f8;
  --border:  #d0d4e8;
  --text:    #1a1d2e;
  --text2:   #4a5070;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; font-size: 14px; line-height: 1.5; }}
.container {{ max-width: var(--max-width); margin: 0 auto; padding: 0 20px; }}
.section {{ padding: 24px 0; border-bottom: 1px solid var(--border); }}
.section-title {{ font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text2); margin-bottom: 16px; }}
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.badge-bull  {{ background: rgba(76,175,125,0.15); color: var(--green); }}
.badge-bear  {{ background: rgba(240,105,105,0.15); color: var(--red); }}
.badge-neut  {{ background: rgba(124,131,253,0.15); color: var(--accent); }}
.badge-gold  {{ background: rgba(255,209,102,0.15); color: var(--gold); }}
.up   {{ color: var(--green); }}
.down {{ color: var(--red); }}

.tab-group {{ display: flex; gap: 4px; }}
.tab {{ padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border); background: transparent; color: var(--text2); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }}
.tab:hover {{ border-color: var(--accent); color: var(--text); }}
.tab.active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}

.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
@media (max-width: 900px)  {{ .grid-4 {{ grid-template-columns: repeat(2, 1fr); }} .grid-3 {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 600px)  {{ .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }} }}

.com-card {{ cursor: pointer; transition: border-color 0.15s; }}
.com-card:hover {{ border-color: var(--accent); }}
.com-card.active {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }}
.com-card .com-name {{ font-weight: 600; font-size: 14px; }}
.com-card .com-ticker {{ font-size: 11px; color: var(--text2); }}
.com-card .com-price {{ font-size: 20px; font-weight: 700; margin: 6px 0 4px; }}
.com-card .com-unit {{ font-size: 10px; color: var(--text2); }}

.stat-row {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }}
.stat-row:last-child {{ border-bottom: none; }}
.stat-label {{ color: var(--text2); }}
.stat-value {{ font-weight: 600; }}

.ind-row {{ display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; }}
.ind-label {{ width: 90px; color: var(--text2); flex-shrink: 0; }}
.ind-bar-wrap {{ flex: 1; height: 4px; background: var(--border); border-radius: 2px; }}
.ind-bar {{ height: 4px; border-radius: 2px; }}
.ind-val {{ width: 60px; text-align: right; font-weight: 600; }}

.gauge-wrap {{ text-align: center; padding: 12px 0; }}
.gauge-score {{ font-size: 36px; font-weight: 700; color: var(--accent); }}
.gauge-label {{ font-size: 13px; font-weight: 600; margin-top: 4px; }}

.plotly-container {{ width: 100%; }}
</style>
</head>
<body>
<script>
  const COMQUANT_DATA = {data_json_str};
</script>

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

<div class="section"><div class="container"><div class="grid-4" id="overview-cards"></div></div></div>

<div class="section">
  <div class="container">
    <div class="section-title">Deep Analysis — <span id="deep-title"></span></div>
    <div class="card" style="margin-bottom:16px;">
      <div id="forecast-chart" style="height:380px;"></div>
    </div>
    <div class="grid-2">
      <div class="card" id="optimal-panel"></div>
      <div class="card" id="indicators-panel"></div>
    </div>
  </div>
</div>

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

<div class="section">
  <div class="container">
    <div class="section-title">Commodity Correlations (3-Month)</div>
    <div style="display:grid; grid-template-columns:2fr 1fr; gap:16px;">
      <div class="card"><div id="corr-heatmap" style="height:380px;"></div></div>
      <div class="card"><div id="dxy-chart"    style="height:380px;"></div></div>
    </div>
  </div>
</div>

<div class="section">
  <div class="container">
    <div class="section-title">Risk & Statistical Analysis</div>
    <div class="grid-2">
      <div class="card" id="risk-panel"></div>
      <div class="card" id="stats-panel"></div>
    </div>
  </div>
</div>

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

<div class="section" id="comspec-section">
  <div class="container">
    <div class="section-title">Commodity Intelligence — <span id="comspec-title"></span></div>
    <div class="grid-2">
      <div class="card" id="comspec-panel"></div>
      <div class="card" id="comspec-chart" style="min-height:160px; display:flex; justify-content:center; align-items:center;"></div>
    </div>
  </div>
</div>

<footer style="padding:20px; text-align:center; border-top:1px solid var(--border); margin-top:32px;">
  <p style="color:var(--text2); font-size:12px;">
    COM-QUANT &nbsp;&bull;&nbsp; Data from Yahoo Finance &nbsp;&bull;&nbsp; For educational purposes only &nbsp;&bull;&nbsp; Not financial advice
  </p>
  <p style="color:var(--text2); font-size:11px; margin-top:4px;">
    Updated daily via GitHub Actions &nbsp;&bull;&nbsp; Built with ARIMA, Holt-Winters, Monte Carlo & Ornstein-Uhlenbeck models
  </p>
</footer>

<script>
// ── State ─────────────────────────────────────────────────────
let currentCategory  = "precious_metals";
let currentCommodity = "GOLD";
let currentWindow    = "1W";
let chartsInitialized = false;
let initializedDivs = new Set();

// ── Helpers ───────────────────────────────────────────────────
function getData() {{ return COMQUANT_DATA.data[currentCommodity]?.[currentWindow]; }}

function formatPrice(p) {{
    if (p === null || p === undefined) return "N/A";
    if (p >= 1000)  return p.toLocaleString("en-US", {{minimumFractionDigits:2, maximumFractionDigits:2}});
    if (p >= 10)    return p.toFixed(3);
    return p.toFixed(4);
}}

function filterNulls(dates, values) {{
    const fd=[], fv=[];
    if (!dates || !values) return [fd, fv];
    dates.forEach((d,i) => {{ if (values[i] != null) {{ fd.push(d); fv.push(values[i]); }} }});
    return [fd, fv];
}}

function plotLayout(overrides = {{}}) {{
    return Object.assign({{
        paper_bgcolor: "transparent",
        plot_bgcolor:  "transparent",
        font: {{ color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || "#e8eaf6",
                family: "system-ui, -apple-system, sans-serif", size: 12 }},
        xaxis: {{ gridcolor: "#2a2d4a", linecolor: "#3a3d5a", zerolinecolor: "#3a3d5a" }},
        yaxis: {{ gridcolor: "#2a2d4a", linecolor: "#3a3d5a", zerolinecolor: "#3a3d5a" }},
        margin: {{ t: 40, r: 20, b: 40, l: 60 }},
        legend: {{ bgcolor: "transparent", bordercolor: "transparent" }},
        hovermode: "x unified",
    }}, overrides);
}}
const PLOT_CONFIG = {{ displayModeBar: false, responsive: true }};

function drawPlot(divId, traces, layout) {{
    if (initializedDivs.has(divId)) {{
        Plotly.react(divId, traces, layout, PLOT_CONFIG);
    }} else {{
        Plotly.newPlot(divId, traces, layout, PLOT_CONFIG);
        initializedDivs.add(divId);
    }}
}}

// ── State setters ─────────────────────────────────────────────
function setCategory(cat) {{
    currentCategory = cat;
    currentCommodity = COMQUANT_DATA.categories[cat].find(c => COMQUANT_DATA.data[c]) || COMQUANT_DATA.categories[cat][0];
    document.querySelectorAll('#category-tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderAll();
}}

function setCommodity(id) {{
    if (!COMQUANT_DATA.data[id]) return;
    currentCommodity = id;
    renderAll();
}}

function setWindow(win) {{
    currentWindow = win;
    document.querySelectorAll('#window-tabs .tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderAll();
}}

function toggleTheme() {{
    const html = document.documentElement;
    const isLight = html.getAttribute('data-theme') === 'light';
    html.setAttribute('data-theme', isLight ? 'dark' : 'light');
    document.getElementById('theme-btn').textContent = isLight ? '☀ Light' : '☽ Dark';
    renderAll();
}}

// ── Render functions ──────────────────────────────────────────

function renderOverviewCards() {{
    const cat = COMQUANT_DATA.categories[currentCategory];
    const container = document.getElementById("overview-cards");
    container.innerHTML = "";
    cat.forEach(cid => {{
        const d = COMQUANT_DATA.data[cid]?.[currentWindow];
        if (!d) return;
        const change1d = d.meta.price_change_1d_pct;
        const chgClass = change1d >= 0 ? "up" : "down";
        const chgArrow = change1d >= 0 ? "▲" : "▼";
        const signal = d.indicators.composite_signal;
        const badgeCls = signal.includes("Bull") ? "badge-bull" : signal.includes("Bear") ? "badge-bear" : "badge-neut";
        const isActive = cid === currentCommodity ? "active" : "";
        container.innerHTML += `
          <div class="card com-card ${{isActive}}" onclick="setCommodity('${{cid}}')">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div>
                <div class="com-name">${{d.meta.name}}</div>
                <div class="com-ticker">${{d.meta.ticker}}</div>
              </div>
              <span class="badge ${{badgeCls}}">${{signal}}</span>
            </div>
            <div class="com-price">${{formatPrice(d.meta.current_price)}}</div>
            <div class="com-unit">${{d.meta.unit}}</div>
            <div style="display:flex;gap:12px;margin-top:6px;font-size:12px;">
              <span class="${{chgClass}}">${{chgArrow}} ${{Math.abs(change1d).toFixed(2)}}% 1D</span>
              <span class="${{d.meta.price_change_5d_pct >= 0 ? 'up' : 'down'}}">
                ${{d.meta.price_change_5d_pct >= 0 ? "▲" : "▼"}} ${{Math.abs(d.meta.price_change_5d_pct).toFixed(2)}}% 5D
              </span>
            </div>
          </div>`;
    }});
}}

function renderForecastChart() {{
    const d = getData();
    if (!d) return;
    
    document.getElementById("deep-title").textContent = d.meta.name;
    
    const histDates = d.history.dates;
    const histClose = d.history.close;
    const fcDates = d.forecast.dates;
    
    const [aFcDates, arima] = filterNulls(fcDates, d.forecast.arima);
    const [hFcDates, hw] = filterNulls(fcDates, d.forecast.holt_winters);
    const [mcFcDates, mc_p50] = filterNulls(fcDates, d.forecast.monte_carlo_p50);
    const [oFcDates, ou] = filterNulls(fcDates, d.forecast.ou_process);
    const [eFcDates, ensemble] = filterNulls(fcDates, d.forecast.ensemble);
    
    const traces = [];
    
    traces.push({{
        x: histDates, y: histClose, mode: 'lines', name: 'Historical', 
        line: {{color: '#9ba3c9', width: 1.5}}
    }});
    
    const [aCiDates, arima_ci_lower] = filterNulls(fcDates, d.forecast.arima_ci_lower);
    const [, arima_ci_upper] = filterNulls(fcDates, d.forecast.arima_ci_upper);
    if (aCiDates.length > 0) {{
        traces.push({{
            x: aCiDates, y: arima_ci_lower, fill: null, line: {{width: 0}}, showlegend: false, hoverinfo: 'skip'
        }});
        traces.push({{
            x: aCiDates, y: arima_ci_upper, fill: 'tonexty', fillcolor: 'rgba(124,131,253,0.1)', 
            line: {{width: 0}}, name: 'ARIMA 95% CI', hoverinfo: 'skip'
        }});
    }}
    
    if (aFcDates.length > 0) {{
        traces.push({{
            x: aFcDates, y: arima, mode: 'lines', name: 'ARIMA (30%)', 
            line: {{color: '#7c83fd', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (hFcDates.length > 0) {{
        traces.push({{
            x: hFcDates, y: hw, mode: 'lines', name: 'Holt-Winters (30%)', 
            line: {{color: '#ff9f43', dash: 'dash', width: 1.5}}
        }});
    }}
    
    const [mcPDates, mc_p5] = filterNulls(fcDates, d.forecast.monte_carlo_p5);
    const [, mc_p95] = filterNulls(fcDates, d.forecast.monte_carlo_p95);
    if (mcPDates.length > 0) {{
        traces.push({{
            x: mcPDates, y: mc_p5, fill: null, line: {{width: 0}}, showlegend: false, hoverinfo: 'skip'
        }});
        traces.push({{
            x: mcPDates, y: mc_p95, fill: 'tonexty', fillcolor: 'rgba(72,219,251,0.08)', 
            line: {{width: 0}}, name: 'MC Range', hoverinfo: 'skip'
        }});
    }}
    
    if (mcFcDates.length > 0) {{
        traces.push({{
            x: mcFcDates, y: mc_p50, mode: 'lines', name: 'MC Median (25%)', 
            line: {{color: '#48dbfb', dash: 'dot', width: 1}}
        }});
    }}
    
    if (oFcDates.length > 0) {{
        traces.push({{
            x: oFcDates, y: ou, mode: 'lines', name: 'Ornstein-Uhlenbeck (15%)', 
            line: {{color: '#4caf7d', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (eFcDates.length > 0) {{
        traces.push({{
            x: eFcDates, y: ensemble, mode: 'lines', name: 'Ensemble', 
            line: {{color: '#ffd166', width: 2.5}}
        }});
    }}
    
    if (d.forecast.optimal_date && d.forecast.optimal_price) {{
        traces.push({{
            x: [d.forecast.optimal_date], y: [d.forecast.optimal_price], mode: 'markers', 
            marker: {{color: '#4caf7d', size: 10, symbol: 'circle'}}, name: 'Best Entry', hoverinfo: 'x+y'
        }});
    }}
    
    const layout = plotLayout({{
        title: `${{d.meta.name}} — ${{currentWindow}} Forecast (${{d.meta.unit}})`,
        shapes: [
            {{
                type: 'line', x0: histDates[histDates.length-1], x1: histDates[histDates.length-1],
                y0: 0, y1: 1, yref: 'paper', line: {{color: '#2a2d4a', dash: 'dot', width: 1}}
            }}
        ]
    }});
    
    drawPlot("forecast-chart", traces, layout);
}}

function renderOptimalEntry() {{
    const d = getData();
    if (!d) return;
    
    const panel = document.getElementById("optimal-panel");
    const odate = d.forecast.optimal_date || "N/A";
    const oprice = d.forecast.optimal_price;
    const ohdays = d.forecast.optimal_horizon_days || "N/A";
    const pgn = d.forecast.potential_gain_pct;
    
    let moveClass = pgn >= 0 ? "up" : "down";
    let moveArrow = pgn >= 0 ? "↑" : "↓";
    let gainStr = pgn != null ? `${{moveArrow}} ${{Math.abs(pgn).toFixed(2)}}%` : "N/A";
    
    panel.innerHTML = `
        <div style="padding:8px 0;">
          <div class="section-title">Best Entry Window</div>
          <div style="font-size:28px; font-weight:800; color:var(--green); margin:8px 0;">${{odate}}</div>
          <div class="stat-row"><span class="stat-label">Price target</span><span class="stat-value">${{formatPrice(oprice)}} ${{d.meta.unit}}</span></div>
          <div class="stat-row"><span class="stat-label">Days from today</span><span class="stat-value">${{ohdays}}</span></div>
          <div class="stat-row"><span class="stat-label">Potential move</span><span class="stat-value ${{moveClass}}">${{gainStr}}</span></div>
          <div class="stat-row"><span class="stat-label">Current price</span><span class="stat-value">${{formatPrice(d.meta.current_price)}}</span></div>
          <div style="font-size:11px; color:var(--text2); margin-top:12px;">Ensemble model. Not financial advice.</div>
        </div>`;
}}

function renderIndicators() {{
    const d = getData();
    if (!d) return;
    const ind = d.indicators;
    const pnl = document.getElementById("indicators-panel");
    
    const sig = ind.composite_signal;
    let sColor = "var(--text2)";
    if (sig.includes("Bullish")) sColor = "var(--green)";
    else if (sig.includes("Bull")) sColor = "#74b9ff";
    else if (sig.includes("Bearish")) sColor = "var(--red)";
    else if (sig.includes("Bear")) sColor = "#ff7675";
    
    const getBarColor = (val, low, high, isReversed=false) => {{
        if (isReversed) {{
            if (val > high) return "var(--red)";
            if (val < low) return "var(--green)";
            return "var(--text2)";
        }} else {{
            if (val < low) return "var(--red)";
            if (val > high) return "var(--green)";
            return "var(--text2)";
        }}
    }};
    
    let html = `
        <div class="section-title">Technical Signals</div>
        <div class="gauge-wrap">
          <div class="gauge-score">${{ind.composite_score.toFixed(0)}}</div>
          <div class="gauge-label" style="color:${{sColor}}">${{sig}}</div>
          <div style="font-size:11px; color:var(--text2);">Composite 0–100</div>
        </div>
    `;
    
    const addRow = (label, val, pct, bg) => {{
        html += `<div class="ind-row"><span class="ind-label">${{label}}</span><div class="ind-bar-wrap"><div class="ind-bar" style="width:${{Math.min(100, Math.max(0, pct))}}%;background:${{bg}}"></div></div><span class="ind-val">${{val}}</span></div>`;
    }};
    
    addRow("RSI (14)", ind.rsi14.toFixed(1), ind.rsi14, getBarColor(ind.rsi14, 30, 70, true));
    
    const maxMacd = Math.max(0.001, Math.abs(ind.macd_hist) * 2);
    const macdPct = (ind.macd_hist + maxMacd) / (2 * maxMacd) * 100;
    addRow("MACD Hist", ind.macd_hist.toFixed(3), macdPct, ind.macd_hist > 0 ? "var(--green)" : "var(--red)");
    
    addRow("Bollinger %B", ind.bollinger_pct_b.toFixed(2), ind.bollinger_pct_b * 100, getBarColor(ind.bollinger_pct_b, 0.2, 0.8, true));
    addRow("Stoch %K", ind.stochastic_k.toFixed(1), ind.stochastic_k, getBarColor(ind.stochastic_k, 20, 80, true));
    addRow("Williams %R", ind.williams_r.toFixed(1), ind.williams_r + 100, getBarColor(ind.williams_r, -80, -20, true));
    
    const maxCci = 200;
    const cciPct = (ind.cci20 + maxCci) / (2 * maxCci) * 100;
    addRow("CCI (20)", ind.cci20.toFixed(1), cciPct, getBarColor(ind.cci20, -100, 100, true));
    
    const zPct = (ind.zscore20 + 3) / 6 * 100;
    addRow("Z-Score (20)", ind.zscore20.toFixed(2), zPct, getBarColor(ind.zscore20, -2, 2, true));
    
    pnl.innerHTML = html;
}}

function renderSpreads() {{
    const sp = COMQUANT_DATA.spreads;
    
    const gs = sp.gold_silver_ratio;
    if (gs && gs.dates) {{
        const [gDates, gVals] = filterNulls(gs.dates, gs.values);
        const gTraces = [
            {{x: gDates, y: gVals, mode: 'lines', name: 'Ratio', line: {{color: '#ffd166', width: 1.5}}}}
        ];
        const gLayout = plotLayout({{
            title: "Gold/Silver Ratio",
            shapes: [{{type: 'line', x0: 0, x1: 1, xref: 'paper', y0: gs.mean_1y, y1: gs.mean_1y, line: {{color: '#9ba3c9', dash: 'dash', width: 1}}}}]
        }});
        drawPlot("spread-gold-silver", gTraces, gLayout);
        document.getElementById("gold-silver-info").textContent = `Current: ${{gs.current.toFixed(2)}} | 1Y Mean: ${{gs.mean_1y.toFixed(2)}} | Z-Score: ${{gs.z_score.toFixed(2)}} | ${{gs.interpretation}}`;
    }} else {{
        document.getElementById("spread-gold-silver").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;'>Data unavailable</div>";
    }}
    
    const bw = sp.brent_wti_spread;
    if (bw && bw.dates) {{
        const [bDates, bVals] = filterNulls(bw.dates, bw.values);
        const bTraces = [
            {{x: bDates, y: bVals, mode: 'lines', name: 'Spread', line: {{color: '#ff9f43', width: 1.5}}}}
        ];
        const bLayout = plotLayout({{
            title: "Brent-WTI Spread",
            shapes: [{{type: 'line', x0: 0, x1: 1, xref: 'paper', y0: bw.mean_1y, y1: bw.mean_1y, line: {{color: '#9ba3c9', dash: 'dash', width: 1}}}}]
        }});
        drawPlot("spread-brent-wti", bTraces, bLayout);
        document.getElementById("brent-wti-info").textContent = `Current: $${{bw.current.toFixed(2)}}/bbl | 1Y Mean: $${{bw.mean_1y.toFixed(2)}} | Z-Score: ${{bw.z_score.toFixed(2)}}`;
    }} else {{
        document.getElementById("spread-brent-wti").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;'>Data unavailable</div>";
    }}
}}

function renderCorrelationMatrix() {{
    const matrix = COMQUANT_DATA.correlations.matrix;
    if (!matrix) return;
    
    const ids = Object.keys(matrix);
    const labels = ids.map(id => COMQUANT_DATA.data[id]?.["1W"]?.meta?.name || id);
    const z = ids.map(ri => ids.map(ci => matrix[ri]?.[ci] ?? 0));
    
    const trace = {{
        type: 'heatmap', z: z, x: labels, y: labels,
        colorscale: [[0,'#f06969'],[0.5,'#2a2d4a'],[1,'#4caf7d']],
        zmin: -1, zmax: 1,
        text: z.map(row => row.map(v => v.toFixed(2))),
        texttemplate: '%{{text}}', textfont: {{size: 10}},
        hoverongaps: false
    }};
    
    const layout = plotLayout({{ title: "Correlation Matrix", margin: {{t:40, r:20, b:60, l:80}} }});
    drawPlot("corr-heatmap", [trace], layout);
    
    const dxy = COMQUANT_DATA.correlations.dxy_proxy;
    if (dxy) {{
        const dxyIds = Object.keys(dxy).filter(id => COMQUANT_DATA.data[id]?.["1W"]);
        const names = dxyIds.map(id => COMQUANT_DATA.data[id]["1W"].meta.name);
        const vals = dxyIds.map(id => dxy[id]);
        const colors = vals.map(v => v < 0 ? "#4caf7d" : "#f06969");
        
        const dxyTrace = {{ type: 'bar', orientation: 'h', x: vals, y: names, marker: {{color: colors}}, name: 'DXY Corr' }};
        const dxyLayout = plotLayout({{ 
            title: "DXY Sensitivity", 
            xaxis: {{ title: "Correlation with USD Index", range: [-1, 1] }},
            margin: {{t:40, r:20, b:40, l:80}}
        }});
        
        drawPlot("dxy-chart", [dxyTrace], dxyLayout);
    }}
}}

function renderRiskStats() {{
    const d = getData();
    if (!d) return;
    
    const risk = d.risk;
    const stat = d.statistics;
    
    const rPanel = document.getElementById("risk-panel");
    const sPanel = document.getElementById("stats-panel");
    
    const srColor = risk.sharpe_ratio > 1 ? "var(--green)" : risk.sharpe_ratio > 0 ? "var(--orange)" : "var(--red)";
    
    rPanel.innerHTML = `
        <div class="stat-row"><span class="stat-label">VaR 95%</span><span class="stat-value" style="color:var(--red)">${{risk.var_95_pct.toFixed(3)}}%</span></div>
        <div class="stat-row"><span class="stat-label">VaR 99%</span><span class="stat-value" style="color:var(--red)">${{risk.var_99_pct.toFixed(3)}}%</span></div>
        <div class="stat-row"><span class="stat-label">CVaR 95%</span><span class="stat-value" style="color:var(--red)">${{risk.cvar_95_pct.toFixed(3)}}%</span></div>
        <div class="stat-row"><span class="stat-label">Max Drawdown</span><span class="stat-value" style="color:var(--red)">${{risk.max_drawdown_pct.toFixed(2)}}%</span></div>
        <div class="stat-row"><span class="stat-label">Sharpe Ratio</span><span class="stat-value" style="color:${{srColor}}">${{risk.sharpe_ratio.toFixed(2)}}</span></div>
        <div class="stat-row"><span class="stat-label">Sortino Ratio</span><span class="stat-value">${{risk.sortino_ratio?.toFixed(2) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">DCA 5-day avg</span><span class="stat-value">${{formatPrice(risk.dca_5d_avg)}}</span></div>
        <div class="stat-row"><span class="stat-label">DCA 10-day avg</span><span class="stat-value">${{formatPrice(risk.dca_10d_avg)}}</span></div>
    `;
    
    sPanel.innerHTML = `
        <div class="stat-row"><span class="stat-label">Hurst Exponent</span><span class="stat-value">${{stat.hurst.toFixed(3)}} — ${{stat.hurst_regime}}</span></div>
        <div class="stat-row"><span class="stat-label">Skewness</span><span class="stat-value">${{stat.skewness.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">Excess Kurtosis</span><span class="stat-value">${{stat.kurtosis_excess.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">ADF p-value</span><span class="stat-value">${{stat.adf_pvalue?.toFixed(4) ?? 'N/A'}} (${{stat.adf_stationary ? '✓ Stationary' : '✗ Non-stationary'}})</span></div>
        <div class="stat-row"><span class="stat-label">Jarque-Bera p</span><span class="stat-value">${{stat.jarque_bera_pvalue?.toFixed(4) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">Ann. Vol (10d)</span><span class="stat-value">${{stat.annualized_vol_10d?.toFixed(2) ?? 'N/A'}}%</span></div>
        <div class="stat-row"><span class="stat-label">Ann. Vol (20d)</span><span class="stat-value">${{stat.annualized_vol_20d?.toFixed(2) ?? 'N/A'}}%</span></div>
        <div class="stat-row"><span class="stat-label">Ann. Vol (30d)</span><span class="stat-value">${{stat.annualized_vol_30d?.toFixed(2) ?? 'N/A'}}%</span></div>
        <div class="stat-row"><span class="stat-label">Mean Daily Ret</span><span class="stat-value">${{stat.mean_daily_return_pct.toFixed(4)}}%</span></div>
    `;
}}

function renderSeasonality() {{
    const d = getData();
    if (!d) return;
    
    document.getElementById("seas-title").textContent = d.meta.name;
    const s = d.seasonality;
    
    const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
    const dVals = days.map(d => (s.day_of_week[d] || 0) * 100);
    const dColors = dVals.map(v => v >= 0 ? "#4caf7d" : "#f06969");
    drawPlot("seas-dow", [{{ type: 'bar', x: days.map(d => d.substr(0,3)), y: dVals, marker: {{color: dColors}} }}], plotLayout({{title: "Day of Week (%)", margin: {{t:30, r:10, b:30, l:40}}}}));
    
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const mVals = months.map(m => (s.monthly[m] || 0) * 100);
    const mColors = mVals.map(v => v >= 0 ? "#4caf7d" : "#f06969");
    drawPlot("seas-mon", [{{ type: 'bar', x: months, y: mVals, marker: {{color: mColors}} }}], plotLayout({{title: "Monthly (%)", margin: {{t:30, r:10, b:30, l:40}}}}));
    
    if (d.meta.category === "agriculture" && d.commodity_specific && d.commodity_specific.quarterly_seasonality) {{
        const qs = d.commodity_specific.quarterly_seasonality;
        const qtrs = ["Q1", "Q2", "Q3", "Q4"];
        const qVals = qtrs.map(q => (qs[q] || 0) * 100);
        const qColors = qVals.map(v => v >= 0 ? "#4caf7d" : "#f06969");
        drawPlot("seas-qtr", [{{ type: 'bar', x: qtrs, y: qVals, marker: {{color: qColors}} }}], plotLayout({{title: "Quarterly (%)", margin: {{t:30, r:10, b:30, l:40}}}}));
    }} else {{
        document.getElementById("seas-qtr").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;text-align:center;padding:20px;color:var(--text2)'>Quarterly seasonality data available for agricultural commodities</div>";
    }}
    
    document.getElementById("seas-summary").textContent = `Historically best day: ${{s.best_day}} • Best month: ${{s.best_month}} | Historical averages, not guarantees`;
}}

function renderRankings() {{
    const ids = Object.keys(COMQUANT_DATA.data);
    
    let infArr = [];
    let dxyArr = [];
    
    ids.forEach(id => {{
        const d1w = COMQUANT_DATA.data[id]?.["1W"];
        if (d1w) {{
            const cs = d1w.commodity_specific;
            infArr.push({{id: id, name: d1w.meta.name, val: cs.inflation_hedge_score}});
            
            const dx = COMQUANT_DATA.correlations?.dxy_proxy?.[id];
            if (dx !== undefined) {{
                dxyArr.push({{id: id, name: d1w.meta.name, val: dx}});
            }}
        }}
    }});
    
    infArr.sort((a,b) => a.val - b.val);
    const infTrace = {{
        type: 'bar', orientation: 'h', 
        x: infArr.map(x => x.val), y: infArr.map(x => x.name),
        marker: {{color: infArr.map(x => x.id === "GOLD" ? "#ffd166" : "#4caf7d")}}
    }};
    drawPlot("inflation-chart", [infTrace], plotLayout({{margin: {{t:20, r:20, b:30, l:100}}, xaxis: {{range: [0, 1]}}}}));
    
    dxyArr.sort((a,b) => a.val - b.val);
    const dxyTrace = {{
        type: 'bar', orientation: 'h',
        x: dxyArr.map(x => x.val), y: dxyArr.map(x => x.name),
        marker: {{color: dxyArr.map(x => x.val < 0 ? "#4caf7d" : "#f06969")}}
    }};
    drawPlot("dxy-rank-chart", [dxyTrace], plotLayout({{margin: {{t:20, r:20, b:30, l:100}}, xaxis: {{range: [-1, 1]}}}}));
}}

function renderCommoditySpecific() {{
    const sec = document.getElementById("comspec-section");
    if (currentCommodity === "GOLD") {{
        sec.style.display = "none";
        return;
    }}
    sec.style.display = "block";
    
    const d = getData();
    if (!d) return;
    
    document.getElementById("comspec-title").textContent = d.meta.name;
    const cs = d.commodity_specific;
    const pnl = document.getElementById("comspec-panel");
    
    let contColor = "var(--text2)";
    if (cs.contango_indicator.includes("Backwardation")) contColor = "var(--green)";
    else if (cs.contango_indicator.includes("Contango")) contColor = "var(--red)";
    
    const hl = d.forecast.half_life_days || d.commodity_specific.half_life_days;
    const hlStr = hl ? `${{hl.toFixed(1)}} days to revert 50% of deviation` : "N/A";
    
    pnl.innerHTML = `
        <div class="stat-row"><span class="stat-label">Inflation Hedge Score</span><span class="stat-value">${{cs.inflation_hedge_score.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">DXY Correlation</span><span class="stat-value">${{cs.dxy_correlation_3m?.toFixed(3) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">Price vs 1Y Mean</span><span class="stat-value">${{cs.price_vs_1y_mean_pct.toFixed(2)}}% (${{cs.price_vs_1y_mean_zscore.toFixed(2)}} σ)</span></div>
        <div class="stat-row"><span class="stat-label">Contango Indicator</span><span class="stat-value" style="color:${{contColor}}">${{cs.contango_indicator}}</span></div>
        <div class="stat-row"><span class="stat-label">OU Half-Life</span><span class="stat-value">${{hlStr}}</span></div>
    `;
    
    const z = cs.price_vs_1y_mean_zscore;
    const zTrace = {{
        type: 'indicator', mode: 'gauge+number', value: z, title: {{text: "Z-Score vs 1Y Mean"}},
        gauge: {{
            axis: {{range: [-3, 3]}},
            bar: {{color: z > 0 ? '#4caf7d' : '#f06969'}},
            steps: [
                {{range: [-3, -1.5], color: 'rgba(240,105,105,0.2)'}},
                {{range: [-1.5, 1.5], color: 'rgba(124,131,253,0.1)'}},
                {{range: [1.5, 3], color: 'rgba(76,175,125,0.2)'}}
            ]
        }}
    }};
    drawPlot("comspec-chart", [zTrace], plotLayout({{margin: {{t:40, b:20, l:30, r:30}}}}));
}}

function renderAll() {{
    renderOverviewCards();
    renderForecastChart();
    renderOptimalEntry();
    renderIndicators();
    renderRiskStats();
    renderSeasonality();
    renderCommoditySpecific();
    if (!chartsInitialized) {{
        renderSpreads();
        renderCorrelationMatrix();
        renderRankings();
        chartsInitialized = true;
    }}
}}

document.addEventListener("DOMContentLoaded", () => {{
    const ts = new Date(COMQUANT_DATA.generated_at);
    document.getElementById("updated-ts").textContent = "Updated: " + ts.toUTCString().replace(" GMT","") + " UTC";
    renderAll();
}});
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
