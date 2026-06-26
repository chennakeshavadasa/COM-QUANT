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
<title>COM-QUANT — Advanced Commodities Analytics</title>
<script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
  --bg:       #0B0E14;
  --surface:  rgba(26, 29, 46, 0.7);
  --surface2: rgba(36, 39, 64, 0.8);
  --border:   rgba(255, 255, 255, 0.08);
  --text:     #F3F4F6;
  --text2:    #9CA3AF;
  --accent:   #6366F1;
  --accent-hover: #818CF8;
  --green:    #10B981;
  --red:      #EF4444;
  --gold:     #F59E0B;
  --orange:   #F97316;
  --teal:     #06B6D4;
  --radius:   12px;
  --max-width: 1400px;
  --shadow:   0 8px 32px 0 rgba(0, 0, 0, 0.3);
  --blur:     backdrop-filter: blur(12px);
}}

[data-theme="light"] {{
  --bg:      #F3F4F6;
  --surface: rgba(255, 255, 255, 0.8);
  --surface2:rgba(243, 244, 246, 0.9);
  --border:  rgba(0, 0, 0, 0.08);
  --text:    #111827;
  --text2:   #4B5563;
  --shadow:  0 8px 32px 0 rgba(31, 38, 135, 0.07);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
body {{ 
  background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.6; 
  transition: background 0.3s, color 0.3s; 
  background-image: radial-gradient(circle at top right, rgba(99, 102, 241, 0.05), transparent 40%);
}}
.container {{ max-width: var(--max-width); margin: 0 auto; padding: 0 20px; }}
.section {{ padding: 32px 0; border-bottom: 1px solid var(--border); }}
.section-title {{ font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text2); margin-bottom: 20px; }}

.card {{ 
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); 
  padding: 20px; box-shadow: var(--shadow); var(--blur);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4); }}

@keyframes fadeUp {{
  0% {{ opacity: 0; transform: translateY(20px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

.card:nth-child(1) {{ animation-delay: 0.05s; }}
.card:nth-child(2) {{ animation-delay: 0.1s; }}
.card:nth-child(3) {{ animation-delay: 0.15s; }}
.card:nth-child(4) {{ animation-delay: 0.2s; }}

.badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; letter-spacing: 0.05em; }}
.badge-bull  {{ background: rgba(16, 185, 129, 0.15); color: var(--green); }}
.badge-bear  {{ background: rgba(239, 68, 68, 0.15); color: var(--red); }}
.badge-neut  {{ background: rgba(99, 102, 241, 0.15); color: var(--accent); }}

.up   {{ color: var(--green); font-weight: 600; }}
.down {{ color: var(--red); font-weight: 600; }}

.tab-group {{ display: flex; gap: 6px; flex-wrap: wrap; }}
.tab {{ 
  padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface2); 
  color: var(--text2); cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s ease; 
}}
.tab:hover {{ border-color: var(--accent); color: var(--text); background: rgba(99, 102, 241, 0.1); }}
.tab.active {{ background: var(--accent); border-color: var(--accent); color: #fff; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }}

.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
.grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
@media (max-width: 1024px) {{ .grid-4 {{ grid-template-columns: repeat(2, 1fr); }} .grid-3 {{ grid-template-columns: 1fr 1fr; }} }}
@media (max-width: 640px)  {{ .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }} }}

.com-card {{ cursor: pointer; transition: all 0.2s ease; border: 2px solid transparent; background: var(--surface2); }}
.com-card:hover {{ border-color: var(--accent-hover); }}
.com-card.active {{ border-color: var(--accent); box-shadow: 0 0 20px rgba(99, 102, 241, 0.2); background: var(--surface); }}
.com-card .com-name {{ font-weight: 700; font-size: 15px; }}
.com-card .com-ticker {{ font-size: 12px; color: var(--text2); font-weight: 500; }}
.com-card .com-price {{ font-size: 24px; font-weight: 800; margin: 8px 0 4px; letter-spacing: -0.02em; }}
.com-card .com-unit {{ font-size: 11px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.05em; }}

.stat-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px; }}
.stat-row:last-child {{ border-bottom: none; }}
.stat-label {{ color: var(--text2); font-weight: 500; }}
.stat-value {{ font-weight: 700; }}

.ind-row {{ display: flex; align-items: center; gap: 12px; padding: 6px 0; font-size: 13px; }}
.ind-label {{ width: 100px; color: var(--text2); flex-shrink: 0; font-weight: 500; }}
.ind-bar-wrap {{ flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }}
.ind-bar {{ height: 100%; border-radius: 3px; transition: width 0.5s ease; }}
.ind-val {{ width: 60px; text-align: right; font-weight: 700; }}

.gauge-wrap {{ text-align: center; padding: 16px 0; }}
.gauge-score {{ font-size: 48px; font-weight: 800; color: var(--accent); letter-spacing: -0.03em; }}
.gauge-label {{ font-size: 16px; font-weight: 700; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.05em; }}

.plotly-container {{ width: 100%; }}
</style>
</head>
<body>
<script>
  const COMQUANT_DATA = {data_json_str};
</script>

<header style="background: var(--surface); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; var(--blur);">
  <div class="container" style="display:flex; justify-content:space-between; align-items:center; padding:16px 20px;">
    <div style="display:flex; align-items:center; gap: 16px;">
      <div style="background: linear-gradient(135deg, var(--accent), var(--teal)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size:26px; font-weight:900; letter-spacing: -0.05em;">COM-QUANT</div>
      <div style="height: 24px; width: 1px; background: var(--border);"></div>
      <div style="font-size:14px; color:var(--text2); font-weight: 500; display: none; @media (min-width: 640px) {{ display: block; }}">Advanced Commodities Analytics</div>
    </div>
    <div style="display:flex; align-items:center; gap:16px;">
      <span id="updated-ts" style="font-size:12px; color:var(--text2); font-weight: 500;"></span>
      <button onclick="toggleTheme()" style="padding:8px 16px; border-radius:8px; border:1px solid var(--border); background:var(--surface2); color:var(--text); cursor:pointer; font-size:13px; font-weight: 600; transition: all 0.2s;" id="theme-btn">☀ Light</button>
    </div>
  </div>
  <div class="container" style="padding:12px 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap: wrap; gap: 12px;">
    <div class="tab-group" id="category-tabs">
      <button class="tab active" onclick="setCategory('precious_metals')">✦ Precious Metals</button>
      <button class="tab"        onclick="setCategory('industrial_metals')">🏗 Industrial</button>
      <button class="tab"        onclick="setCategory('energy')">⚡ Energy</button>
      <button class="tab"        onclick="setCategory('agriculture')">⬡ Agriculture</button>
      <button class="tab"        onclick="setCategory('livestock')">🐄 Livestock</button>
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
    <div class="section-title">Deep Analysis — <span id="deep-title" style="color: var(--text);"></span></div>
    <div class="card" style="margin-bottom:20px;">
      <div id="forecast-chart" style="height:450px;"></div>
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
        <div id="spread-gold-silver" style="height:280px;"></div>
        <div id="gold-silver-info" style="margin-top:12px; font-size:13px; font-weight: 500; color:var(--text2); text-align: center;"></div>
      </div>
      <div class="card">
        <div id="spread-brent-wti" style="height:280px;"></div>
        <div id="brent-wti-info" style="margin-top:12px; font-size:13px; font-weight: 500; color:var(--text2); text-align: center;"></div>
      </div>
    </div>
  </div>
</div>

<div class="section">
  <div class="container">
    <div class="section-title">Commodity Correlations (3-Month)</div>
    <div style="display:grid; grid-template-columns:2fr 1fr; gap:20px;">
      <div class="card"><div id="corr-heatmap" style="height:420px;"></div></div>
      <div class="card"><div id="dxy-chart"    style="height:420px;"></div></div>
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
    <div class="section-title">Seasonality Analysis — <span id="seas-title" style="color: var(--text);"></span></div>
    <div class="grid-3">
      <div class="card"><div id="seas-dow"  style="height:250px;"></div></div>
      <div class="card"><div id="seas-mon"  style="height:250px;"></div></div>
      <div class="card"><div id="seas-qtr"  style="height:250px;"></div></div>
    </div>
    <div style="margin-top:12px; font-size:13px; font-weight:500; color:var(--text2); text-align: center;" id="seas-summary"></div>
  </div>
</div>

<div class="section">
  <div class="container">
    <div class="section-title">Commodity Rankings</div>
    <div class="grid-2">
      <div class="card">
        <div class="section-title" style="font-size: 13px;">Inflation Hedge Score (vs Gold benchmark)</div>
        <div id="inflation-chart" style="height:350px;"></div>
      </div>
      <div class="card">
        <div class="section-title" style="font-size: 13px;">DXY Sensitivity (correlation with USD)</div>
        <div id="dxy-rank-chart" style="height:350px;"></div>
      </div>
    </div>
  </div>
</div>

<div class="section" id="comspec-section">
  <div class="container">
    <div class="section-title">Commodity Intelligence — <span id="comspec-title" style="color: var(--text);"></span></div>
    <div class="grid-2">
      <div class="card" id="comspec-panel"></div>
      <div class="card"><div id="comspec-chart" style="height:250px; width:100%;"></div></div>
    </div>
  </div>
</div>

<footer style="padding:32px 20px; text-align:center; background: var(--surface); border-top:1px solid var(--border); margin-top:40px;">
  <p style="color:var(--text); font-size:14px; font-weight: 600;">
    COM-QUANT &nbsp;&bull;&nbsp; Advanced Algorithmic Analytics
  </p>
  <p style="color:var(--text2); font-size:12px; margin-top:8px; max-width: 600px; margin-left: auto; margin-right: auto;">
    Data sourced from Yahoo Finance. This dashboard is fully automated via GitHub Actions and uses ARIMA, Holt-Winters, Monte Carlo, Ornstein-Uhlenbeck, and SVR models. For educational and research purposes only. Not financial advice.
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

function getThemeColors() {{
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {{
        text: isDark ? '#F3F4F6' : '#111827',
        text2: isDark ? '#9CA3AF' : '#4B5563',
        border: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
        surface: isDark ? '#1A1D2E' : '#FFFFFF',
        bg: isDark ? '#0B0E14' : '#F3F4F6'
    }};
}}

function plotLayout(overrides = {{}}) {{
    const colors = getThemeColors();

    return Object.assign({{
        paper_bgcolor: 'transparent',
        plot_bgcolor:  'transparent',
        font: {{ color: colors.text, family: "'Inter', sans-serif", size: 14 }},
        xaxis: {{ 
            gridcolor: colors.border, linecolor: colors.border, zerolinecolor: colors.border,
            showticklabels: true, tickfont: {{ color: colors.text, size: 12 }}
        }},
        yaxis: {{ 
            gridcolor: colors.border, linecolor: colors.border, zerolinecolor: colors.border,
            showticklabels: true, tickfont: {{ color: colors.text, size: 12 }}
        }},
        margin: {{ t: 50, r: 20, b: 50, l: 60 }},
        legend: {{ bgcolor: "rgba(0,0,0,0.2)", bordercolor: colors.border, borderwidth: 1, font: {{size: 12}} }},
        hovermode: "x unified",
        hoverlabel: {{ bgcolor: colors.surface, font: {{ color: colors.text, family: "'Inter', sans-serif", size: 13 }}, bordercolor: colors.border }}
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
    const availableInCat = COMQUANT_DATA.categories[cat].filter(c => COMQUANT_DATA.data[c]);
    currentCommodity = availableInCat.length > 0 ? availableInCat[0] : null;
    
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
    
    // Force re-render of all charts to update colors
    chartsInitialized = false; 
    initializedDivs.clear();
    renderAll();
}}

// ── Render functions ──────────────────────────────────────────

function renderOverviewCards() {{
    if (!currentCommodity) return;
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
            <div style="display:flex;gap:12px;margin-top:12px;font-size:13px;font-weight:600;">
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
    const [sFcDates, svr] = filterNulls(fcDates, d.forecast.svr);
    const [rFcDates, rf] = filterNulls(fcDates, d.forecast.rf);
    const [eFcDates, ensemble] = filterNulls(fcDates, d.forecast.ensemble);
    
    const traces = [];
    const colors = getThemeColors();
    
    traces.push({{
        x: histDates, y: histClose, mode: 'lines', name: 'Historical', 
        line: {{color: colors.text2, width: 2}}
    }});
    
    const [aCiDates, arima_ci_lower] = filterNulls(fcDates, d.forecast.arima_ci_lower);
    const [, arima_ci_upper] = filterNulls(fcDates, d.forecast.arima_ci_upper);
    if (aCiDates.length > 0) {{
        traces.push({{
            x: aCiDates, y: arima_ci_lower, fill: null, line: {{width: 0}}, showlegend: false, hoverinfo: 'skip'
        }});
        traces.push({{
            x: aCiDates, y: arima_ci_upper, fill: 'tonexty', fillcolor: 'rgba(99, 102, 241, 0.1)', 
            line: {{width: 0}}, name: 'ARIMA 95% CI', hoverinfo: 'skip'
        }});
    }}
    
    if (aFcDates.length > 0) {{
        traces.push({{
            x: aFcDates, y: arima, mode: 'lines', name: 'ARIMA (25%)', 
            line: {{color: '#6366F1', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (hFcDates.length > 0) {{
        traces.push({{
            x: hFcDates, y: hw, mode: 'lines', name: 'Holt-Winters (25%)', 
            line: {{color: '#F97316', dash: 'dash', width: 1.5}}
        }});
    }}
    
    const [mcPDates, mc_p5] = filterNulls(fcDates, d.forecast.monte_carlo_p5);
    const [, mc_p95] = filterNulls(fcDates, d.forecast.monte_carlo_p95);
    if (mcPDates.length > 0) {{
        traces.push({{
            x: mcPDates, y: mc_p5, fill: null, line: {{width: 0}}, showlegend: false, hoverinfo: 'skip'
        }});
        traces.push({{
            x: mcPDates, y: mc_p95, fill: 'tonexty', fillcolor: 'rgba(6, 182, 212, 0.08)', 
            line: {{width: 0}}, name: 'MC Range', hoverinfo: 'skip'
        }});
    }}
    
    if (mcFcDates.length > 0) {{
        traces.push({{
            x: mcFcDates, y: mc_p50, mode: 'lines', name: 'MC Median (20%)', 
            line: {{color: '#06B6D4', dash: 'dot', width: 1.5}}
        }});
    }}
    
    if (oFcDates.length > 0) {{
        traces.push({{
            x: oFcDates, y: ou, mode: 'lines', name: 'Ornstein-Uhlenbeck (15%)', 
            line: {{color: '#10B981', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (sFcDates.length > 0) {{
        traces.push({{
            x: sFcDates, y: svr, mode: 'lines', name: 'SVR (15%)', 
            line: {{color: '#EC4899', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (rFcDates.length > 0) {{
        traces.push({{
            x: rFcDates, y: rf, mode: 'lines', name: 'Random Forest (10%)', 
            line: {{color: '#8B5CF6', dash: 'dash', width: 1.5}}
        }});
    }}
    
    if (eFcDates.length > 0) {{
        traces.push({{
            x: eFcDates, y: ensemble, mode: 'lines', name: 'Ensemble', 
            line: {{color: '#F59E0B', width: 3}}
        }});
    }}
    
    if (d.forecast.optimal_date && d.forecast.optimal_price) {{
        traces.push({{
            x: [d.forecast.optimal_date], y: [d.forecast.optimal_price], mode: 'markers', 
            marker: {{color: '#10B981', size: 12, symbol: 'diamond', line: {{color: '#fff', width: 1}}}}, 
            name: 'Best Entry', hoverinfo: 'x+y'
        }});
    }}
    
    const layout = plotLayout({{
        title: {{ text: `${{d.meta.name}} — ${{currentWindow}} Forecast (${{d.meta.unit}})`, font: {{size: 16, weight: 700}} }},
        shapes: [
            {{
                type: 'line', x0: histDates[histDates.length-1], x1: histDates[histDates.length-1],
                y0: 0, y1: 1, yref: 'paper', line: {{color: colors.border, dash: 'dot', width: 2}}
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
        <div style="padding:12px 0;">
          <div class="section-title">Best Entry Window</div>
          <div style="font-size:36px; font-weight:800; color:var(--green); margin:12px 0; letter-spacing:-0.03em;">${{odate}}</div>
          <div class="stat-row"><span class="stat-label">Price target</span><span class="stat-value">${{formatPrice(oprice)}} ${{d.meta.unit}}</span></div>
          <div class="stat-row"><span class="stat-label">Days from today</span><span class="stat-value">${{ohdays}}</span></div>
          <div class="stat-row"><span class="stat-label">Potential move</span><span class="stat-value ${{moveClass}}">${{gainStr}}</span></div>
          <div class="stat-row"><span class="stat-label">Current price</span><span class="stat-value">${{formatPrice(d.meta.current_price)}}</span></div>
          <div style="font-size:12px; color:var(--text2); margin-top:20px; font-style:italic;">Calculated via weighted model ensemble. Not financial advice.</div>
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
    else if (sig.includes("Bull")) sColor = "#34D399";
    else if (sig.includes("Bearish")) sColor = "var(--red)";
    else if (sig.includes("Bear")) sColor = "#F87171";
    
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
          <div style="font-size:12px; color:var(--text2); margin-top:4px; font-weight:500;">Composite Score 0–100</div>
        </div>
        <div style="margin-top: 16px;">
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
    
    html += `</div>`;
    pnl.innerHTML = html;
}}

function renderSpreads() {{
    const sp = COMQUANT_DATA.spreads;
    const colors = getThemeColors();
    
    const gs = sp.gold_silver_ratio;
    if (gs && gs.dates) {{
        const [gDates, gVals] = filterNulls(gs.dates, gs.values);
        const gTraces = [
            {{x: gDates, y: gVals, mode: 'lines', name: 'Ratio', line: {{color: '#F59E0B', width: 2}}}}
        ];
        const gLayout = plotLayout({{
            title: "Gold / Silver Ratio",
            shapes: [{{type: 'line', x0: 0, x1: 1, xref: 'paper', y0: gs.mean_1y, y1: gs.mean_1y, line: {{color: colors.text2, dash: 'dash', width: 2}}}}]
        }});
        drawPlot("spread-gold-silver", gTraces, gLayout);
        document.getElementById("gold-silver-info").innerHTML = `Current: <strong>${{gs.current.toFixed(2)}}</strong> &nbsp;|&nbsp; 1Y Mean: <strong>${{gs.mean_1y.toFixed(2)}}</strong> &nbsp;|&nbsp; Z-Score: <strong>${{gs.z_score.toFixed(2)}}</strong><br><span style="color:var(--accent);">${{gs.interpretation}}</span>`;
    }} else {{
        document.getElementById("spread-gold-silver").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;font-weight:600;'>Data unavailable</div>";
    }}
    
    const bw = sp.brent_wti_spread;
    if (bw && bw.dates) {{
        const [bDates, bVals] = filterNulls(bw.dates, bw.values);
        const bTraces = [
            {{x: bDates, y: bVals, mode: 'lines', name: 'Spread', line: {{color: '#F97316', width: 2}}}}
        ];
        const bLayout = plotLayout({{
            title: "Brent - WTI Spread",
            shapes: [{{type: 'line', x0: 0, x1: 1, xref: 'paper', y0: bw.mean_1y, y1: bw.mean_1y, line: {{color: colors.text2, dash: 'dash', width: 2}}}}]
        }});
        drawPlot("spread-brent-wti", bTraces, bLayout);
        document.getElementById("brent-wti-info").innerHTML = `Current: <strong>$${{bw.current.toFixed(2)}}/bbl</strong> &nbsp;|&nbsp; 1Y Mean: <strong>$${{bw.mean_1y.toFixed(2)}}</strong> &nbsp;|&nbsp; Z-Score: <strong>${{bw.z_score.toFixed(2)}}</strong>`;
    }} else {{
        document.getElementById("spread-brent-wti").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;font-weight:600;'>Data unavailable</div>";
    }}
}}

function renderCorrelationMatrix() {{
    const matrix = COMQUANT_DATA.correlations;
    if (!matrix) return;
    
    // Filter to only IDs that exist in data and ignore dxy_proxy which is a special key
    const ids = Object.keys(matrix).filter(id => id !== "dxy_proxy" && COMQUANT_DATA.data[id] && COMQUANT_DATA.data[id]["1W"]);
    if (ids.length === 0) return;

    const labels = ids.map(id => COMQUANT_DATA.data[id]["1W"].meta.name);
    const z = ids.map(ri => ids.map(ci => matrix[ri]?.[ci] ?? 0));
    
    const colors = getThemeColors();
    
    const trace = {{
        type: 'heatmap', z: z, x: labels, y: labels,
        colorscale: [[0,'#EF4444'],[0.5,colors.surface],[1,'#10B981']],
        zmin: -1, zmax: 1,
        text: z.map(row => row.map(v => v.toFixed(2))),
        texttemplate: '%{{text}}', textfont: {{size: 11, family: 'Inter', color: colors.text}},
        hoverongaps: false
    }};
    
    const layout = plotLayout({{ title: "Correlation Matrix (3 Months)", margin: {{t:60, r:20, b:100, l:120}} }});
    drawPlot("corr-heatmap", [trace], layout);
    
    const dxy = COMQUANT_DATA.correlations.dxy_proxy;
    if (dxy) {{
        const dxyIds = Object.keys(dxy).filter(id => COMQUANT_DATA.data[id] && COMQUANT_DATA.data[id]["1W"]);
        const names = dxyIds.map(id => COMQUANT_DATA.data[id]["1W"].meta.name);
        const vals = dxyIds.map(id => dxy[id]);
        const barColors = vals.map(v => v < 0 ? "#10B981" : "#EF4444");
        
        const dxyTrace = {{ type: 'bar', orientation: 'h', x: vals, y: names, marker: {{color: barColors}}, name: 'DXY Corr' }};
        const dxyLayout = plotLayout({{ 
            title: "Sensitivity to USD (DXY)", 
            xaxis: {{ title: "Correlation", range: [-1, 1], showticklabels: true }},
            margin: {{t:60, r:40, b:60, l:120}}
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
        <div class="stat-row"><span class="stat-label">VaR (95%)</span><span class="stat-value" style="color:var(--red)">${{risk.var_95_pct.toFixed(2)}}%</span></div>
        <div class="stat-row"><span class="stat-label">VaR (99%)</span><span class="stat-value" style="color:var(--red)">${{risk.var_99_pct.toFixed(2)}}%</span></div>
        <div class="stat-row"><span class="stat-label">CVaR (95%)</span><span class="stat-value" style="color:var(--red)">${{risk.cvar_95_pct.toFixed(2)}}%</span></div>
        <div class="stat-row"><span class="stat-label">Max Drawdown</span><span class="stat-value" style="color:var(--red)">${{risk.max_drawdown_pct.toFixed(2)}}%</span></div>
        <div class="stat-row"><span class="stat-label">Sharpe Ratio</span><span class="stat-value" style="color:${{srColor}}">${{risk.sharpe_ratio.toFixed(2)}}</span></div>
        <div class="stat-row"><span class="stat-label">Sortino Ratio</span><span class="stat-value">${{risk.sortino_ratio?.toFixed(2) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">DCA 5-Day Avg</span><span class="stat-value">${{formatPrice(risk.dca_5d_avg)}}</span></div>
        <div class="stat-row"><span class="stat-label">DCA 10-Day Avg</span><span class="stat-value">${{formatPrice(risk.dca_10d_avg)}}</span></div>
    `;
    
    sPanel.innerHTML = `
        <div class="stat-row"><span class="stat-label">Hurst Exponent</span><span class="stat-value">${{stat.hurst.toFixed(3)}} — <span style="color:var(--accent)">${{stat.hurst_regime}}</span></span></div>
        <div class="stat-row"><span class="stat-label">Skewness</span><span class="stat-value">${{stat.skewness.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">Excess Kurtosis</span><span class="stat-value">${{stat.kurtosis_excess.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">ADF p-value</span><span class="stat-value">${{stat.adf_pvalue?.toFixed(4) ?? 'N/A'}} (${{stat.adf_stationary ? '✓ Stationary' : '✗ Non-stationary'}})</span></div>
        <div class="stat-row"><span class="stat-label">Jarque-Bera p</span><span class="stat-value">${{stat.jarque_bera_pvalue?.toFixed(4) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">Ann. Vol (10d)</span><span class="stat-value">${{stat.annualized_vol_10d?.toFixed(2) ?? 'N/A'}}%</span></div>
        <div class="stat-row"><span class="stat-label">Ann. Vol (20d)</span><span class="stat-value">${{stat.annualized_vol_20d?.toFixed(2) ?? 'N/A'}}%</span></div>
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
    const dColors = dVals.map(v => v >= 0 ? "#10B981" : "#EF4444");
    drawPlot("seas-dow", [{{ type: 'bar', x: days.map(d => d.substr(0,3)), y: dVals, marker: {{color: dColors}} }}], plotLayout({{title: "Day of Week (%)", margin: {{t:40, r:10, b:40, l:40}}}}));
    
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const mVals = months.map(m => (s.monthly[m] || 0) * 100);
    const mColors = mVals.map(v => v >= 0 ? "#10B981" : "#EF4444");
    drawPlot("seas-mon", [{{ type: 'bar', x: months, y: mVals, marker: {{color: mColors}} }}], plotLayout({{title: "Monthly (%)", margin: {{t:40, r:10, b:40, l:40}}}}));
    
    if (d.meta.category === "agriculture" && d.commodity_specific && d.commodity_specific.quarterly_seasonality) {{
        const qs = d.commodity_specific.quarterly_seasonality;
        const qtrs = ["Q1", "Q2", "Q3", "Q4"];
        const qVals = qtrs.map(q => (qs[q] || 0) * 100);
        const qColors = qVals.map(v => v >= 0 ? "#10B981" : "#EF4444");
        drawPlot("seas-qtr", [{{ type: 'bar', x: qtrs, y: qVals, marker: {{color: qColors}} }}], plotLayout({{title: "Quarterly (%)", margin: {{t:40, r:10, b:40, l:40}}}}));
    }} else {{
        document.getElementById("seas-qtr").innerHTML = "<div style='display:flex;height:100%;align-items:center;justify-content:center;text-align:center;padding:20px;color:var(--text2);font-weight:600;'>Quarterly seasonality data only available for Agriculture</div>";
    }}
    
    document.getElementById("seas-summary").textContent = `Historically Best Day: ${{s.best_day}} • Best Month: ${{s.best_month}} | (Historical averages do not guarantee future performance)`;
}}

function renderRankings() {{
    const ids = Object.keys(COMQUANT_DATA.data);
    
    let infArr = [];
    let dxyArr = [];
    
    ids.forEach(id => {{
        const d1w = COMQUANT_DATA.data[id]?.["1W"];
        if (d1w) {{
            const cs = d1w.commodity_specific;
            if (cs && cs.inflation_hedge_score !== undefined) {{
                infArr.push({{id: id, name: d1w.meta.name, val: cs.inflation_hedge_score}});
            }}
            
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
        marker: {{color: infArr.map(x => x.id === "GOLD" ? "#F59E0B" : "#10B981")}}
    }};
    drawPlot("inflation-chart", [infTrace], plotLayout({{margin: {{t:30, r:40, b:50, l:120}}, xaxis: {{range: [0, 1]}}}}));
    
    dxyArr.sort((a,b) => a.val - b.val);
    const dxyTrace = {{
        type: 'bar', orientation: 'h',
        x: dxyArr.map(x => x.val), y: dxyArr.map(x => x.name),
        marker: {{color: dxyArr.map(x => x.val < 0 ? "#10B981" : "#EF4444")}}
    }};
    drawPlot("dxy-rank-chart", [dxyTrace], plotLayout({{margin: {{t:30, r:40, b:50, l:120}}, xaxis: {{range: [-1, 1]}}}}));
}}

function renderCommoditySpecific() {{
    const sec = document.getElementById("comspec-section");
    if (!currentCommodity || currentCommodity === "GOLD") {{
        sec.style.display = "none";
        return;
    }}
    sec.style.display = "block";
    
    const d = getData();
    if (!d || !d.commodity_specific) return;
    
    document.getElementById("comspec-title").textContent = d.meta.name;
    const cs = d.commodity_specific;
    const pnl = document.getElementById("comspec-panel");
    
    let contColor = "var(--text2)";
    if (cs.contango_indicator.includes("Backwardation")) contColor = "var(--green)";
    else if (cs.contango_indicator.includes("Contango")) contColor = "var(--red)";
    
    const hl = d.forecast.half_life_days || d.commodity_specific.half_life_days;
    const hlStr = hl ? `${{hl.toFixed(1)}} days to revert 50%` : "N/A";
    
    pnl.innerHTML = `
        <div class="stat-row"><span class="stat-label">Inflation Hedge Score</span><span class="stat-value">${{cs.inflation_hedge_score.toFixed(3)}}</span></div>
        <div class="stat-row"><span class="stat-label">DXY Correlation</span><span class="stat-value">${{cs.dxy_correlation_3m?.toFixed(3) ?? 'N/A'}}</span></div>
        <div class="stat-row"><span class="stat-label">Price vs 1Y Mean</span><span class="stat-value">${{cs.price_vs_1y_mean_pct.toFixed(2)}}% (${{cs.price_vs_1y_mean_zscore.toFixed(2)}} σ)</span></div>
        <div class="stat-row"><span class="stat-label">Term Structure Indicator</span><span class="stat-value" style="color:${{contColor}}">${{cs.contango_indicator}}</span></div>
        <div class="stat-row"><span class="stat-label">Mean Reversion Half-Life</span><span class="stat-value">${{hlStr}}</span></div>
    `;
    
    const z = cs.price_vs_1y_mean_zscore;
    const colors = getThemeColors();
    const zTrace = {{
        type: 'indicator', mode: 'gauge+number', value: z, title: {{text: "Z-Score vs 1Y Mean", font: {{color: colors.text}}}},
        gauge: {{
            axis: {{range: [-3, 3], tickwidth: 1, tickcolor: colors.text2}},
            bar: {{color: z > 0 ? '#10B981' : '#EF4444'}},
            bgcolor: "rgba(255,255,255,0.05)",
            borderwidth: 2, bordercolor: "transparent",
            steps: [
                {{range: [-3, -1.5], color: 'rgba(239, 68, 68, 0.2)'}},
                {{range: [-1.5, 1.5], color: 'rgba(99, 102, 241, 0.1)'}},
                {{range: [1.5, 3], color: 'rgba(16, 185, 129, 0.2)'}}
            ]
        }},
        number: {{font: {{color: colors.text}}}}
    }};
    drawPlot("comspec-chart", [zTrace], plotLayout({{margin: {{t:60, b:30, l:40, r:40}}}}));
}}

function renderAll() {{
    if (!currentCommodity) return;
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
    setCategory(currentCategory); // Initializes currentCommodity and renders
}});
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
