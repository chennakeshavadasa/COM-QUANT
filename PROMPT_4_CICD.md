# TASK FOR GEMINI
# Read this entire file and create exactly what is described.
# Output files:
#   .github/workflows/update.yml   ← main file
#   .nojekyll                      ← empty file at repo root (needed for GitHub Pages)
# Save to: COM-QUANT/ directory

---

## CONTEXT

COM-QUANT is a static commodities quantitative dashboard served on GitHub Pages.
`engine.py` downloads commodity data and writes `multi_data.json`.
`build_dashboard.py` reads that JSON and writes `index.html`.
This GitHub Actions workflow runs both scripts daily and commits the results.

---

## FILE 1: `.github/workflows/update.yml`

```yaml
name: Daily COM-QUANT Update

on:
  schedule:
    - cron: '0 2 * * *'   # 02:00 UTC daily (07:30 IST — before Indian market open)
  workflow_dispatch:       # allow manual trigger from GitHub Actions UI

jobs:
  update:
    runs-on: ubuntu-latest
    permissions:
      contents: write      # needed to commit and push

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: |
          pip install --upgrade pip
          pip install yfinance numpy pandas scipy statsmodels scikit-learn

      - name: Create .nojekyll (required for GitHub Pages)
        run: touch .nojekyll

      - name: Run engine.py (data download + model computation)
        run: python engine.py

      - name: Run build_dashboard.py (bake JSON into HTML)
        run: python build_dashboard.py

      - name: Commit and push updated files
        run: |
          git config user.name  "COM-QUANT Bot"
          git config user.email "actions@github.com"
          git add multi_data.json index.html .nojekyll
          git diff --staged --quiet || git commit -m "Auto-update: $(date -u '+%Y-%m-%d %H:%M UTC')"
          git push
```

---

## FILE 2: `.nojekyll`

Create an empty file called `.nojekyll` at the repository root.
This tells GitHub Pages to serve files directly without running Jekyll.
Without it, files starting with `_` (like `_data`) are ignored by GitHub Pages.

```bash
touch .nojekyll
```

Or create it with: `echo "" > .nojekyll`

---

## GitHub Pages Setup (manual one-time step — add to README)

After pushing these files, the user must:
1. Go to `github.com/<username>/COM-QUANT` → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click Save
5. The dashboard will be live at `https://<username>.github.io/COM-QUANT/`

Then trigger the workflow manually once:
1. Go to Actions tab → "Daily COM-QUANT Update" → Run workflow

---

## VERIFICATION CHECKLIST

After setup the following should be true:
- [ ] `.github/workflows/update.yml` exists with the cron schedule
- [ ] `.nojekyll` exists at repo root
- [ ] `engine.py`, `build_dashboard.py`, `multi_data.json`, `index.html` all at repo root
- [ ] GitHub Actions runs successfully (green checkmark)
- [ ] `index.html` is committed by "COM-QUANT Bot" after the action runs
- [ ] `https://<username>.github.io/COM-QUANT/` loads the dashboard

---

## NOTE ON TIMING

The cron runs at 02:00 UTC = 07:30 IST.
This is deliberate — commodity markets (especially MCX in India) open at 09:00 IST,
so the dashboard is fresh before the trading day starts.
