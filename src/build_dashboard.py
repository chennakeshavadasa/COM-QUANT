import json
import sys
import datetime

def sparkline_svg(prices, sector_color, width=280, height=70):
    prices = [p for p in prices if p is not None]
    if len(prices) < 2:
        return "<svg></svg>"
    mn, mx = min(prices), max(prices)
    rng = mx - mn or 1
    xs = [i / (len(prices) - 1) * width for i in range(len(prices))]
    ys = [height - (p - mn) / rng * height for p in prices]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
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

def score_to_signal(score):
    if   score >= 70: return "strong-buy",  "STRONG BUY",  "🟢"
    elif score >= 55: return "buy",         "BUY",         "🔵"
    elif score >= 40: return "neutral",     "NEUTRAL",     "⚪"
    elif score >= 25: return "sell",        "SELL",        "🟠"
    else:             return "strong-sell", "STRONG SELL", "🔴"

def render_card(key, data):
    meta = data["meta"]
    sector_colors = {
        "precious_metals": "#F5A623",
        "energy": "#FF6B35",
        "agriculture": "#4CAF50",
        "industrial_metals": "#4A9EFF",
        "livestock": "#A78BFA"
    }
    sector_cat = meta["category"]
    sector_color = sector_colors.get(sector_cat, "#FFFFFF")
    
    score = data["indicators"]["composite_score"]
    sig_cls, sig_text, sig_emoji = score_to_signal(score)
    
    cp = meta["current_price"]
    chg = meta["price_change_1d_pct"]
    chg_val = cp * (chg / 100)
    chg_color = "var(--positive)" if chg >= 0 else "var(--negative)"
    chg_arrow = "▲" if chg >= 0 else "▼" if chg < 0 else "—"
    
    if chg == 0:
        chg_color = "var(--text-secondary)"
    
    prices = data["history"]["close"][-30:] if len(data["history"]["close"]) >= 30 else data["history"]["close"]
    svg = sparkline_svg(prices, sector_color)
    
    ens_fc = data["forecast"]["ensemble"]
    valid_ens = [x for x in ens_fc if x is not None]
    if valid_ens:
        fc_val = valid_ens[-1]
        fc_pct = (fc_val - cp) / cp * 100
        fc_arr = "↗" if fc_pct > 0 else "↘" if fc_pct < 0 else "→"
    else:
        fc_val = cp
        fc_pct = 0
        fc_arr = "→"
        
    rsi = data["indicators"]["rsi14"]
    hurst = data["statistics"]["hurst"]
    if hurst < 0.45: hurst_label = "Mean-Rev."
    elif hurst <= 0.55: hurst_label = "Random"
    else: hurst_label = "Trending"
    
    var95 = data["risk"]["var_95_pct"]
    vol = data["statistics"].get("annualized_vol_20d", data["statistics"].get("annualized_vol_30d", 0))
    if vol is None: vol = 0
    maxdd = data["risk"]["max_drawdown_pct"]
    sharpe = data["risk"]["sharpe_ratio"]
    if sharpe is None: sharpe = 0
    
    return f"""
<div class="commodity-card" style="--sector-color: {sector_color}" 
     data-sector="{sector_cat}" 
     data-name="{meta['name']}" 
     data-ticker="{meta['ticker']}" 
     data-score="{score}" 
     data-rsi="{rsi}" 
     data-vol="{vol}" 
     data-sharpe="{sharpe}" 
     data-ensemble-pct="{fc_pct}"
     onclick="openModal('{key}')">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <div style="font-weight:700; font-size:16px;">{meta['name']} &middot; <span style="font-size:12px; color:var(--text-secondary)">{meta['ticker']}</span></div>
      <div style="font-size:12px; color:var(--text-muted); text-transform:capitalize; margin-top:2px;">{sector_cat.replace('_', ' ')}</div>
    </div>
    <div class="signal-badge signal-{sig_cls}">{sig_emoji} {sig_text}</div>
  </div>
  
  <div style="height:1px; background:var(--border); margin:12px 0;"></div>
  
  <div style="display:flex; align-items:baseline; gap:12px;">
    <div class="mono" style="font-size:20px; font-weight:600;">${cp:,.2f}</div>
    <div class="mono" style="font-size:13px; color:{chg_color}">{chg_arrow} ${abs(chg_val):,.2f} &nbsp; {chg:+.2f}%</div>
  </div>
  
  <div style="height:1px; background:var(--border); margin:12px 0;"></div>
  
  <div>{svg}</div>
  
  <div style="height:1px; background:var(--border); margin:12px 0;"></div>
  
  <div style="font-size:12px; color:var(--text-secondary);">
    Ensemble 30d forecast: <span class="mono" style="color:var(--text-primary)">${fc_val:,.2f}</span> (<span class="mono" style="color:{'var(--positive)' if fc_pct>=0 else 'var(--negative)'}">{fc_pct:+.2f}%</span>) {fc_arr}
  </div>
  
  <div style="height:1px; background:var(--border); margin:12px 0;"></div>
  
  <div class="metrics-grid">
    <div class="metric-item">
      <span class="metric-label">RSI</span>
      {rsi_bar_html(rsi)}
    </div>
    <div class="metric-item">
      <span class="metric-label">Hurst</span>
      <span class="metric-val mono">{hurst:.2f} <span class="metric-sub">{hurst_label}</span></span>
    </div>
    <div class="metric-item">
      <span class="metric-label">VaR 95%</span>
      <span class="metric-val mono negative">{-abs(var95):.2f}%</span>
    </div>
    <div class="metric-item">
      <span class="metric-label">Ann. Vol</span>
      <span class="metric-val mono">{vol:.1f}%</span>
    </div>
    <div class="metric-item">
      <span class="metric-label">Max DD</span>
      <span class="metric-val mono negative">{-abs(maxdd):.1f}%</span>
    </div>
    <div class="metric-item">
      <span class="metric-label">Sharpe</span>
      <span class="metric-val mono">{sharpe:.2f}</span>
    </div>
  </div>
  
  <div style="height:1px; background:var(--border); margin:12px 0;"></div>
  
  <div style="font-size:12px; font-weight:500; color:var(--signal-buy); text-align:right;">View Full Analysis &rarr;</div>
</div>
"""

def generate_charts_js(data_dict):
    charts = {}
    
    for cid, win_data in data_dict.items():
        if not win_data: continue
        # Use first window found, e.g., '1M' or '1W'
        w = list(win_data.keys())[0]
        if '1M' in win_data: w = '1M'
        
        d = win_data[w]
        
        h_dates = d["history"]["dates"]
        h_close = d["history"]["close"]
        f_dates = d["forecast"]["dates"]
        
        # Chart 1: Price + Forecasts
        traces1 = []
        traces1.append({"x": h_dates, "y": h_close, "name": "Price", "mode": "lines", "line": {"color": "#FFFFFF", "width": 2}})
        
        # arima
        if d["forecast"]["arima"] and d["forecast"]["arima"][0] is not None:
            # CI bands
            if d["forecast"]["arima_ci_lower"] and d["forecast"]["arima_ci_lower"][0] is not None:
                traces1.append({"x": f_dates, "y": d["forecast"]["arima_ci_lower"], "fill": "none", "line": {"width": 0}, "showlegend": False, "hoverinfo": "skip"})
                traces1.append({"x": f_dates, "y": d["forecast"]["arima_ci_upper"], "fill": "tonexty", "fillcolor": "rgba(74, 158, 255, 0.1)", "line": {"width": 0}, "name": "ARIMA 95% CI", "hoverinfo": "skip"})
            traces1.append({"x": f_dates, "y": d["forecast"]["arima"], "name": "ARIMA", "mode": "lines", "line": {"color": "#4A9EFF", "dash": "dash"}})
            
        # hw
        if d["forecast"]["holt_winters"] and d["forecast"]["holt_winters"][0] is not None:
            traces1.append({"x": f_dates, "y": d["forecast"]["holt_winters"], "name": "Holt-Winters", "mode": "lines", "line": {"color": "#A78BFA", "dash": "dash"}})
            
        # MC
        if d["forecast"]["monte_carlo_p50"] and d["forecast"]["monte_carlo_p50"][0] is not None:
            if d["forecast"]["monte_carlo_p5"] and d["forecast"]["monte_carlo_p5"][0] is not None:
                traces1.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p5"], "fill": "none", "line": {"width": 0}, "showlegend": False, "hoverinfo": "skip"})
                traces1.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p95"], "fill": "tonexty", "fillcolor": "rgba(255, 107, 53, 0.08)", "line": {"width": 0}, "name": "MC P5-P95", "hoverinfo": "skip"})
            traces1.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p50"], "name": "MC Median", "mode": "lines", "line": {"color": "#FF6B35", "dash": "dash"}})
            
        # OU
        if d["forecast"]["ou_process"] and d["forecast"]["ou_process"][0] is not None:
            traces1.append({"x": f_dates, "y": d["forecast"]["ou_process"], "name": "OU Process", "mode": "lines", "line": {"color": "#F5A623", "dash": "dash"}})
            
        # Ensemble
        if d["forecast"]["ensemble"] and d["forecast"]["ensemble"][0] is not None:
            traces1.append({"x": f_dates, "y": d["forecast"]["ensemble"], "name": "Ensemble", "mode": "lines", "line": {"color": "#FFFFFF", "width": 2.5}})
            
        layout1 = {
            "title": f"Price & Ensemble Forecast — {d['meta']['name']}",
            "shapes": [{"type": "line", "x0": h_dates[-1], "x1": h_dates[-1], "y0": 0, "y1": 1, "yref": "paper", "line": {"color": "rgba(255,255,255,0.2)", "dash": "dash"}}]
        }
        
        # Chart 2: Momentum
        # Simplified: Just RSI
        rsi_val = d["indicators"]["rsi14"]
        traces2 = [
            {"x": h_dates, "y": [rsi_val]*len(h_dates), "name": "RSI", "mode": "lines", "line": {"color": "#4A9EFF"}}
        ]
        layout2 = {"title": "Momentum Indicators (RSI)", "yaxis": {"range": [0, 100]}}
        
        # Chart 3: MC Fan (stubbed using p5, 25, 50, 75, 95)
        traces3 = []
        if d["forecast"]["monte_carlo_p50"] and d["forecast"]["monte_carlo_p50"][0] is not None:
            traces3.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p5"], "fill": "none", "line": {"width": 0}, "showlegend": False})
            traces3.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p95"], "fill": "tonexty", "fillcolor": "rgba(255, 107, 53, 0.2)", "line": {"width": 0}, "name": "MC P5-P95"})
            traces3.append({"x": f_dates, "y": d["forecast"]["monte_carlo_p50"], "name": "MC P50", "mode": "lines", "line": {"color": "#FF6B35", "width": 2}})
        layout3 = {"title": f"Monte Carlo Simulation — {w} Horizon"}
        
        # Chart 4: Seasonality
        traces4 = []
        if d["seasonality"]["day_of_week"]:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            vals = [d["seasonality"]["day_of_week"].get(day, 0) for day in days]
            colors = ["#00D084" if v >= 0 else "#FF4757" for v in vals]
            traces4.append({"x": days, "y": vals, "type": "bar", "marker": {"color": colors}})
        layout4 = {"title": "Day-of-Week Seasonality (Historical)"}

        charts[cid] = {
            "traces1": traces1, "layout1": layout1,
            "traces2": traces2, "layout2": layout2,
            "traces3": traces3, "layout3": layout3,
            "traces4": traces4, "layout4": layout4
        }
    return json.dumps(charts)

def main():
    if not os.path.exists("multi_data.json"):
        sys.exit(1)
        
    with open("multi_data.json", "r", encoding="utf-8") as f:
        jsdata = json.load(f)
        
    generated_at = jsdata["_meta"]["generated_at"]
    generated_at_utc = jsdata["_meta"]["generated_at"].replace(" UTC", "")
    
    cards_html = []
    for cid in jsdata["data"]:
        # Find available window
        if not jsdata["data"][cid]: continue
        w = list(jsdata["data"][cid].keys())[0]
        if '1M' in jsdata["data"][cid]: w = '1M'
        cards_html.append(render_card(cid, jsdata["data"][cid][w]))
        
    charts_js = generate_charts_js(jsdata["data"])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>COM-QUANT - Institutional Commodities Terminal</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-primary:    #080B14;
  --bg-secondary:  #0D1421;
  --bg-card:       rgba(255, 255, 255, 0.04);
  --bg-card-hover: rgba(255, 255, 255, 0.07);
  --border:        rgba(255, 255, 255, 0.07);
  --border-bright: rgba(255, 255, 255, 0.14);
  --text-primary:  #E8EDF5;
  --text-secondary:#8B95A3;
  --text-muted:    #4A5568;
  --sector-metals: #F5A623;
  --sector-energy: #FF6B35;
  --sector-agri:   #4CAF50;
  --signal-strong-buy:  #00D084;
  --signal-buy:         #4A9EFF;
  --signal-neutral:     #8B95A3;
  --signal-sell:        #FF9F43;
  --signal-strong-sell: #FF4757;
  --chart-arima:    #4A9EFF;
  --chart-hw:       #A78BFA;
  --chart-mc:       #FF6B35;
  --chart-ou:       #F5A623;
  --chart-ensemble: #FFFFFF;
  --positive: #00D084;
  --negative: #FF4757;
  --radius:   12px;
  --radius-sm: 8px;
  --shadow:   0 4px 24px rgba(0, 0, 0, 0.45);
  --transition: 180ms ease;
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 16px; scroll-behavior: smooth; }}
body {{
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.5;
  min-height: 100vh;
}}
.mono {{ font-family: 'JetBrains Mono', monospace; }}

.app-header {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 64px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(135deg, #0D1B2A 0%, #080B14 100%);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(12px);
}}
.header-left   {{ display: flex; align-items: center; gap: 12px; }}
.header-logo   {{ font-size: 20px; font-weight: 700; letter-spacing: -0.5px;
                 background: linear-gradient(135deg, #4A9EFF, #A78BFA);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.header-sub    {{ font-size: 12px; color: var(--text-secondary); }}
.header-right  {{ text-align: right; }}
.header-ts     {{ font-size: 11px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }}
.header-countdown {{ font-size: 12px; color: var(--signal-buy); font-family: 'JetBrains Mono', monospace; margin-top: 2px; }}

#stale-banner {{
  display: none; width: 100%; background: rgba(255, 159, 67, 0.9); color: #000;
  font-weight: 600; font-size: 13px; text-align: center; padding: 8px;
  position: fixed; top: 64px; left: 0; z-index: 95;
}}

.filter-bar {{
  position: sticky; top: 64px; z-index: 90;
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  padding: 10px 24px;
  background: rgba(8, 11, 20, 0.92);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(8px);
}}
.filter-btn {{
  padding: 5px 14px; border-radius: 20px; font-size: 12px; font-weight: 500;
  border: 1px solid var(--border); background: transparent;
  color: var(--text-secondary); cursor: pointer; transition: var(--transition);
}}
.filter-btn:hover, .filter-btn.active {{
  border-color: var(--signal-buy); color: var(--signal-buy);
  background: rgba(74, 158, 255, 0.10);
}}
.search-box {{
  margin-left: auto; padding: 5px 12px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--bg-secondary);
  color: var(--text-primary); font-size: 13px; outline: none; width: 180px;
}}
.sort-select {{
  padding: 5px 10px; border-radius: var(--radius-sm);
  border: 1px solid var(--border); background: var(--bg-secondary);
  color: var(--text-secondary); font-size: 12px; cursor: pointer;
}}

.dashboard-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  padding: 20px 24px 40px;
  margin-top: 100px;
}}

@media (max-width: 375px) {{
  .dashboard-grid {{ grid-template-columns: 1fr; }}
}}

.commodity-card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 18px 14px;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition), border-color var(--transition);
  position: relative;
  overflow: hidden;
}}
.commodity-card::before {{
  content: '';
  position: absolute; top: 0; left: 0; bottom: 0;
  width: 3px;
  background: var(--sector-color);
  border-radius: 3px 0 0 3px;
}}
.commodity-card:hover {{
  transform: translateY(-2px);
  box-shadow: var(--shadow);
  border-color: var(--border-bright);
  background: var(--bg-card-hover);
}}

.signal-badge {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
  letter-spacing: 0.3px;
}}
.signal-strong-buy  {{ background: rgba(0,208,132,0.15); color: #00D084; border: 1px solid rgba(0,208,132,0.3); }}
.signal-buy         {{ background: rgba(74,158,255,0.15); color: #4A9EFF; border: 1px solid rgba(74,158,255,0.3); }}
.signal-neutral     {{ background: rgba(139,149,163,0.15); color: #8B95A3; border: 1px solid rgba(139,149,163,0.3); }}
.signal-sell        {{ background: rgba(255,159,67,0.15); color: #FF9F43; border: 1px solid rgba(255,159,67,0.3); }}
.signal-strong-sell {{ background: rgba(255,71,87,0.15); color: #FF4757; border: 1px solid rgba(255,71,87,0.3); }}

.metrics-grid      {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; margin-top: 12px; }}
.metric-item       {{ display: flex; flex-direction: column; gap: 3px; }}
.metric-label      {{ font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); }}
.metric-val        {{ font-size: 13px; color: var(--text-primary); }}
.metric-val.positive {{ color: var(--positive); }}
.metric-val.negative {{ color: var(--negative); }}
.metric-sub        {{ font-size: 10px; color: var(--text-secondary); }}

.modal-overlay {{
  display: none; position: fixed; inset: 0; z-index: 200;
  background: rgba(8, 11, 20, 0.97);
  backdrop-filter: blur(6px);
  overflow-y: auto;
  padding: 24px;
}}
.modal-overlay.open {{ display: block; }}
.modal-inner {{
  max-width: 1200px; margin: 0 auto;
  background: var(--bg-secondary);
  border: 1px solid var(--border-bright);
  border-radius: var(--radius);
  padding: 28px;
}}
.modal-close {{
  float: right; font-size: 22px; cursor: pointer;
  color: var(--text-secondary); background: none; border: none;
  line-height: 1;
}}
.modal-chart {{ width: 100%; height: 350px; margin-bottom: 24px; }}

.app-footer {{
  text-align: center; padding: 20px; font-size: 11px;
  color: var(--text-muted); border-top: 1px solid var(--border);
  margin-top: 40px;
}}
</style>
</head>
<body>

<header class="app-header">
  <div class="header-left">
    <div class="header-logo">📊 COM-QUANT</div>
    <div class="header-sub">Commodities Quantitative Analysis [10 markets live]</div>
  </div>
  <div class="header-right">
    <div class="header-ts">Last: {generated_at}</div>
    <div class="header-countdown" id="countdown"></div>
  </div>
</header>
<div id="stale-banner"></div>

<div class="filter-bar">
  <button class="filter-btn active" data-sector="all">ALL</button>
  <button class="filter-btn" data-sector="precious_metals">PRECIOUS METALS</button>
  <button class="filter-btn" data-sector="energy">ENERGY</button>
  <button class="filter-btn" data-sector="agriculture">AGRICULTURE</button>
  
  <input type="text" class="search-box" id="search-box" placeholder="🔍 search...">
  
  <span style="font-size:12px; color:var(--text-secondary); margin-left:12px;">Sort:</span>
  <select class="sort-select" id="sort-select">
    <option value="score">Composite Score</option>
    <option value="ensemble-pct">Ensemble Forecast %</option>
    <option value="rsi">RSI</option>
    <option value="sharpe">Sharpe Ratio</option>
    <option value="vol" selected>Volatility ↓</option>
  </select>
</div>

<div class="dashboard-grid">
  {"".join(cards_html)}
</div>

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
const CHARTS = {charts_js};
const PLOTLY_DARK = {{
    "paper_bgcolor": "#0D1421",
    "plot_bgcolor":  "#0D1421",
    "font":          {{"family": "Inter, sans-serif", "color": "#8B95A3", "size": 12}},
    "title_font":    {{"family": "Inter, sans-serif", "color": "#E8EDF5", "size": 14}},
    "xaxis": {{
        "gridcolor":      "rgba(255,255,255,0.05)",
        "zerolinecolor":  "rgba(255,255,255,0.08)",
        "tickfont":       {{"family": "JetBrains Mono, monospace", "color": "#8B95A3", "size": 10}},
        "linecolor":      "rgba(255,255,255,0.08)",
    }},
    "yaxis": {{
        "gridcolor":      "rgba(255,255,255,0.05)",
        "zerolinecolor":  "rgba(255,255,255,0.08)",
        "tickfont":       {{"family": "JetBrains Mono, monospace", "color": "#8B95A3", "size": 10}},
        "linecolor":      "rgba(255,255,255,0.08)",
    }},
    "legend": {{
        "bgcolor":     "rgba(255,255,255,0.05)",
        "bordercolor": "rgba(255,255,255,0.10)",
        "borderwidth": 1,
        "font":        {{"size": 11}},
    }},
    "margin": {{"l": 55, "r": 20, "t": 45, "b": 40}},
    "hovermode": "x unified",
}};

function applyDark(layout) {{
    return Object.assign({{}}, PLOTLY_DARK, layout);
}}

function openModal(key) {{
  const c = CHARTS[key];
  Plotly.newPlot('chart1', c.traces1, applyDark(c.layout1), {{responsive: true, displayModeBar: false}});
  Plotly.newPlot('chart2', c.traces2, applyDark(c.layout2), {{responsive: true, displayModeBar: false}});
  Plotly.newPlot('chart3', c.traces3, applyDark(c.layout3), {{responsive: true, displayModeBar: false}});
  Plotly.newPlot('chart4', c.traces4, applyDark(c.layout4), {{responsive: true, displayModeBar: false}});
  document.getElementById('detail-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}}
function closeModal() {{
  document.getElementById('detail-modal').classList.remove('open');
  document.body.style.overflow = '';
}}
document.addEventListener('keydown', e => e.key === 'Escape' && closeModal());

(function() {{
  const genAt  = new Date("{generated_at_utc}Z");
  const updateH = 6;
  function tick() {{
    const now   = new Date();
    const nextUp = new Date(genAt.getTime() + updateH * 3600 * 1000);
    const diff   = nextUp - now;
    if (diff <= 0) {{
      document.getElementById('countdown').textContent = 'Update overdue — refresh';
      return;
    }}
    const hh = Math.floor(diff / 3600000);
    const mm = Math.floor((diff % 3600000) / 60000);
    const ss = Math.floor((diff % 60000) / 1000);
    document.getElementById('countdown').textContent =
      `Next update in ${{hh}}h ${{mm.toString().padStart(2,'0')}}m ${{ss.toString().padStart(2,'0')}}s`;
  }}
  tick(); setInterval(tick, 1000);
}})();

(function() {{
  const genAt = new Date("{generated_at_utc}Z");
  const ageH  = (Date.now() - genAt) / 3600000;
  if (ageH > 25) {{
    const banner = document.getElementById('stale-banner');
    banner.textContent = `⚠  Data may be stale — last updated ${{Math.floor(ageH)}} hours ago`;
    banner.style.display = 'block';
  }}
}})();

document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const sector = btn.dataset.sector || 'all';
    document.querySelectorAll('.commodity-card').forEach(card => {{
      const show = sector === 'all' || card.dataset.sector === sector;
      card.style.display = show ? '' : 'none';
    }});
  }});
}});

document.getElementById('search-box').addEventListener('input', function() {{
  const q = this.value.toLowerCase();
  document.querySelectorAll('.commodity-card').forEach(card => {{
    const match = card.dataset.name.toLowerCase().includes(q)
                || card.dataset.ticker.toLowerCase().includes(q);
    card.style.display = match ? '' : 'none';
  }});
}});

document.getElementById('sort-select').addEventListener('change', function() {{
  const grid = document.querySelector('.dashboard-grid');
  const cards = [...grid.querySelectorAll('.commodity-card')];
  cards.sort((a, b) => +b.dataset[this.value] - +a.dataset[this.value]);
  cards.forEach(c => grid.appendChild(c));
}});
</script>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Built index.html")

if __name__ == "__main__":
    main()
