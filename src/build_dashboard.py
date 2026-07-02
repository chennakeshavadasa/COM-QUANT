import json
import os
import sys


def main():
    html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    size_kb = os.path.getsize("index.html") / 1024
    print(f"Built index.html ({size_kb:.1f} KB)")


def generate_html():
    return """<!DOCTYPE html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM-QUANT - Institutional Commodities Terminal</title>
<meta name="description" content="Quantitative commodities analysis dashboard with forecasting models, technical indicators, and risk metrics for 28+ commodity markets.">
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-primary:    #080B14;
  --bg-secondary:  #0D1421;
  --bg-card:       rgba(255,255,255,0.04);
  --bg-card-hover: rgba(255,255,255,0.07);
  --border:        rgba(255,255,255,0.07);
  --border-bright: rgba(255,255,255,0.14);
  --text-primary:  #E8EDF5;
  --text-secondary:#8B95A3;
  --text-muted:    #4A5568;
  --positive: #00D084;
  --negative: #FF4757;
  --signal-buy: #4A9EFF;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 4px 24px rgba(0,0,0,0.45);
  --transition: 180ms ease;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{font-size:16px;scroll-behavior:smooth}}
body{{background:var(--bg-primary);color:var(--text-primary);font-family:'Inter',system-ui,sans-serif;line-height:1.5;min-height:100vh}}
.mono{{font-family:'JetBrains Mono',monospace}}

.app-header{{
  position:fixed;top:0;left:0;right:0;z-index:100;height:64px;
  display:flex;align-items:center;justify-content:space-between;padding:0 24px;
  background:linear-gradient(135deg,#0D1B2A 0%,#080B14 100%);
  border-bottom:1px solid var(--border);backdrop-filter:blur(12px);
}}
.header-logo{{font-size:20px;font-weight:700;letter-spacing:-0.5px;
  background:linear-gradient(135deg,#4A9EFF,#A78BFA);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header-sub{{font-size:12px;color:var(--text-secondary)}}
.header-right{{text-align:right}}
.header-ts{{font-size:11px;color:var(--text-secondary);font-family:'JetBrains Mono',monospace}}
.header-countdown{{font-size:12px;color:var(--signal-buy);font-family:'JetBrains Mono',monospace;margin-top:2px}}

#stale-banner{{
  display:none;width:100%;background:rgba(255,159,67,0.9);color:#000;
  font-weight:600;font-size:13px;text-align:center;padding:8px;
  position:fixed;top:64px;left:0;z-index:95;
}}

.filter-bar{{
  position:sticky;top:64px;z-index:90;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap;
  padding:10px 24px;background:rgba(8,11,20,0.92);
  border-bottom:1px solid var(--border);backdrop-filter:blur(8px);
}}
.filter-btn{{
  padding:5px 14px;border-radius:20px;font-size:12px;font-weight:500;
  border:1px solid var(--border);background:transparent;
  color:var(--text-secondary);cursor:pointer;transition:var(--transition);
}}
.filter-btn:hover,.filter-btn.active{{
  border-color:var(--signal-buy);color:var(--signal-buy);
  background:rgba(74,158,255,0.10);
}}
.search-box{{
  margin-left:auto;padding:5px 12px;border-radius:var(--radius-sm);
  border:1px solid var(--border);background:var(--bg-secondary);
  color:var(--text-primary);font-size:13px;outline:none;width:180px;
}}
.sort-select{{
  padding:5px 10px;border-radius:var(--radius-sm);
  border:1px solid var(--border);background:var(--bg-secondary);
  color:var(--text-secondary);font-size:12px;cursor:pointer;
}}

#loading-screen{{
  position:fixed;inset:0;z-index:500;background:var(--bg-primary);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;
}}
.spinner{{
  width:48px;height:48px;border:3px solid rgba(74,158,255,0.2);
  border-top-color:#4A9EFF;border-radius:50%;animation:spin 0.8s linear infinite;
}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
.loading-text{{font-size:14px;color:var(--text-secondary)}}

.dashboard-grid{{
  display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
  gap:16px;padding:20px 24px 40px;margin-top:100px;
}}
@media(max-width:375px){{.dashboard-grid{{grid-template-columns:1fr}}}}

.commodity-card{{
  background:var(--bg-card);border:1px solid var(--border);
  border-radius:var(--radius);padding:18px 18px 14px;cursor:pointer;
  transition:transform var(--transition),box-shadow var(--transition),border-color var(--transition);
  position:relative;overflow:hidden;
}}
.commodity-card::before{{
  content:'';position:absolute;top:0;left:0;bottom:0;width:3px;
  background:var(--sector-color,#4A9EFF);border-radius:3px 0 0 3px;
}}
.commodity-card:hover{{
  transform:translateY(-2px);box-shadow:var(--shadow);
  border-color:var(--border-bright);background:var(--bg-card-hover);
}}

.signal-badge{{
  display:inline-flex;align-items:center;gap:5px;
  padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:0.3px;
}}
.signal-strong-buy{{background:rgba(0,208,132,0.15);color:#00D084;border:1px solid rgba(0,208,132,0.3)}}
.signal-buy{{background:rgba(74,158,255,0.15);color:#4A9EFF;border:1px solid rgba(74,158,255,0.3)}}
.signal-neutral{{background:rgba(139,149,163,0.15);color:#8B95A3;border:1px solid rgba(139,149,163,0.3)}}
.signal-sell{{background:rgba(255,159,67,0.15);color:#FF9F43;border:1px solid rgba(255,159,67,0.3)}}
.signal-strong-sell{{background:rgba(255,71,87,0.15);color:#FF4757;border:1px solid rgba(255,71,87,0.3)}}

.metrics-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;margin-top:12px}}
.metric-item{{display:flex;flex-direction:column;gap:3px}}
.metric-label{{font-size:10px;text-transform:uppercase;letter-spacing:0.6px;color:var(--text-muted)}}
.metric-val{{font-size:13px;color:var(--text-primary)}}
.metric-val.negative{{color:var(--negative)}}
.metric-sub{{font-size:10px;color:var(--text-secondary)}}

.modal-overlay{{
  display:none;position:fixed;inset:0;z-index:200;
  background:rgba(8,11,20,0.97);backdrop-filter:blur(6px);
  overflow-y:auto;padding:24px;
}}
.modal-overlay.open{{display:block}}
.modal-inner{{
  max-width:1200px;margin:0 auto;background:var(--bg-secondary);
  border:1px solid var(--border-bright);border-radius:var(--radius);padding:28px;
}}
.modal-close{{
  float:right;font-size:22px;cursor:pointer;
  color:var(--text-secondary);background:none;border:none;line-height:1;
}}
.modal-chart{{width:100%;height:350px;margin-bottom:24px}}

.app-footer{{
  text-align:center;padding:20px;font-size:11px;
  color:var(--text-muted);border-top:1px solid var(--border);margin-top:40px;
}}
</style>
</head>
<body>

<div id="loading-screen">
  <div class="spinner"></div>
  <div class="loading-text">Loading market data...</div>
</div>

<header class="app-header">
  <div style="display:flex;align-items:center;gap:12px">
    <div class="header-logo">📊 COM-QUANT</div>
    <div class="header-sub">Commodities Quantitative Analysis</div>
  </div>
  <div class="header-right">
    <div class="header-ts" id="header-ts">Last: {generated_at}</div>
    <div class="header-countdown" id="countdown"></div>
  </div>
</header>
<div id="stale-banner"></div>

<div class="filter-bar">
  <button class="filter-btn active" data-sector="all">ALL</button>
  <button class="filter-btn" data-sector="precious_metals">PRECIOUS METALS</button>
  <button class="filter-btn" data-sector="energy">ENERGY</button>
  <button class="filter-btn" data-sector="agriculture">AGRICULTURE</button>
  <button class="filter-btn" data-sector="industrial_metals">INDUSTRIAL METALS</button>
  <button class="filter-btn" data-sector="livestock">LIVESTOCK</button>
  <input type="text" class="search-box" id="search-box" placeholder="🔍 search...">
  <span style="font-size:12px;color:var(--text-secondary);margin-left:12px">Sort:</span>
  <select class="sort-select" id="sort-select">
    <option value="score">Composite Score</option>
    <option value="ensemble-pct">Ensemble Forecast %</option>
    <option value="rsi">RSI</option>
    <option value="sharpe">Sharpe Ratio</option>
    <option value="vol" selected>Volatility ↓</option>
  </select>
</div>

<div class="dashboard-grid" id="dashboard-grid"></div>

<div class="modal-overlay" id="detail-modal">
  <div class="modal-inner">
    <button class="modal-close" onclick="closeModal()">&times;</button>
    <div class="modal-chart" id="chart1"></div>
    <div class="modal-chart" id="chart2"></div>
    <div class="modal-chart" id="chart3"></div>
    <div class="modal-chart" id="chart4"></div>
  </div>
</div>

<footer class="app-footer">
  COM-QUANT &middot; Automated commodities analysis &middot; Data via Yahoo Finance &middot;
  For educational purposes only &middot; Not financial advice
</footer>

<script>
const SECTOR_COLORS = {{
  precious_metals:  '#F5A623',
  energy:           '#FF6B35',
  agriculture:      '#4CAF50',
  industrial_metals:'#4A9EFF',
  livestock:        '#A78BFA'
}};

const PLOTLY_DARK = {{
  paper_bgcolor:'#0D1421', plot_bgcolor:'#0D1421',
  font:{{family:'Inter,sans-serif',color:'#8B95A3',size:12}},
  title_font:{{family:'Inter,sans-serif',color:'#E8EDF5',size:14}},
  xaxis:{{gridcolor:'rgba(255,255,255,0.05)',tickfont:{{family:'JetBrains Mono,monospace',color:'#8B95A3',size:10}}}},
  yaxis:{{gridcolor:'rgba(255,255,255,0.05)',tickfont:{{family:'JetBrains Mono,monospace',color:'#8B95A3',size:10}}}},
  legend:{{bgcolor:'rgba(255,255,255,0.05)',bordercolor:'rgba(255,255,255,0.10)',borderwidth:1,font:{{size:11}}}},
  margin:{{l:55,r:20,t:45,b:40}},
  hovermode:'x unified'
}};

let ALLDATA = null;
let CHARTS_CACHE = {{}};

function applyDark(layout) {{ return Object.assign({{}}, PLOTLY_DARK, layout); }}

function sparklineSVG(prices, color, width=280, height=70) {{
  prices = prices.filter(p => p != null);
  if (prices.length < 2) return '';
  const mn = Math.min(...prices), mx = Math.max(...prices);
  const rng = mx - mn || 1;
  const xs = prices.map((_, i) => i / (prices.length - 1) * width);
  const ys = prices.map(p => height - (p - mn) / rng * height);
  const pts = xs.map((x, i) => `${{x.toFixed(1)}},${{ys[i].toFixed(1)}}`).join(' ');
  const fill = `0,${{height}} ${{pts}} ${{width}},${{height}}`;
  const id = 'sg_' + color.replace('#','');
  return `<svg viewBox="0 0 ${{width}} ${{height}}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:${{height}}px;display:block">
    <defs><linearGradient id="${{id}}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${{color}}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="${{color}}" stop-opacity="0.0"/>
    </linearGradient></defs>
    <polygon points="${{fill}}" fill="url(#${{id}})"/>
    <polyline points="${{pts}}" fill="none" stroke="${{color}}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>
  </svg>`;
}}

function rsiBar(val) {{
  const pct = Math.min(Math.max(val || 50, 0), 100);
  const color = pct < 30 ? 'var(--positive)' : pct > 70 ? 'var(--negative)' : 'var(--text-secondary)';
  return `<div style="display:flex;align-items:center;gap:8px">
    <span class="mono" style="font-size:12px;color:${{color}}">${{pct.toFixed(1)}}</span>
    <div style="flex:1;height:4px;background:rgba(255,255,255,0.1);border-radius:2px">
      <div style="width:${{pct}}%;height:100%;background:${{color}};border-radius:2px;transition:width 0.6s ease"></div>
    </div>
  </div>`;
}}

function scoreToSignal(score) {{
  if (score >= 70) return ['strong-buy',  '🟢 STRONG BUY'];
  if (score >= 55) return ['buy',         '🔵 BUY'];
  if (score >= 40) return ['neutral',     '⚪ NEUTRAL'];
  if (score >= 25) return ['sell',        '🟠 SELL'];
  return              ['strong-sell', '🔴 STRONG SELL'];
}}

function renderCard(cid, data) {{
  const meta = data.meta;
  const color = SECTOR_COLORS[meta.category] || '#FFFFFF';
  const score = data.indicators.composite_score;
  const [sigCls, sigText] = scoreToSignal(score);
  const cp = meta.current_price;
  const chg = meta.price_change_1d_pct;
  const chgVal = cp * (chg / 100);
  const chgColor = chg >= 0 ? 'var(--positive)' : 'var(--negative)';
  const chgArrow = chg > 0 ? '▲' : chg < 0 ? '▼' : '—';
  const prices = data.history.close.slice(-30);
  const svg = sparklineSVG(prices, color);
  const ens = (data.forecast.ensemble || []).filter(x => x != null);
  const fcVal = ens.length ? ens[ens.length-1] : cp;
  const fcPct = (fcVal - cp) / cp * 100;
  const fcArr = fcPct > 0 ? '↗' : fcPct < 0 ? '↘' : '→';
  const rsi = data.indicators.rsi14;
  const hurst = data.statistics.hurst;
  const hurstLabel = hurst < 0.45 ? 'Mean-Rev.' : hurst <= 0.55 ? 'Random' : 'Trending';
  const var95 = data.risk.var_95_pct;
  const vol = data.statistics.annualized_vol_20d || data.statistics.annualized_vol_30d || 0;
  const maxdd = data.risk.max_drawdown_pct;
  const sharpe = data.risk.sharpe_ratio || 0;
  const fcPctStr = (fcPct >= 0 ? '+' : '') + fcPct.toFixed(2) + '%';
  const fcColor = fcPct >= 0 ? 'var(--positive)' : 'var(--negative)';

  return `<div class="commodity-card" style="--sector-color:${{color}}"
    data-sector="${{meta.category}}" data-name="${{meta.name}}" data-ticker="${{meta.ticker}}"
    data-score="${{score}}" data-rsi="${{rsi}}" data-vol="${{vol}}" data-sharpe="${{sharpe}}"
    data-ensemble-pct="${{fcPct}}" onclick="openModal('${{cid}}')">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <div style="font-weight:700;font-size:16px">${{meta.name}} &middot; <span style="font-size:12px;color:var(--text-secondary)">${{meta.ticker}}</span></div>
        <div style="font-size:12px;color:var(--text-muted);text-transform:capitalize;margin-top:2px">${{meta.category.replace(/_/g,' ')}}</div>
      </div>
      <div class="signal-badge signal-${{sigCls}}">${{sigText}}</div>
    </div>
    <div style="height:1px;background:var(--border);margin:12px 0"></div>
    <div style="display:flex;align-items:baseline;gap:12px">
      <div class="mono" style="font-size:20px;font-weight:600">$${{cp.toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}})}}</div>
      <div class="mono" style="font-size:13px;color:${{chgColor}}">${{chgArrow}} $${{Math.abs(chgVal).toFixed(2)}} &nbsp; ${{chg >= 0 ? '+' : ''}}${{chg.toFixed(2)}}%</div>
    </div>
    <div style="height:1px;background:var(--border);margin:12px 0"></div>
    <div>${{svg}}</div>
    <div style="height:1px;background:var(--border);margin:12px 0"></div>
    <div style="font-size:12px;color:var(--text-secondary)">
      Ensemble 30d forecast: <span class="mono" style="color:var(--text-primary)">$${{fcVal.toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}})}}</span>
      (<span class="mono" style="color:${{fcColor}}">${{fcPctStr}}</span>) ${{fcArr}}
    </div>
    <div style="height:1px;background:var(--border);margin:12px 0"></div>
    <div class="metrics-grid">
      <div class="metric-item"><span class="metric-label">RSI</span>${{rsiBar(rsi)}}</div>
      <div class="metric-item"><span class="metric-label">Hurst</span><span class="metric-val mono">${{hurst.toFixed(2)}} <span class="metric-sub">${{hurstLabel}}</span></span></div>
      <div class="metric-item"><span class="metric-label">VaR 95%</span><span class="metric-val mono negative">-${{Math.abs(var95).toFixed(2)}}%</span></div>
      <div class="metric-item"><span class="metric-label">Ann. Vol</span><span class="metric-val mono">${{(vol||0).toFixed(1)}}%</span></div>
      <div class="metric-item"><span class="metric-label">Max DD</span><span class="metric-val mono negative">-${{Math.abs(maxdd).toFixed(1)}}%</span></div>
      <div class="metric-item"><span class="metric-label">Sharpe</span><span class="metric-val mono">${{sharpe.toFixed(2)}}</span></div>
    </div>
    <div style="height:1px;background:var(--border);margin:12px 0"></div>
    <div style="font-size:12px;font-weight:500;color:var(--signal-buy);text-align:right">View Full Analysis &rarr;</div>
  </div>`;
}}

function buildCharts(cid, winData) {{
  if (CHARTS_CACHE[cid]) return CHARTS_CACHE[cid];
  const keys = Object.keys(winData);
  let w = keys[0];
  if (winData['1M']) w = '1M';
  const d = winData[w];
  const hDates = d.history.dates, hClose = d.history.close;
  const fDates = d.forecast.dates;
  const traces1 = [];
  traces1.push({{x:hDates,y:hClose,name:'Price',mode:'lines',line:{{color:'#FFFFFF',width:2}}}});
  if (d.forecast.arima_ci_lower?.[0] != null) {{
    traces1.push({{x:fDates,y:d.forecast.arima_ci_lower,fill:'none',line:{{width:0}},showlegend:false,hoverinfo:'skip'}});
    traces1.push({{x:fDates,y:d.forecast.arima_ci_upper,fill:'tonexty',fillcolor:'rgba(74,158,255,0.1)',line:{{width:0}},name:'ARIMA 95% CI',hoverinfo:'skip'}});
  }}
  if (d.forecast.arima?.[0] != null)
    traces1.push({{x:fDates,y:d.forecast.arima,name:'ARIMA',mode:'lines',line:{{color:'#4A9EFF',dash:'dash'}}}});
  if (d.forecast.holt_winters?.[0] != null)
    traces1.push({{x:fDates,y:d.forecast.holt_winters,name:'Holt-Winters',mode:'lines',line:{{color:'#A78BFA',dash:'dash'}}}});
  if (d.forecast.monte_carlo_p5?.[0] != null) {{
    traces1.push({{x:fDates,y:d.forecast.monte_carlo_p5,fill:'none',line:{{width:0}},showlegend:false,hoverinfo:'skip'}});
    traces1.push({{x:fDates,y:d.forecast.monte_carlo_p95,fill:'tonexty',fillcolor:'rgba(255,107,53,0.08)',line:{{width:0}},name:'MC P5-P95',hoverinfo:'skip'}});
  }}
  if (d.forecast.monte_carlo_p50?.[0] != null)
    traces1.push({{x:fDates,y:d.forecast.monte_carlo_p50,name:'MC Median',mode:'lines',line:{{color:'#FF6B35',dash:'dash'}}}});
  if (d.forecast.ou_process?.[0] != null)
    traces1.push({{x:fDates,y:d.forecast.ou_process,name:'OU Process',mode:'lines',line:{{color:'#F5A623',dash:'dash'}}}});
  if (d.forecast.ensemble?.[0] != null)
    traces1.push({{x:fDates,y:d.forecast.ensemble,name:'Ensemble',mode:'lines',line:{{color:'#FFFFFF',width:2.5}}}});
  const layout1 = {{
    title:`Price & Ensemble Forecast — ${{d.meta.name}}`,
    shapes:[{{type:'line',x0:hDates[hDates.length-1],x1:hDates[hDates.length-1],y0:0,y1:1,yref:'paper',line:{{color:'rgba(255,255,255,0.2)',dash:'dash'}}}}]
  }};
  const rsiVal = d.indicators.rsi14;
  const traces2 = [{{x:hDates,y:Array(hDates.length).fill(rsiVal),name:'RSI',mode:'lines',line:{{color:'#4A9EFF'}}}}];
  const layout2 = {{title:'Momentum (RSI)',yaxis:{{range:[0,100]}}}};
  const traces3 = [];
  if (d.forecast.monte_carlo_p50?.[0] != null) {{
    traces3.push({{x:fDates,y:d.forecast.monte_carlo_p5,fill:'none',line:{{width:0}},showlegend:false}});
    traces3.push({{x:fDates,y:d.forecast.monte_carlo_p95,fill:'tonexty',fillcolor:'rgba(255,107,53,0.2)',line:{{width:0}},name:'MC P5-P95'}});
    traces3.push({{x:fDates,y:d.forecast.monte_carlo_p50,name:'MC P50',mode:'lines',line:{{color:'#FF6B35',width:2}}}});
  }}
  const layout3 = {{title:`Monte Carlo Simulation — ${{w}} Horizon`}};
  const traces4 = [];
  const dow = d.seasonality?.day_of_week || {{}};
  if (Object.keys(dow).length) {{
    const days = ['Monday','Tuesday','Wednesday','Thursday','Friday'];
    const vals = days.map(dy => dow[dy] || 0);
    traces4.push({{x:days,y:vals,type:'bar',marker:{{color:vals.map(v => v>=0?'#00D084':'#FF4757')}}}});
  }}
  const layout4 = {{title:'Day-of-Week Seasonality'}};
  CHARTS_CACHE[cid] = {{traces1,layout1,traces2,layout2,traces3,layout3,traces4,layout4}};
  return CHARTS_CACHE[cid];
}}

function openModal(cid) {{
  const c = buildCharts(cid, ALLDATA.data[cid]);
  Plotly.newPlot('chart1',c.traces1,applyDark(c.layout1),{{responsive:true,displayModeBar:false}});
  Plotly.newPlot('chart2',c.traces2,applyDark(c.layout2),{{responsive:true,displayModeBar:false}});
  Plotly.newPlot('chart3',c.traces3,applyDark(c.layout3),{{responsive:true,displayModeBar:false}});
  Plotly.newPlot('chart4',c.traces4,applyDark(c.layout4),{{responsive:true,displayModeBar:false}});
  document.getElementById('detail-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}}
function closeModal() {{
  document.getElementById('detail-modal').classList.remove('open');
  document.body.style.overflow = '';
}}
document.addEventListener('keydown', e => e.key === 'Escape' && closeModal());

function initDashboard(jsdata) {{
  ALLDATA = jsdata;
  const grid = document.getElementById('dashboard-grid');
  const genAt = jsdata._meta.generated_at;
  document.getElementById('header-ts').textContent = 'Last: ' + genAt;

  // Countdown timer
  const genDate = new Date(genAt.replace(' UTC','') + 'Z');
  function tick() {{
    const diff = genDate.getTime() + 6*3600000 - Date.now();
    if (diff <= 0) {{ document.getElementById('countdown').textContent = 'Update overdue — refresh'; return; }}
    const hh = Math.floor(diff/3600000);
    const mm = Math.floor((diff%3600000)/60000);
    const ss = Math.floor((diff%60000)/1000);
    document.getElementById('countdown').textContent = `Next update in ${{hh}}h ${{mm.toString().padStart(2,'0')}}m ${{ss.toString().padStart(2,'0')}}s`;
  }}
  tick(); setInterval(tick, 1000);

  // Stale banner
  if ((Date.now() - genDate) / 3600000 > 25) {{
    const b = document.getElementById('stale-banner');
    b.textContent = `⚠  Data may be stale — last updated ${{Math.floor((Date.now()-genDate)/3600000)}} hours ago`;
    b.style.display = 'block';
  }}

  // Render cards
  let html = '';
  for (const cid in jsdata.data) {{
    if (!jsdata.data[cid]) continue;
    const keys = Object.keys(jsdata.data[cid]);
    if (!keys.length) continue;
    let w = keys[0];
    if (jsdata.data[cid]['1M']) w = '1M';
    html += renderCard(cid, jsdata.data[cid][w]);
  }}
  grid.innerHTML = html;

  // Hide loader
  document.getElementById('loading-screen').style.display = 'none';

  // Filter buttons
  document.querySelectorAll('.filter-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const sector = btn.dataset.sector;
      document.querySelectorAll('.commodity-card').forEach(card => {{
        card.style.display = (sector === 'all' || card.dataset.sector === sector) ? '' : 'none';
      }});
    }});
  }});

  // Search
  document.getElementById('search-box').addEventListener('input', function() {{
    const q = this.value.toLowerCase();
    document.querySelectorAll('.commodity-card').forEach(card => {{
      card.style.display = (card.dataset.name.toLowerCase().includes(q) || card.dataset.ticker.toLowerCase().includes(q)) ? '' : 'none';
    }});
  }});

  // Sort
  document.getElementById('sort-select').addEventListener('change', function() {{
    const g = document.querySelector('.dashboard-grid');
    [...g.querySelectorAll('.commodity-card')]
      .sort((a,b) => +b.dataset[this.value] - +a.dataset[this.value])
      .forEach(c => g.appendChild(c));
  }});
}}

// Fetch data at runtime from main branch — keeps gh-pages deployment tiny
fetch('https://raw.githubusercontent.com/chennakeshavadasa/COM-QUANT/main/multi_data.json')
  .then(r => r.json())
  .then(initDashboard)
  .catch(err => {{
    document.getElementById('loading-screen').innerHTML =
      '<div style="color:#FF4757;font-size:14px">⚠ Failed to load market data: ' + err.message + '</div>';
  }});
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
