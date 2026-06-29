import os
import re

def apply_fixes():
    with open('src/engine.py', 'r') as f:
        content = f.read()

    # Fix 4: Add import os
    if 'import os' not in content:
        content = content.replace('import time\n', 'import time\nimport os\n')

    # Fix 2: Vectorize Monte Carlo
    mc_old = r'''def fit_monte_carlo\(prices, forecast_days, n_sims=5000\):
    n = forecast_days
    try:
        r = np.diff\(np.log\(prices\)\)
        sigma = np.std\(r\) \* np.sqrt\(252\)
        mu_ann = np.mean\(r\) \* 252 \+ \(sigma\*\*2\) / 2
        
        dt = 1/252
        S0 = prices\[-1\]
        
        paths = np.zeros\(\(n_sims, n\)\)
        Z = np.random.randn\(n_sims, n\)
        
        drift = \(mu_ann - \(sigma\*\*2\)/2\) \* dt
        vol = sigma \* np.sqrt\(dt\)
        
        for t in range\(n\):
            if t == 0:
                paths\[:, t\] = S0 \* np.exp\(drift \+ vol \* Z\[:, t\]\)
            else:
                paths\[:, t\] = paths\[:, t-1\] \* np.exp\(drift \+ vol \* Z\[:, t\]\)
        
        p5 = np.percentile\(paths, 5, axis=0\)
        p25 = np.percentile\(paths, 25, axis=0\)
        p50 = np.percentile\(paths, 50, axis=0\)
        p75 = np.percentile\(paths, 75, axis=0\)
        p95 = np.percentile\(paths, 95, axis=0\)
        
        return \{
            "p5": p5.tolist\(\), "p25": p25.tolist\(\), "p50": p50.tolist\(\), 
            "p75": p75.tolist\(\), "p95": p95.tolist\(\), "mu": float\(mu_ann\), "sigma": float\(sigma\)
        \}
    except:
        return \{"p5": \[None\]\*n, "p25": \[None\]\*n, "p50": \[None\]\*n, "p75": \[None\]\*n, "p95": \[None\]\*n, "mu": None, "sigma": None\}'''

    mc_new = '''def fit_monte_carlo(prices, forecast_days, n_sims=5000):
    n = forecast_days
    try:
        series = pd.Series(prices)
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
        
        return {
            "p5":  [round(float(v), 4) for v in pcts[0]],
            "p25": [round(float(v), 4) for v in pcts[1]],
            "p50": [round(float(v), 4) for v in pcts[2]],
            "p75": [round(float(v), 4) for v in pcts[3]],
            "p95": [round(float(v), 4) for v in pcts[4]],
            "mu":  mu,
            "sigma": sig,
        }
    except:
        return {"p5": [None]*n, "p25": [None]*n, "p50": [None]*n, "p75": [None]*n, "p95": [None]*n, "mu": None, "sigma": None}'''

    content = re.sub(mc_old, mc_new, content)

    # Fix 4: Add _meta in main()
    # Find the output dictionary assembly
    output_old = '''    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "categories":   CATEGORIES,
        "data":         data_out,
        "spreads":      spreads,
        "correlations": correlations,
    }

    with open("multi_data.json", "w") as f:
        json.dump(json_safe(output), f, indent=2)

    print(f"\\nDone in {time.time()-start:.1f}s \\u2192 multi_data.json written.")'''

    output_new = '''    failed = []
    for cid in COMMODITIES:
        if cid not in data_out or not data_out[cid]:
            failed.append(cid)

    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "categories":   CATEGORIES,
        "data":         data_out,
        "spreads":      spreads,
        "correlations": correlations,
        "_meta": {
            "generated_at":       datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "commodities_ok":     [k for k in data_out if data_out[k]],
            "commodities_failed": failed,
            "engine_version":     "2.0.0",
            "update_interval_h":  6,
        },
    }

    out_path = "multi_data.json"
    with open(out_path, "w") as fh:
        json.dump(json_safe(output), fh, separators=(",", ":"), default=str)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"\\n\\u2705  Saved \\u2192 {out_path}  ({size_kb:.1f} KB)")'''
    
    content = content.replace(output_old, output_new)

    # Fix 5: Trim historical arrays (cap disp to 365)
    disp_old = 'disp  = wp["display_days"]'
    disp_new = 'disp  = min(365, wp["display_days"])'
    content = content.replace(disp_old, disp_new)

    with open('src/engine.py', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    apply_fixes()
